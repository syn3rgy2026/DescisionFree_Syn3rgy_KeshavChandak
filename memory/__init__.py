from memory.working import WorkingMemoryTool
from memory.persistent import PersistentMemoryTool
from memory.context import AgentContextManager

MEMORY_TOOLS = [
    WorkingMemoryTool(),
    PersistentMemoryTool(),
]
