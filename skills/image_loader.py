import os
from pathlib import Path
from typing import List

try:
    from PIL import Image
except ImportError:
    Image = None

def get_images_from_folder(folder_path: str) -> List[str]:
    """
    Scans a folder for image files and returns their absolute paths.
    Validates them using PIL if installed.
    """
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = []
    
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        print(f"Error: {folder_path} is an invalid directory.")
        return []

    for file in path.iterdir():
        if file.suffix.lower() in valid_extensions:
            # Validate image integrity
            if Image:
                try:
                    with Image.open(file) as img:
                        img.verify()
                except Exception as e:
                    print(f"Warning: Skipping corrupted image {file.name}: {e}")
                    continue
            images.append(str(file.absolute()))
            
    return images
