"""
semantic.py
-----------
Semantic (vector) memory backed by ChromaDB + sentence-transformers.
Stores text passages with embeddings so the agent can later retrieve
memories by meaning rather than exact keyword match.
Persists to ~/.agent/chroma/
"""

import os
from smolagents import Tool


CHROMA_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma")
COLLECTION_NAME = "agent_semantic_memory"
EMBED_MODEL = "all-MiniLM-L6-v2"


def _get_collection():
    """Lazily initialize ChromaDB client and collection."""
    import chromadb
    from chromadb.utils import embedding_functions

    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )
    return collection


class SemanticMemoryTool(Tool):
    name = "semantic_memory"
    description = """Use this tool when you need to store or find information BY MEANING rather
than by exact key. It uses vector embeddings so you can search with natural
language and find related memories even if the wording is different.

Good for: storing research summaries, user context paragraphs, notes from
web pages, or any free-form text you might need to recall later.

Supported actions:
  store  — save a text passage with an id and optional metadata
           (requires id + value, optional category)
  search — find the most similar stored passages to a query
           (requires value as the search query, returns top 5)
"""
    inputs = {
        "action": {
            "type": "string",
            "description": "One of: store, search",
        },
        "id": {
            "type": "string",
            "description": "Unique identifier for the memory (required for store)",
            "nullable": True,
        },
        "value": {
            "type": "string",
            "description": "The text to store, or the natural-language search query",
        },
        "category": {
            "type": "string",
            "description": "Optional tag/category for filtering (e.g. 'research', 'user_fact')",
            "nullable": True,
        },
    }
    output_type = "string"

    def forward(
        self,
        action: str,
        value: str,
        id: str = None,
        category: str = None,
    ) -> str:
        try:
            action = action.strip().lower()

            if action == "store":
                if not id:
                    return "ERROR: 'store' requires an id"
                if not value:
                    return "ERROR: 'store' requires a value (the text to embed)"
                try:
                    collection = _get_collection()
                except Exception as e:
                    return f"ERROR: failed to connect to ChromaDB — {str(e)}"
                metadata = {}
                if category:
                    metadata["category"] = category.strip().lower()
                try:
                    collection.upsert(
                        ids=[id],
                        documents=[value],
                        metadatas=[metadata] if metadata else None,
                    )
                except Exception as e:
                    return f"ERROR: failed to store embedding — {str(e)}"
                return f"OK — stored semantic memory '{id}'"

            elif action == "search":
                if not value:
                    return "ERROR: 'search' requires a value (the query text)"
                try:
                    collection = _get_collection()
                except Exception as e:
                    return f"ERROR: failed to connect to ChromaDB — {str(e)}"
                try:
                    results = collection.query(
                        query_texts=[value],
                        n_results=5,
                    )
                except Exception as e:
                    return f"ERROR: search failed — {str(e)}"
                ids = results.get("ids", [[]])[0]
                docs = results.get("documents", [[]])[0]
                dists = results.get("distances", [[]])[0]
                if not ids:
                    return "No semantic memories found."
                lines = []
                for i, (mid, doc, dist) in enumerate(zip(ids, docs, dists), 1):
                    score = round(1 - dist, 3) if dist <= 1 else round(dist, 3)
                    preview = doc[:200] + "..." if len(doc) > 200 else doc
                    lines.append(f"  {i}. [{mid}] (score={score}) {preview}")
                return f"Top {len(lines)} results:\n" + "\n".join(lines)

            else:
                return f"ERROR: unknown action '{action}'. Use store/search"

        except Exception as e:
            return f"ERROR: {str(e)}"
