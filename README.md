# Excel Agent

A powerful AI-powered Excel analysis tool that allows you to query Excel files using natural language. The system automatically finds relevant Excel files, generates Python analysis code, and executes it to provide insights from your data.

## Features

- **Natural Language Queries**: Ask questions about your Excel data in plain English
- **Automatic File Discovery**: Uses semantic search to find the most relevant Excel files for your questions
- **AI-Powered Code Generation**: Leverages GPT-4 to generate custom Python analysis code
- **Safe Code Execution**: Runs generated code in isolated Jupyter kernels
- **Multi-Sheet Support**: Handles Excel files with multiple worksheets
- **Flexible Data Analysis**: Supports various types of data analysis tasks (summarization, filtering, calculations, etc.)
- **Modern Web Interface**: Clean, responsive UI for easy interaction with your data
- **Real-time Progress**: See analysis progress with Server-Sent Events (SSE)
- **Code Visualization**: View generated Python code with syntax highlighting
- **Interactive Data Tables**: View analysis results in formatted tables with export functionality
- **Progressive UI Rendering**: Dynamic content containers that adapt based on content type

## Architecture

The system consists of three main components:

### 1. Preprocessing Pipeline
- **File Cleaning**: Processes and cleans Excel files to handle merged cells and complex formatting
- **Metadata Generation**: Extracts structure information, column names, data types, and sample data
- **Vector Indexing**: Creates embeddings for semantic search using FAISS and OpenAI embeddings

### 2. Query Processing Pipeline
- **Semantic Search**: Finds relevant Excel files using vector similarity search
- **Code Generation**: Uses GPT-4 to generate Python analysis code based on file metadata and user questions
- **Code Execution**: Safely executes generated code in isolated Jupyter environments

### 3. FastAPI Backend
- RESTful API with endpoints for querying and health checks
- Asynchronous processing for efficient handling of requests
- Server-Sent Events (SSE) for real-time streaming responses

### 4. Streaming Response System

The system implements a sophisticated three-phase streaming response architecture:

#### Phase 1: Code Generation (`content_type: 'code'`)
- **Start**: Initializes code display container
- **In Progress**: Streams generated Python code with syntax highlighting
- **End**: Adds copy-to-clipboard functionality

#### Phase 2: Data Processing (`content_type: 'data'`)
- **Start**: Prepares data table container
- **In Progress**: Streams data results (supports JSON arrays/objects)
- **End**: Enables CSV export functionality

#### Phase 3: Result Analysis (`content_type: 'result'`)
- **Start**: Creates result display area
- **In Progress**: Streams analysis conclusions and insights
- **End**: Completes the analysis session

Each phase uses `content_status` field (`start`, `in_progress`, `end`) to manage UI lifecycle, enabling smooth progressive rendering and interactive features.

## Installation

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd /path/to/excel_agent
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

## Usage

### 1. Prepare Your Excel Files

Place your Excel files (`.xlsx` or `.xls`) in the `backend/files/original/` directory.

### 2. Preprocess the Files

Run the preprocessing pipeline to clean, analyze, and index your Excel files:

```bash
cd backend/preprocessing
python batch_preprocess.py
```

This will:
- Clean and restructure your Excel files
- Generate metadata and embeddings
- Create a FAISS vector index for fast semantic search

### 3. Start the API Server

```bash
cd backend
python app.py
```

The API will be available at `http://localhost:8000`

### 4. Query Your Data

#### Option A: Web Interface (Recommended)

Start both the backend API and frontend interface:

```bash
./start.sh --frontend
```

This will start:
- Backend API at `http://localhost:8000`
- Frontend UI at `http://localhost:3000`

Open your browser and navigate to `http://localhost:3000` to use the web interface.

#### Option B: API Direct Access

Send POST requests to the `/query` endpoint:

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the total sales amount for apples?"}'
```

**Example Response:**
```json
{
  "question": "What is the total sales amount for apples?",
  "relevant_files": ["sales_data_output_path.xlsx", "inventory_output_path.xlsx"],
  "generated_code": "import pandas as pd\n... # Generated analysis code",
  "excel_file_used": "sales_data_output_path.xlsx",
  "execution_result": "Total sales for apples: $15,240.50"
}
```

## API Endpoints

### POST `/query`
Query Excel data using natural language.

**Request Body:**
```json
{
  "question": "string"
}
```

**Response:**
```json
{
  "question": "string",
  "relevant_files": ["string"],
  "generated_code": "string",
  "excel_file_used": "string",
  "execution_result": "string"
}
```

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Configuration

The system uses several configuration options defined in the preprocessing scripts:

- **Embedding Model**: `text-embedding-3-small` (OpenAI)
- **Code Generation Model**: `gpt-4o-mini` (OpenAI)
- **Vector Search**: Top-K results (default: 2)
- **Sample Rows**: Number of sample rows extracted for metadata (default: 2)

## Project Structure

```
excel_agent/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── preprocessing/
│   │   ├── batch_preprocess.py    # Main preprocessing pipeline
│   │   ├── dismantle_excel.py     # Excel file cleaning
│   │   ├── build_excel_metadata.py # Metadata extraction
│   │   └── build_vector_store.py   # FAISS index creation
│   ├── pipeline/
│   │   ├── query_index.py      # Semantic search
│   │   ├── code_generator.py   # AI code generation
│   │   └── execute_python.py   # Safe code execution
│   └── files/
│       ├── original/           # Input Excel files
│       ├── processed/          # Cleaned Excel files + metadata
│       └── vector_store/       # FAISS index
├── requirements.txt           # Python dependencies
├── stop_all.sh               # Shutdown script
└── README.md
```

## Dependencies

- **FastAPI**: Web framework for the API
- **OpenAI**: AI models for embeddings and code generation
- **pandas**: Data manipulation and analysis
- **FAISS**: Vector similarity search
- **sentence-transformers**: Text embeddings
- **jupyter-client/ipykernel**: Safe code execution environment
- **openpyxl**: Excel file processing

## Example Use Cases

1. **Sales Analysis**: "What were the total sales by product category last quarter?"
2. **Financial Reporting**: "Calculate the average expense growth rate over the past 3 years"
3. **Student Records**: "How many students scored above 90% in mathematics?"
4. **Inventory Management**: "Which products have stock levels below the reorder point?"

## Troubleshooting

### Common Issues

1. **No relevant files found**: Ensure your Excel files have been preprocessed and the vector index is built
2. **Code execution errors**: Check that the generated code is valid Python and that required libraries are installed
3. **OpenAI API errors**: Verify your API key is set and has sufficient credits

### Stopping the Server

Use the provided stop script:

```bash
./stop_all.sh
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please create an issue in the GitHub repository.
