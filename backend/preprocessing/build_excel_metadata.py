import os, json, hashlib, pandas as pd, logging
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(f'excel_agent_preprocessing.{__name__}')


# ---------- CONFIG ----------
FOLDER = os.path.join(project_root, "backend", "files", "processed")  # Folder containing Excel files processed by dismantle_excel.py
ORIGINAL_FOLDER = os.path.join(project_root, "backend", "files", "original")  # Fallback folder with original Excel files
OUTPUT_JSON = os.path.join(project_root, "backend", "files", "processed", "metadata_inventory.json")
N_SAMPLE_ROWS = 2
OPENAI_MODEL_SUMMARY = "gpt-4o-mini"
OPENAI_MODEL_EMBED = "text-embedding-3-small"
# -----------------------------

client = OpenAI()

def summarize_excel_structure(file_path):
    """Create metadata summary for one Excel file."""
    logger.info(f"Processing file: {file_path}")
    try:
        excel = pd.ExcelFile(file_path, engine='openpyxl')
    except Exception as e:
        logger.error(f"Failed to open Excel file {file_path}: {e}")
        raise

    metadata = {
        "file_name": Path(file_path).name,
        "file_path": str(Path(file_path).resolve()),
        "file_size": os.path.getsize(file_path),
        "sheet_names": excel.sheet_names,
        "columns": {},
        "dtypes": {},
        "sample_values": {}
    }

    # --- extract structure info ---
    for sheet in excel.sheet_names:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=N_SAMPLE_ROWS)
            metadata["columns"][sheet] = df.columns.tolist()
            metadata["dtypes"][sheet] = df.dtypes.astype(str).to_dict()
            # Convert sample values to strings to ensure JSON serializability
            sample_df = df.head(N_SAMPLE_ROWS)
            metadata["sample_values"][sheet] = sample_df.astype(str).to_dict(orient="records")
        except Exception as e:
            metadata["columns"][sheet] = []
            metadata["dtypes"][sheet] = {}
            metadata["sample_values"][sheet] = []
            metadata["error"] = str(e)
            logger.error(f"Error processing sheet '{sheet}' in file {file_path}: {e}")

    # --- create summary text for embedding ---
    summary_prompt = f"""
    You are describing an Excel file. Summarize its likely contents and purpose in one short English sentence.

    File name: {metadata['file_name']}
    Sheets: {metadata['sheet_names']}
    Columns: {metadata['columns']}
    """
    try:
        summary_resp = client.chat.completions.create(
            model=OPENAI_MODEL_SUMMARY,
            messages=[{"role": "user", "content": summary_prompt}],
            max_completion_tokens=60
        )
        summary_text = summary_resp.choices[0].message.content.strip()
    except Exception as e:
        summary_text = f"Summary generation failed: {e}"
        logger.error(f"Error generating summary for file {metadata['file_name']}: {e}")

    metadata["summary"] = summary_text

    # --- embedding for retrieval ---
    try:
        emb_resp = client.embeddings.create(
            model=OPENAI_MODEL_EMBED,
            input=summary_text
        )
        metadata["embedding_vector"] = emb_resp.data[0].embedding
    except Exception as e:
        metadata["embedding_vector"] = []
        metadata["embedding_error"] = str(e)
        logger.error(f"Error generating embedding for file {metadata['file_name']}: {e}")

    return metadata


def build_inventory(folder):
    """Generate metadata for all Excel files in folder."""
    inventory = []
    for file in os.listdir(folder):
        if file.lower().endswith((".xlsx", ".xls")):
            file_path = os.path.join(folder, file)
            logger.info(f"Processing: {file_path}")
            meta = summarize_excel_structure(file_path)
            inventory.append(meta)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)
    logger.info(f"Metadata inventory saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    build_inventory(FOLDER)
