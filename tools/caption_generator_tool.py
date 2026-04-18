import json
from smolagents import tool
from skills.image_understanding import analyze_image
from skills.caption_generator import generate_captions

@tool
def analyze_and_generate_captions(image_path: str, platform: str) -> str:
    """
    Analyzes an image and generates 3 tailored caption options for social media.
    Args:
        image_path: Absolute path to the image file to be analyzed.
        platform: The social media platform string (e.g., 'instagram', 'linkedin').
    Returns:
        A JSON string containing exactly 3 caption options in an array.
    """
    try:
        # Step 1: Analyze image to get metadata
        metadata = analyze_image(image_path)
        
        # Step 2: Pass metadata and platform to generate captions
        captions = generate_captions(metadata, platform)
        
        return json.dumps(captions, indent=2)
    except Exception as e:
        return json.dumps([f"Fallback caption 1 for {platform}: Here's a great photo! #marketing", 
                           f"Fallback caption 2 for {platform}: Check out this amazing shot!", 
                           f"Fallback caption 3 for {platform}: Loving this moment!"])
