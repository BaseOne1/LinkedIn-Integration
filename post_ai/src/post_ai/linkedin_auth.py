import requests
import os

def post_to_linkedin(content, images):
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    # Basic text post example
    body = {
        "author": f"urn:li:person:{os.getenv('LINKEDIN_USER_ID')}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE"  # You can switch to IMAGE later
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    response = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=body)

    print(f"📡 LinkedIn API response: {response.status_code} - {response.text}")
