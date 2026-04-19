import json
import logging

logger = logging.getLogger("user_interaction")

def generate_ready_payload(image_path: str, platform: str, post_type: str, caption: str, hashtags: list) -> str:
    """
    Structures the final user-approved payload into the required JSON format.
    """
    payload = {
        "image": image_path,
        "platform": platform,
        "type": post_type,
        "caption": caption,
        "hashtags": hashtags,
        "status": "ready_to_post"
    }
    
    # Return as pretty-printed JSON string
    return json.dumps(payload, indent=4)
