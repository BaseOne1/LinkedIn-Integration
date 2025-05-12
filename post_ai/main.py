import logging
from src.post_ai.services.text_handler import generate_post_content
from src.post_ai.db.s3_handler import upload_post_to_s3
from src.post_ai.services.image_generator import generate_image
from src.post_ai.config.config import params
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    
    logging.info("Generating post content...")
    post_text = generate_post_content()

    logging.info("Generating image...")
    image_prompt = params["image_gen"]["prompt"]
    image_url = generate_image()

    if image_url:
        logging.info("Uploading post and sending approval email...")
        upload_post_to_s3(post_text, image_url)
    else:
        logging.error("Failed to generate image. Aborting.")
