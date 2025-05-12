import json
import base64
import requests
import logging
from datetime import datetime
from src.post_ai.db.s3_client import s3
from src.post_ai.services.email_handler import send_email_to_receiver

# Setup logger
logger = logging.getLogger("s3_uploader")
logger.setLevel(logging.INFO)

bucket_name = "falaipostings"

def upload_post_to_s3(post_text: str, image_url: str) -> str:
    try:
        timestamp = datetime.utcnow().isoformat().replace(":", "-")
        key = f"pending/post_{timestamp}.json"

        response = requests.get(image_url)
        response.raise_for_status()

        image_base64 = base64.b64encode(response.content).decode('utf-8')
        image_data_uri = f"data:image/jpeg;base64,{image_base64}"

        post_data = {
            "text": post_text,
            "image_url": image_url,
            "image_base64": image_data_uri,
            "status": "pending"
        }

        s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(post_data))
        logger.info(f"Post uploaded to S3: {key}")

        send_email_to_receiver(post_text, key)
        return key

    except Exception as e:
        logger.exception(f"Failed to upload post or send email: {e}")
        raise
