from typing import List
from smolagents import tool
import os

@tool
def detect_new_images(folder_path: str) -> List[str]:
    """
    Scans a specified directory and returns a list of absolute paths to valid images.
    Use this to detect what images are available to be processed.

    Args:
        folder_path: The absolute or relative path to the directory to scan.

    Returns:
        List of strings, where each string is an absolute path to an image file.
    """
    try:
        from skills.image_loader import get_images_from_folder
        return get_images_from_folder(folder_path)
    except Exception as e:
        # Fallback if skill missing
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        images = []
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if any(file.lower().endswith(ext) for ext in valid_exts):
                    images.append(os.path.abspath(os.path.join(folder_path, file)))
        return images
