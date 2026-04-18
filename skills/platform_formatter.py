def format_for_platform(caption: str, platform: str, post_type: str = "post") -> dict:
    """
    Applies final touch-ups, emoji constraints, and hashtag structures
    based on the platform and post type.
    """
    platform = platform.lower()
    post_type = post_type.lower()
    
    formatted_caption = caption
    hashtags = []

    if platform == "instagram":
        # Ensure it has spacing
        formatted_caption = formatted_caption.replace("\\n", "\n\n")
        # Default trending tags simulation
        hashtags = ["#instagood", "#marketing", "#photooftheday", "#brand"]
        if post_type == "story":
            formatted_caption = f"🚨 NEW POST 🚨\n{caption}\nTap here! 👆"
            hashtags = ["#story"]
            
    elif platform == "linkedin":
        # Professional formatting, stripping excessive emojis if possible
        hashtags = ["#MarketingStrategy", "#BusinessGrowth", "#ProfessionalDevelopment"]
        if post_type == "article":
            formatted_caption = f"📊 Professional Insight:\n\n{caption}"

    return {
        "caption": formatted_caption,
        "hashtags": hashtags
    }
