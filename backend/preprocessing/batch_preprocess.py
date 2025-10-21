#!/usr/bin/env python3
"""
Batch preprocessor for Excel files.

This script processes all Excel files in the original folder through three stages:
1. dismantle_excel: Cleans and restructures Excel files
2. build_excel_metadata: Generates metadata and embeddings for processed files
3. build_vector_store: Creates FAISS vector index from embeddings
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.preprocessing.dismantle_excel import main_unmerge_file
from backend.preprocessing.build_excel_metadata import build_inventory
from backend.preprocessing.build_vector_store import build_faiss_index

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'excel_agent_preprocessing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('excel_agent.batch_preprocess')

def batch_process_excel_files():
    """Process all Excel files in original folder through the complete pipeline."""

    # Define paths
    original_folder = project_root / "backend" / "files" / "original"
    processed_folder = project_root / "backend" / "files" / "processed"
    vector_store_folder = project_root / "backend" / "files" / "vector_store"

    # Ensure directories exist
    processed_folder.mkdir(parents=True, exist_ok=True)
    vector_store_folder.mkdir(parents=True, exist_ok=True)

    # Get all Excel files in original folder
    excel_files = list(original_folder.glob("*.xlsx")) + list(original_folder.glob("*.xls"))

    if not excel_files:
        logger.warning(f"No Excel files found in {original_folder}")
        return False

    logger.info(f"Found {len(excel_files)} Excel files to process")

    # Stage 1: dismantle_excel - Process each file individually
    logger.info("=== STAGE 1: Dismantling Excel files ===")
    processed_files = []

    for input_file in excel_files:
        file_name = input_file.name
        output_file = processed_folder / f"{input_file.stem}_output_path.xlsx"

        logger.info(f"Processing: {file_name}")
        try:
            result = main_unmerge_file(str(input_file), str(output_file))
            if result:
                processed_files.append(output_file)
                logger.info(f"✓ Successfully processed: {file_name}")
            else:
                logger.error(f"✗ Failed to process: {file_name}")
        except Exception as e:
            logger.error(f"✗ Error processing {file_name}: {e}")

    if not processed_files:
        logger.error("No files were successfully processed in Stage 1")
        return False

    logger.info(f"Stage 1 completed. {len(processed_files)} files processed.")

    # Stage 2: build_excel_metadata - Generate metadata for all processed files
    logger.info("=== STAGE 2: Building Excel metadata ===")
    try:
        build_inventory(str(processed_folder))
        logger.info("✓ Excel metadata built successfully")
    except Exception as e:
        logger.error(f"✗ Failed to build Excel metadata: {e}")
        return False

    # Stage 3: build_vector_store - Create FAISS index
    logger.info("=== STAGE 3: Building vector store ===")
    try:
        build_faiss_index()
        logger.info("✓ Vector store built successfully")
    except Exception as e:
        logger.error(f"✗ Failed to build vector store: {e}")
        return False

    logger.info("=== BATCH PROCESSING COMPLETED SUCCESSFULLY ===")
    logger.info(f"Processed {len(processed_files)} Excel files")
    logger.info(f"Metadata saved to: {processed_folder / 'metadata_inventory.json'}")
    logger.info(f"Vector index saved to: {vector_store_folder / 'faiss_index.bin'}")

    return True

if __name__ == "__main__":
    success = batch_process_excel_files()
    sys.exit(0 if success else 1)
