# Story Generator Backend

This is the backend for the Story AI Generator project. It provides APIs for generating stories using AI.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Jonathan-Shiju/Story-ai-generator-backend.git
cd Story-ai-generator
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Backend Server

You can start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

Replace `main:app` with the actual Python file and FastAPI app instance if different.

### 5. API Usage

- The backend exposes endpoints for story generation.
- Refer to the API documentation (usually available at `/docs` when running FastAPI).

## Project Structure

- `requirements.txt`: Python dependencies.
- `main.py`: FastAPI application entry point (may vary).
- Other files: Supporting modules and assets.

## Notes

- Ensure Python 3.8+ is installed.
- For development, use the virtual environment to avoid dependency conflicts.

