import os
import base64
import json
from smolagents import OpenAIServerModel

def encode_image(image_path: str) -> str:
    """Encodes an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image(image_path: str) -> dict:
    """
    Analyzes an image using Vision capabilities to extract context.
    Returns a dictionary safely containing target_audience, tone, and purpose.
    """
    # Assuming config defines OPENAI_API_KEY or we use smolagents OpenAIServerModel API directly.
    # We will use the standard openai python package for simplicity giving direct structured output.
    try:
        import openai
        import config
    except ImportError:
        print("Missing required libraries 'openai' or 'config.py'")
        return {"audience":"general", "tone":"neutral", "purpose":"awareness"}

    client = openai.OpenAI(
        api_key=config.INFERX_API_KEY, 
        base_url=config.INFERX_ENDPOINT
    )

    base64_image = encode_image(image_path)

    prompt = """
    Analyze this image for marketing purposes.
    Extract the following attributes and return ONLY a valid JSON object:
    {
        "target_audience": "e.g., young professionals, tech enthusiasts",
        "tone": "e.g., professional, fun, aesthetic, startup",
        "purpose": "e.g., branding, promotion, storytelling, awareness",
        "key_objects": "short string describing main objects/scene"
    }
    """

    try:
        response = client.chat.completions.create(
            model=config.MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        content = response.choices[0].message.content
        # Strip markdown code blocks if any
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        return json.loads(content)
        
    except Exception as e:
        print(f"Vision API error: {e}. Falling back to default metadata.")
        return {
            "target_audience": "general audience",
            "tone": "professional",
            "purpose": "general awareness",
            "key_objects": "unknown"
        }
