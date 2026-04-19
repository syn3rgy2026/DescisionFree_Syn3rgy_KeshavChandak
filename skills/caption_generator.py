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
    You are an elite digital marketing strategist and social media growth expert.
    You need to write 3 highly converting, unique marketing captions for a {platform} post.
    
    Image Context: {image_metadata.get('key_objects')}
    Target Audience: {image_metadata.get('target_audience')}
    Tone: {image_metadata.get('tone')}
    Purpose: {image_metadata.get('purpose')}
    
    Marketing Requirements:
    - Include an irresistible, scroll-stopping Hook in the first line (e.g. bold claim, question, or relatable statement).
    - Frame the core message using copywriting frameworks (like AIDA: Attention, Interest, Desire, Action or PAS: Problem, Agitate, Solution).
    - Include a clear, compelling Call-to-Action (CTA) such as "Save this for later," "Tag a friend who needs this," or "Click the link in bio."
    - Append 10-15 highly relevant and trending hashtags strategically placed at the end to maximize organic reach and discoverability.
    - Use line breaks and emojis to maintain a visually pleasing, easy-to-read structure.
    - Provide exactly 3 different options separated ONLY by exactly '---OPTION---'.
    - DO NOT use markdown lists or numbers for the options, just write the raw caption text separated by the delimiter.
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
