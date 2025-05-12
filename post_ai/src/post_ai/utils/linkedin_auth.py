import os
from dotenv import load_dotenv
from src.comment.config.config import settings
from src.comment.utils.logger import get_logger
import requests



def refresh_access_token():
    refresh_token = os.getenv("REFRESH_TOKEN")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        new_access_token = response.json().get("access_token")
        print(" Access token refreshed.")
        return new_access_token
    else:
        print(f"Failed to refresh token: {response.text}")
        return None