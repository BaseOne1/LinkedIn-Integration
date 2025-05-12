import os
import yaml
from dotenv import load_dotenv

load_dotenv()

def get_linkedin_headers(params_yaml=None):
    if not params_yaml:
        params_yaml = Settings.load_params()
    headers = params_yaml.get("headers", {})
    for k, v in headers.items():
        if isinstance(v, str) and "${ACCESS_TOKEN}" in v:
            headers[k] = v.replace("${ACCESS_TOKEN}", os.getenv("ACCESS_TOKEN", ""))
    return headers

def get_params_yaml():
    return Settings.load_params()

class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.access_token = os.getenv("ACCESS_TOKEN")
        self.org_id = os.getenv("ORG_ID_TARGET")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.refresh_token = os.getenv("REFRESH_TOKEN")
        self.fal_key = os.getenv("FAL_KEY")
        self.fine_tune_id = os.getenv("FINE_TUNE_ID")
        self.bucket_name = "falaipostings"
        self.params = self.load_params()
        self.image_gen = self.process_image_gen_params(self.params.get("image_gen", {}))
        self.email = EmailSettings(self.params.get("email", {}))   # 🛠 Pass email params here

    @staticmethod
    def load_yaml(path: str):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    @classmethod
    def load_prompts(cls):
        return cls.load_yaml("prompts.yaml")

    @classmethod
    def load_params(cls):
        return cls.load_yaml("params.yaml")

    def process_image_gen_params(self, image_gen_params):
        if image_gen_params.get("finetune_id") == "FINE_TUNE_ID":
            image_gen_params["finetune_id"] = os.getenv("FINE_TUNE_ID")
        return image_gen_params

class EmailSettings:
    def __init__(self, email_params: dict):
        self.from_name = email_params.get("from_name", os.getenv("EMAIL_SENDER", "default_sender@example.com"))
        self.to = email_params.get("to", os.getenv("EMAIL_RECEIVER", "default_receiver@example.com"))
        self.subject = email_params.get("subject", "LinkedIn Post Awaiting Approval")
        self.smtp_user = os.getenv("SES_SMTP_USER")
        self.smtp_pass = os.getenv("SES_SMTP_PASS")
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = os.getenv("SMTP_PORT")
        self.approve_url = email_params.get("approve_url", "")
        self.reject_url = email_params.get("reject_url", "")

# Instantiate settings object globally
settings = Settings()
prompts = settings.load_prompts()
params = settings.load_params()
