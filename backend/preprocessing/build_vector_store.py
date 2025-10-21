import json, faiss, numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(f'excel_agent_preprocessing.{__name__}')

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

METADATA_FILE = SCRIPT_DIR / "../files/processed/metadata_inventory.json"
INDEX_FILE = SCRIPT_DIR / "../files/vector_store/faiss_index.bin"

def build_faiss_index():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    # Filter entries with embeddings
    vectors = [m["embedding_vector"] for m in inventory if m.get("embedding_vector")]
    if not vectors:
        raise ValueError("No embeddings found in metadata_inventory.json")

    vectors = np.array(vectors).astype("float32")
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    faiss.write_index(index, str(INDEX_FILE))
    print(f"FAISS index saved to {INDEX_FILE}")
    print(f"Indexed {len(vectors)} files.")

if __name__ == "__main__":
    build_faiss_index()
