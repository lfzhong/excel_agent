from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import logging
import uuid
import asyncio
from pathlib import Path

# Import pipeline modules
from pipeline.query_index import search_relevant_files
from pipeline.code_generator import generate_code
from pipeline.execute_python import model_execute_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('excel_agent_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Excel Agent API", description="API for querying Excel files using natural language")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def suc(data):
    """
    Standardize success response format.

    Args:
        data: The payload data to wrap

    Returns:
        dict: Standardized success response with code, msg, and data
    """
    return {"code": 0, "msg": "success", "data": data}

def to_ret_s_suc(answer, finished, content_type, content_status, chat_id, response_id):
    """
    Wrap response payload into proper SSE message format.

    Args:
        answer: The content/answer to send
        finished: Boolean indicating if the response is complete (1) or in progress (0)
        content_type: Type of content being sent
        content_status: Status of the content (e.g., "start", "in_progress", "end")
        chat_id: Unique chat session identifier
        response_id: Unique response identifier

    Returns:
        str: Formatted SSE message with data: JSON\n\n
    """
    payload = {
        "answer": answer,
        "finished": finished,
        "content_type": content_type,
        "content_status": content_status,
        "chat_id": chat_id,
        "response_id": response_id
    }
    return f"data: {json.dumps(suc(payload))}\n\n"

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    relevant_files: list
    generated_code: str
    excel_file_used: str
    execution_result: str

@app.get("/query")
async def query_excel_data(question: str):
    """
    Query Excel data using natural language with SSE streaming.

    This endpoint streams the analysis process:
    1. Finding relevant Excel files
    2. Generating Python code to analyze the data
    3. Executing the code and streaming results
    """
    chat_id = str(uuid.uuid4())
    response_id = str(uuid.uuid4())

    async def query_stream():
        try:
            logger.info(f"Processing question: {question}")

            # Step 1: Finding relevant files
            yield to_ret_s_suc(
                answer="🔍 Searching for relevant Excel files...",
                finished=0,
                content_type="text",
                content_status="start",
                chat_id=chat_id,
                response_id=response_id
            )

            relevant_files = search_relevant_files(question)
            if not relevant_files:
                yield to_ret_s_suc(
                    answer="❌ No relevant Excel files found for your question.",
                    finished=1,
                    content_type="error",
                    content_status="end",
                    chat_id=chat_id,
                    response_id=response_id
                )
                return

            logger.info(f"Found {len(relevant_files)} relevant files")

            # Step 2: Use the most relevant file (first result)
            top_file = relevant_files[0]
            file_name = top_file['file_name']

            yield to_ret_s_suc(
                answer=f"📊 Found {len(relevant_files)} relevant files. Using: {file_name}",
                finished=0,
                content_type="text",
                content_status="in_progress",
                chat_id=chat_id,
                response_id=response_id
            )

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
            yield to_ret_s_suc(
                answer="🤖 Generating Python analysis code...",
                finished=0,
                content_type="text",
                content_status="in_progress",
                chat_id=chat_id,
                response_id=response_id
            )

            generated_code = generate_code(metadata_text, question)
            logger.info("Generated code for analysis")

            # Step 3.5: Replace any file path assignments with the actual file path
            actual_file_path = top_file['file_path']

            # Simple approach: split into lines and replace any line containing file_path assignment
            lines = generated_code.split('\n')
            for i, line in enumerate(lines):
                # Look for file_path assignment, ignoring comments
                code_part = line.split('#')[0].strip()  # Remove comments
                if 'file_path' in code_part and '=' in code_part:
                    # Replace the entire line with the correct assignment
                    lines[i] = f"file_path = '{actual_file_path}'"
                    break  # Only replace the first occurrence

            generated_code = '\n'.join(lines)

            # Send generated code - Start phase
            yield to_ret_s_suc(
                answer="",
                finished=0,
                content_type="code",
                content_status="start",
                chat_id=chat_id,
                response_id=response_id
            )

            # Send generated code - In progress phase
            yield to_ret_s_suc(
                answer=f"```python\n{generated_code}\n```",
                finished=0,
                content_type="code",
                content_status="in_progress",
                chat_id=chat_id,
                response_id=response_id
            )

            # Send generated code - End phase
            yield to_ret_s_suc(
                answer="",
                finished=0,
                content_type="code",
                content_status="end",
                chat_id=chat_id,
                response_id=response_id
            )

            # Step 4: Execute the generated code
            yield to_ret_s_suc(
                answer="⚡ Executing data analysis...",
                finished=0,
                content_type="text",
                content_status="in_progress",
                chat_id=chat_id,
                response_id=response_id
            )

            execution_result = model_execute_main(generated_code)
            logger.info("Executed code and got results")

            # Send data results - Start phase
            yield to_ret_s_suc(
                answer="",
                finished=0,
                content_type="data",
                content_status="start",
                chat_id=chat_id,
                response_id=response_id
            )

            # Send data results - In progress phase
            # For now, we'll send the execution result as data
            # In a more advanced implementation, this could stream DataFrame chunks
            yield to_ret_s_suc(
                answer=execution_result,
                finished=0,
                content_type="data",
                content_status="in_progress",
                chat_id=chat_id,
                response_id=response_id
            )

            # Send data results - End phase
            yield to_ret_s_suc(
                answer="",
                finished=0,
                content_type="data",
                content_status="end",
                chat_id=chat_id,
                response_id=response_id
            )

            # Send final analysis results - Start phase
            yield to_ret_s_suc(
                answer="",
                finished=0,
                content_type="result",
                content_status="start",
                chat_id=chat_id,
                response_id=response_id
            )

            # Send final analysis results - In progress phase
            yield to_ret_s_suc(
                answer=f"**Analysis Complete:**\n{execution_result}",
                finished=0,
                content_type="result",
                content_status="in_progress",
                chat_id=chat_id,
                response_id=response_id
            )

            # Send final analysis results - End phase
            yield to_ret_s_suc(
                answer="",
                finished=1,
                content_type="result",
                content_status="end",
                chat_id=chat_id,
                response_id=response_id
            )

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            yield to_ret_s_suc(
                answer=f"❌ Error during analysis: {str(e)}",
                finished=1,
                content_type="error",
                content_status="end",
                chat_id=chat_id,
                response_id=response_id
            )

    return StreamingResponse(
        query_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
