import smtplib
import json
import logging
from base64 import b64decode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from src.post_ai.config.config import settings
from src.post_ai.db.s3_client import s3

# Setup logger
logger = logging.getLogger("email_sender")
logger.setLevel(logging.INFO)

def send_email_to_receiver(post_text: str, key: str):
    try:
        # Fetch email settings
        emailsettings = settings.email
        from_name = emailsettings.from_name
        to = emailsettings.to
        smtp_server = emailsettings.smtp_server
        smtp_port = int(emailsettings.smtp_port)
        smtp_user = emailsettings.smtp_user
        smtp_pass = emailsettings.smtp_pass
        bucket_name = settings.bucket_name

        print(to)

        # Fetch post data from S3
        response = s3.get_object(Bucket=bucket_name, Key=key)
        post_data = json.loads(response["Body"].read())

        # Decode image if available
        base64_image_data = post_data.get("image_base64", "")
        image_bytes = b64decode(base64_image_data.split(",")[1]) if "," in base64_image_data else b""

        # Create email
        msg = MIMEMultipart("related")
        msg["Subject"] = emailsettings.subject
        msg["From"] = from_name
        msg["To"] = to

        approve_link = f"https://ther7oaeqc.execute-api.ap-south-1.amazonaws.com/default/postai?file={key}&action=approve"
        reject_link = f"https://ther7oaeqc.execute-api.ap-south-1.amazonaws.com/default/postai?file={key}&action=reject"

        html = f"""
        <html>
            <body>
                <h2>LinkedIn Post Approval Request</h2>
                <p>{post_text}</p>
                <img src="cid:postimage" style="max-width: 500px; border: 1px solid #ccc;" />
                <br><br>
                <a href='{approve_link}' style='padding:10px 20px; background-color:green; color:white; text-decoration:none;'>Approve</a>
                &nbsp;&nbsp;
                <a href='{reject_link}' style='padding:10px 20px; background-color:red; color:white; text-decoration:none;'>Reject</a>
            </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        if image_bytes:
            img = MIMEImage(image_bytes)
            img.add_header("Content-ID", "<postimage>")
            img.add_header("Content-Disposition", "inline", filename="post.jpg")
            msg.attach(img)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_name, to, msg.as_string())

        logger.info(f"Approval email sent successfully for file: {key}")

    except Exception as e:
        logger.exception(f"Failed to send approval email for file: {key}: {e}")
