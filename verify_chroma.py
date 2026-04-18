
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="llm_knowledge")

# Query for something likely to be in the text
results = collection.query(
    query_texts=["What are Large Language Models?"],
    n_results=1
)

print("Verification Result:")
print(results['documents'])
