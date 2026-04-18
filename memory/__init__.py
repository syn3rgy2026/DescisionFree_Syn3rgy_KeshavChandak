from memory.working import WorkingMemoryTool
from memory.persistent import PersistentMemoryTool
from memory.semantic import SemanticMemoryTool
from memory.context import AgentContextManager

MEMORY_TOOLS = [
    WorkingMemoryTool(),
    PersistentMemoryTool(),
    SemanticMemoryTool(),
]
