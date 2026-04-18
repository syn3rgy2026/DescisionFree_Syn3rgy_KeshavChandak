import json
import logging

try:
    from tools.human_confirm import ask_human_confirmation
except ImportError:
    ask_human_confirmation = None

logger = logging.getLogger("approval_manager")

def get_posting_approval(payload: dict) -> bool:
    """
    Takes a generated payload dictionary and requests mandatory
    human confirmation before posting using the human_confirm module.

    Args:
        payload: The payload dict containing image, platform, caption, etc.

    Returns:
        Boolean indicating whether the user approved the posting.
    """
    if ask_human_confirmation is None:
        logger.warning("Human confirmation tool missing. Proceeding with caution.")
        return False
        
    action = f"Post social media content to {payload.get('platform')}"
    reason = "Mandatory human confirmation is required before any content is published out of the local environment."
    risk_level = "MEDIUM"
    
    details = json.dumps({
        "Image": payload.get("image", "unknown"),
        "Platform": payload.get("platform", "unknown"),
        "Type": payload.get("type", "post"),
        "Caption": payload.get("caption", "...")
    })
    
    response = ask_human_confirmation(
        action=action,
        reason=reason,
        risk_level=risk_level,
        details=details
    )
    
    if response and response.strip().lower() == "yes":
        return True
    return False
