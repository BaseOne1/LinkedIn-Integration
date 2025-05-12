import json
import os
import boto3
import requests
from datetime import datetime, timezone, timedelta
import hashlib

UNIPILE_API_KEY = os.getenv("UNIPILE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ARIA_ID = os.getenv("ARIA_ID")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("AriaBotState")

def was_greeted(sender_id):
    try:
        response = table.get_item(Key={
            "PK ": f"GREETED#{sender_id}",
            "SK": f"GREETED#{sender_id}"
        })

        item = response.get("Item")
        if not item:
            return False

        ttl = item.get("ttl")
        if not ttl:
            return False

        current_time = int(datetime.now(timezone.utc).timestamp())
        return current_time < ttl
    except Exception as e:
        print(f"DynamoDB get_item error (was_greeted): {e}")
        return False

def mark_greeted(sender_id, ttl_minutes=5):
    ttl = int((datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).timestamp())
    try:
        table.put_item(Item={
            "PK ": f"GREETED#{sender_id}",
            "SK": f"GREETED#{sender_id}",
            "ttl": ttl
        })
    except Exception as e:
        print(f"DynamoDB put_item error (mark_greeted): {e}")



def store_message_for_user(sender_id, role, content, ttl_minutes=30):
    ttl = int((datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).timestamp())
    timestamp = datetime.now(timezone.utc).isoformat()
    message_id = hashlib.sha256(f"{sender_id}:{timestamp}:{role}".encode()).hexdigest()
    
    try:
        table.put_item(Item={
            "PK ": f"MEMORY#{sender_id}",
            "SK": f"MSG#{timestamp}",
            "role": role,
            "content": content,
            "ttl": ttl
        })
    except Exception as e:
        print(f"[DynamoDB Error - store_message] {e}")

def get_recent_messages(sender_id, limit=10):
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("PK ").eq(f"MEMORY#{sender_id}"),
            ScanIndexForward=True,
            Limit=limit
        )
        return [
            {"role": item["role"], "content": item["content"]}
            for item in response.get("Items", [])
        ]
    except Exception as e:
        print(f"[DynamoDB Error - get_recent_messages] {e}")
        return []


def generate_openai_reply(user_message, sender_name, greeted_before, sender_id):
    """Generate response using OpenAI with short-term memory."""
    if sender_id == ARIA_ID:
        return None
    greeting = f"Hello {sender_name}, how can I assist you today?" if not greeted_before else ""
    system_prompt = (
        "You are ARIA,You will:\n"
        "- You respond precise and as professional chatbot"
        "- Your CEO is Matthew spuffard"
        "- If asked about sales accept to check and schedule sales calls.\n"
        "- If asked about CEO accept to check and schedule call with CEO.\n"
        "- Ask for their agreement before getting their contact information as per baseone data policy then ask contact information.\n"
        "- Acknowlegde the contact information has been recorded and baseone's teams will get to you shortly"
        "- Acknowlegde the contact information has been recorded and our CEO will get to you shortly"
        "- Acknowlegde informations received and ask for further assistant"
        "- if answer is negative for further assistants wish a good day and send a closing chat prompt"
        "- if asked provide\n"
        "- Website: https://baseone.uk/\n"
        "- About: https://baseone.uk/our-purpose/\n"
        "- Services: https://baseone.uk/services/\n"
        "- Case Studies: https://baseone.uk/casestudies/\n"
        "- Insights: https://baseone.uk/latest-insights/\n"
        "- Contact: https://baseone.uk/get-in-touch/\n"
        "- ARIA Page: https://www.linkedin.com/company/106444572/admin/dashboard/\n"
        "- BaseOne LinkedIn: https://www.linkedin.com/company/baseone/\n"
        "- CEO: https://www.linkedin.com/in/matthewspuffard/"
    )

    history = get_recent_messages(sender_id, limit=5) 
    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": user_message})
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 200
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json=payload
        )
        data = response.json()

    
        if response.status_code != 200 or "choices" not in data:
            print(f"[OpenAI API Error] {data}")
            return "Thanks for your message! One of our executives will reach out shortly."
        
        reply = data["choices"][0]["message"]["content"].strip()
        store_message_for_user(sender_id, "user", user_message)
        store_message_for_user(sender_id, "assistant", reply)

        return f"{greeting}\n{reply}" if greeting else reply

    except Exception as e:
        print(f"[OpenAI Error] {e}")
        return "Thanks for your message! One of our executives will reach out shortly."


def send_unipile_message(chat_id, account_id, message, api_key):
    url = f"https://api13.unipile.com:14364/api/v1/chats/{chat_id}/messages"
    files = {
        "text": (None, message),
        "account_id": (None, account_id)
    }
    headers = {
        "X-API-KEY": api_key,
        "accept": "application/json"
    }
    try:
        response = requests.post(url, files=files, headers=headers)
        print(f"Unipile response: {response.status_code} - {response.text}")
        return response.status_code, response.text
    except Exception as e:
        print("Error sending message to Unipile:", str(e))
        return 500, str(e)

def lambda_handler(event, context):
    print("Event received:", json.dumps(event, indent=2))

    try:
        body = json.loads(event.get("body", "{}"))
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid JSON: {str(e)}"})
        }

    required_fields = ["event", "message_type", "message", "sender", "account_info", "chat_id", "account_id", "timestamp"]
    if not all(field in body for field in required_fields):
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Ignored non-message event"})
        }

    event_type = body["event"]
    message_type = body["message_type"]
    message = body.get("message", "").strip()
    sender = body["sender"]
    sender_name = sender.get("attendee_name", "")
    sender_id = sender.get("attendee_id", "")
    account_name = body["account_info"].get("name", "")
    chat_id = body["chat_id"]
    account_id = body["account_id"]
    timestamp = body["timestamp"]


    if event_type != "message_received" or message_type != "MESSAGE" or not message:
        print("Rejected: Not a valid message event")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Non-message event"})
        }

    
    if ARIA_ID and sender_id == ARIA_ID:
        print(f"Rejected: Message from ARIA ignored (sender_id matched ARIA_ID)")
        return {
            "statusCode": 200,
            "body": json.dumps("Ignored self message")
        }

    
    if sender_name == account_name:
        print(f"Rejected: Self message from account '{account_name}' ignored")
        return {
            "statusCode": 200,
            "body": json.dumps("Self message ignored")
        }
    message_hash = hashlib.sha256(f"{sender_id}:{message}:{timestamp}".encode()).hexdigest()

    exists = table.get_item(Key={
        "PK ": f"DEDUPLICATION#{sender_id}",
        "SK": f"HASH#{message_hash}"
    })

    if "Item" in exists:
        print("Duplicate message detected. Skipping.")
        return {
            "statusCode": 200,
            "body": json.dumps("Duplicate message ignored")
        }

    table.put_item(Item={
        "PK ": f"DEDUPLICATION#{sender_id}",
        "SK": f"HASH#{message_hash}",
        "ttl": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())
    })

    print(f"Processing message from {sender_name} ({sender_id}): {message}")

    greeted_before = was_greeted(sender_id)
    if not greeted_before:
        mark_greeted(sender_id)

    reply = generate_openai_reply(message, sender_name, greeted_before, sender_id)
    if not reply:
        print("No reply generated (possibly from ARIA message)")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No reply generated"})
        }

    print("Reply generated:", reply)
    status, response_text = send_unipile_message(chat_id, account_id, reply, UNIPILE_API_KEY)

    return {
        "statusCode": 200 if status == 200 else 500,
        "body": json.dumps({
            "message": "Reply sent" if status == 200 else "Failed to send reply",
            "unipile_response": response_text
        })
    }


