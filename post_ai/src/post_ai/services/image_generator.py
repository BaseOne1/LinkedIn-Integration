import time
import fal_client
import logging
from src.post_ai.config.config import settings, prompts  # <-- IMPORT prompts

# Setup logger
logger = logging.getLogger("image_generator")
logger.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

def generate_image() -> str:
    try:
        logger.info("Starting image generation...")

        # Fetch prompt from YAML
        prompt = prompts["generate_image"]["prompt"]
        logger.info(f"Prompt fetched for image generation: {prompt}")

        # Start generation request
        response = fal_client.subscribe(
            "fal-ai/flux-pro/v1.1-ultra-finetuned",
            arguments={**settings.image_gen, "prompt": prompt},
            with_logs=True,
        )

        max_retries = 30
        sleep_between_retries = 2
        attempt = 0

        while attempt < max_retries:
            if response and "images" in response and response["images"]:
                logger.info("Image generation successful.")
                return response["images"][0]["url"]

            logger.info(f"Waiting for image... (attempt {attempt + 1}/{max_retries})")
            time.sleep(sleep_between_retries)
            response = fal_client.get(response["request_id"], with_logs=True)
            attempt += 1

        logger.error("Image generation timed out after max retries.")
        return None

    except Exception as e:
        logger.exception(f"Error during image generation: {e}")
        return None
