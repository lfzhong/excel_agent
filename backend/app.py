from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import logging
from pathlib import Path

# Import pipeline modules
from pipeline.query_index import search_relevant_files
from pipeline.code_generator import generate_code
from pipeline.execute_python import model_execute_main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Excel Agent API", description="API for querying Excel files using natural language")

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    relevant_files: list
    generated_code: str
    excel_file_used: str
    execution_result: str

@app.post("/query", response_model=QueryResponse)
async def query_excel_data(request: QueryRequest):
    """
    Query Excel data using natural language.

    This endpoint:
    1. Finds relevant Excel files based on the question
    2. Generates Python code to analyze the data
    3. Executes the code and returns results
    """
    try:
        question = request.question
        logger.info(f"Processing question: {question}")

        # Step 1: Find relevant files
        relevant_files = search_relevant_files(question)
        if not relevant_files:
            raise HTTPException(status_code=404, detail="No relevant Excel files found for the question")

        logger.info(f"Found {len(relevant_files)} relevant files")

        # Step 2: Use the most relevant file (first result)
        top_file = relevant_files[0]
        file_name = top_file['file_name']

        # Construct comprehensive metadata text including column information
        metadata_text = f"File: {top_file['file_name']}\n"
        metadata_text += f"Summary: {top_file['summary']}\n"
        metadata_text += f"File path: {top_file['file_path']}\n"
        metadata_text += f"Sheet names: {', '.join(top_file['sheet_names'])}\n"

        # Add column information for each sheet
        for sheet_name, columns in top_file['columns'].items():
            if columns:  # Only add if sheet has columns
                metadata_text += f"Sheet '{sheet_name}' columns: {', '.join(columns)}\n"

        # Add sample data if available
        for sheet_name, samples in top_file.get('sample_values', {}).items():
            if samples:
                metadata_text += f"Sample data from sheet '{sheet_name}': {str(samples[:2])}\n"

        logger.info(f"Using file: {file_name}")

        # Step 3: Generate code based on metadata and question
        generated_code = generate_code(metadata_text, question)
        logger.info("Generated code for analysis")

        # Step 3.5: Replace any file path assignments with the actual file path
        actual_file_path = top_file['file_path']

        # Simple approach: split into lines and replace any line containing file_path assignment
        lines = generated_code.split('\n')
        for i, line in enumerate(lines):
            # Look for file_path assignment, ignoring comments
            code_part = line.split('#')[0].strip()  # Remove comments
            print(f"DEBUG: Checking line {i}: '{line}' -> code_part: '{code_part}'")
            if 'file_path' in code_part and '=' in code_part:
                print(f"DEBUG: Found file_path assignment, replacing with: file_path = '{actual_file_path}'")
                # Replace the entire line with the correct assignment
                lines[i] = f"file_path = '{actual_file_path}'"
                break  # Only replace the first occurrence

        generated_code = '\n'.join(lines)

        # Step 4: Execute the generated code
        execution_result = model_execute_main(generated_code)
        logger.info("Executed code and got results")

        # Return response with all information
        return QueryResponse(
            question=question,
            relevant_files=[file['file_name'] for file in relevant_files],
            generated_code=generated_code,
            excel_file_used=file_name,
            execution_result=execution_result
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
