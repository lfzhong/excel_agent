import json, faiss, numpy as np
from openai import OpenAI
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

METADATA_FILE = SCRIPT_DIR / "../files/processed/metadata_inventory.json"
INDEX_FILE = SCRIPT_DIR / "../files/vector_store/faiss_index.bin"
TOP_K = 2
client = OpenAI()

def search_relevant_files(question):
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    index = faiss.read_index(str(INDEX_FILE))

    # Embed the user question
    resp = client.embeddings.create(model="text-embedding-3-small", input=question)
    q_vec = np.array([resp.data[0].embedding]).astype("float32")

    distances, indices = index.search(q_vec, TOP_K)
    results = [inventory[i] for i in indices[0]]
    return results

if __name__ == "__main__":
    q = input("Enter your question: 苹果的销售额有多少？")
    results = search_relevant_files(q)
    for i, r in enumerate(results, 1):
        print(f"\nTop {i}: {r['file_name']}\nSummary: {r['summary']}")

