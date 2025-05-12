import openai
import logging
from src.post_ai.config.config import settings, prompts, params

# Setup logging
logger = logging.getLogger("text_handler")
logger.setLevel(logging.INFO)

# Set OpenAI API key
openai.api_key = settings.openai_api_key

def generate_post_content() -> str:
    try:
        logger.info("Generating post content...")
        
        model_name = params["openai"]["model"]
        max_tokens = params["openai"]["max_tokens"]
        temperature = params["openai"]["temperature"]
        top_p = params["openai"]["top_p"]
        frequency_penalty = params["openai"]["frequency_penalty"]
        presence_penalty = params["openai"]["presence_penalty"]

        system_prompt = prompts["generate_post"]["system"]
        user_prompt = prompts["generate_post"]["user"]

        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )

        post_content = response['choices'][0]['message']['content']
        logger.info("Post content generation successful.")
        return post_content

    except Exception as e:
        logger.exception(f"Failed to generate post content: {e}")
        raise
