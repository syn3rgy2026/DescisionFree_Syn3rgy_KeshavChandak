import os
import mss
from PIL import Image
from smolagents import tool

from typing import Any

@tool
def take_and_analyze_screenshot(question: str) -> Any:
    """Takes a screenshot of the primary monitor and saves it for analysis.
    
    Args:
        question: The user's question about the screen contents.
        
    Returns:
        The raw PIL image of the screenshot for you to analyze visually!
    """
    output_path = "output/temp_screen.png"
    os.makedirs("output", exist_ok=True)
    
    with mss.mss() as sct:
        # Grab primary monitor (index 1)
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.save(output_path)
        
    return img

take_and_analyze_screenshot.output_type = "image"
