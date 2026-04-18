from tools.file_tool import ALL_TOOLS as FILE_TOOLS
from tools.shell_tool import SHELL_TOOLS
from tools.file_watcher import detect_new_images
from tools.instagram_tool import post_to_instagram, login_to_instagram
from tools.linkedin_tool import post_to_linkedin, login_to_linkedin
from tools.human_confirm import ask_human_confirmation

ALL_TOOLS = FILE_TOOLS + SHELL_TOOLS + [
    detect_new_images, 
    post_to_instagram, 
    login_to_instagram, 
    post_to_linkedin, 
    login_to_linkedin,
    ask_human_confirmation
]
