
import chromadb
import json
import os

# Correct path based on directory listing
json_path = 'llm_data.json'

if not os.path.exists(json_path):
    print(f"Error: {json_path} not found")
    exit(1)

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)['documents']

# Initialize Chroma Client with persistent storage
client = chromadb.PersistentClient(path="./chroma_db")

# Create or get a collection
collection = client.get_or_create_collection(name="llm_knowledge")

# Create IDs and metadata
ids = [f"id_{i}" for i in range(len(data))]
metadatas = [{"source": f"web_page_{i}"} for i in range(len(data))]

# Add the documents
collection.add(
    documents=data,
    metadatas=metadatas,
    ids=ids
)

print(f"Successfully stored {len(data)} documents in Chroma DB.")
