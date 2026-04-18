from tools.scraper_tool import scrape_website, scrape_website_structured
from tools.web_screenshot import capture_website_screenshot
from tools.file_tool import ALL_TOOLS as FILE_TOOLS
from tools.shell_tool import SHELL_TOOLS

ALL_TOOLS = FILE_TOOLS + SHELL_TOOLS + [
    scrape_website,
    scrape_website_structured,
    capture_website_screenshot
]