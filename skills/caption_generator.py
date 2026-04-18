import json
import logging

try:
    import openai
    import config
except ImportError:
    pass

logger = logging.getLogger("caption_generator")

def generate_captions(image_metadata: dict, platform: str) -> list:
    """
    Generates 3 tailored caption options using an LLM.
    Args:
        image_metadata: output from image_understanding
        platform: string (e.g., 'instagram', 'linkedin')
    Returns:
        List of 3 string captions.
    """
    try:
        client = openai.OpenAI(
            api_key=config.INFERX_API_KEY, 
            base_url=config.INFERX_ENDPOINT
        )
    except Exception:
        # Fallback 
        return [f"Mock dynamic caption for {platform} about {image_metadata.get('key_objects', 'this photo')}! #marketing"] * 3

    sys_prompt = f"""
    You are an expert social media marketer.
    You need to write 3 unique marketing captions for a {platform} post.
    
    Image Context: {image_metadata.get('key_objects')}
    Target Audience: {image_metadata.get('target_audience')}
    Tone: {image_metadata.get('tone')}
    Purpose: {image_metadata.get('purpose')}
    
    Requirements:
    - Include a strong Hook in the first line.
    - Include a Value proposition/message.
    - Include a Call-to-Action (CTA).
    - Provide exactly 3 different options separated by '---OPTION---'.
    - DO NOT use markdown lists, just write the raw caption text.
    """

    try:
        response = client.chat.completions.create(
            model=config.MODEL_ID,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "Generate the 3 caption options now."}
            ],
            max_tokens=600,
            temperature=0.7
        )
        content = response.choices[0].message.content
        
        options = [opt.strip() for opt in content.split("---OPTION---") if opt.strip()]
        
        # Ensure we return at least a fallback if the parsing failed
        if not options:
            return [content.strip()]
            
        return options[:3]

    except Exception as e:
        logger.error(f"Failed to generate captions: {e}")
        return [f"Great photo of {image_metadata.get('key_objects', 'this moment')}! Check it out!"] * 3
