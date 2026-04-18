from tools.file_tool import ALL_TOOLS as FILE_TOOLS
from tools.shell_tool import SHELL_TOOLS
from tools.email_tool import send_email, reset_email_credentials
from tools.email_reader_tool import read_emails

EMAIL_TOOLS = [send_email, reset_email_credentials, read_emails]

ALL_TOOLS = FILE_TOOLS + SHELL_TOOLS + EMAIL_TOOLS
