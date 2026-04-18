from tools.file_tool import ALL_TOOLS as FILE_TOOLS
from tools.shell_tool import SHELL_TOOLS
from tools.email_tool import send_email, reset_email_credentials
from tools.email_reader_tool import read_emails

EMAIL_TOOLS = [send_email, reset_email_credentials, read_emails]

try:
    from memory.working import WorkingMemoryTool
    from memory.persistent import PersistentMemoryTool
    from memory.semantic import SemanticMemoryTool
    MEMORY_TOOLS = [WorkingMemoryTool(), PersistentMemoryTool(), SemanticMemoryTool()]
except Exception as _mem_err:
    import sys
    print(f"⚠️  Memory tools failed to load: {_mem_err}", file=sys.stderr)
    MEMORY_TOOLS = []

ALL_TOOLS = FILE_TOOLS + SHELL_TOOLS + EMAIL_TOOLS + MEMORY_TOOLS
