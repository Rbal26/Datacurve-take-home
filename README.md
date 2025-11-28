# PR Telemetry Trace API

## What This Is

This is a backend API that collects and analyzes developer debugging sessions. When a developer fixes a bug, their IDE can send a "trace" containing their actions (file edits, terminal commands, reasoning steps). This system validates the trace, stores it as JSON, runs the code's tests in Docker, and uses GPT-4o-mini to evaluate the quality of the developer's reasoning. It returns a combined QA score.

## Project Files

```
Datacurve-take-home/
├── app/
│   ├── models/          # Data validation schemas (Pydantic)
│   ├── storage/         # Save/load traces as JSON files
│   ├── api/             # FastAPI HTTP endpoints
│   └── qa/
│       ├── test_runner.py   # Runs tests in Docker containers
│       └── llm_judge.py     # Evaluates reasoning with GPT-4o-mini
├── tests/               # 44 unit and integration tests
├── data/                # Stored trace JSON files (created on first run)
├── sample_repo/         # Example Python project used for testing
├── main.py              # API entry point
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container definition
├── docker-compose.yml   # Multi-service setup
└── .env                 # Your API keys (not committed to Git)
```

## Prerequisites

- **Python 3.11+** installed
- **Docker Desktop** installed and running
- **OpenAI API key** (get one at https://platform.openai.com/api-keys)

## How to Run (Step by Step)

### Step 1: Get the Code

```bash
git clone <your-repository-url>
cd Datacurve-take-home
```

### Step 2: Create Python Virtual Environment

```bash
python -m venv .venv
```

### Step 3: Activate Virtual Environment

**If you're on Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**If you're on Mac or Linux:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` appear in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Set Up Your API Key

**Windows:**
```powershell
Copy-Item .env.example .env
notepad .env
```

**Mac/Linux:**
```bash
cp .env.example .env
nano .env
```

In the file that opens, replace `your_openai_api_key_here` with your actual OpenAI API key:
```
OPENAI_API_KEY=sk-proj-abc123yourkeyhere
```

Save and close the file.

### Step 6: Start the API Server

```bash
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The API is now running! Keep this terminal open.

### Step 7: Test It Works

Open a **new terminal** and run:

**Windows (PowerShell):**
```powershell
Invoke-WebRequest http://localhost:8000/health
```

**Mac/Linux:**
```bash
curl http://localhost:8000/health
```

You should see: `{"status":"healthy"}`

### Step 8: Run the Test Suite

In the new terminal (with venv activated):
```bash
pytest tests/ -v
```

Expected result: `44 passed in X seconds`

## API Endpoints

Once running, the API provides these endpoints:

- `GET /health` - Check if API is running
- `POST /traces` - Submit a new debugging trace
- `GET /traces/{trace_id}` - Retrieve a stored trace
- `POST /traces/{trace_id}/events` - Add more events to an existing trace
- `POST /traces/{trace_id}/finalize` - Run tests in Docker + evaluate reasoning with AI

## Example Usage

**Create a trace:**

**Windows:**
```powershell
$body = @{
    developer_id = "dev-001"
    repo = @{
        name = "my-app"
        url = "https://github.com/user/repo"
        branch = "main"
        commit_before = "abc123"
        commit_after = "def456"
        test_command = "pytest"
    }
    start_time = "2025-11-27T10:00:00Z"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/traces `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**Mac/Linux:**
```bash
curl -X POST http://localhost:8000/traces \
  -H "Content-Type: application/json" \
  -d '{
    "developer_id": "dev-001",
    "repo": {
      "name": "my-app",
      "url": "https://github.com/user/repo",
      "branch": "main",
      "commit_before": "abc123",
      "commit_after": "def456",
      "test_command": "pytest"
    },
    "start_time": "2025-11-27T10:00:00Z"
  }'
```

The response will include a `trace_id` you can use to retrieve or finalize the trace.

See `API_EXAMPLES.md` for more detailed examples.

## Alternative: Run with Docker

If you prefer Docker, you can skip the Python setup and just run:

```bash
docker-compose up
```

This starts the API on port 8000 automatically.

## Running Tests

The project includes 44 tests organized by feature:

- `test_models.py` - Data validation (11 tests)
- `test_storage.py` - File operations (6 tests)
- `test_api.py` - HTTP endpoints (8 tests)
- `test_incremental.py` - Event appending (7 tests)
- `test_qa_runner.py` - Docker test execution (5 tests)
- `test_llm_judge.py` - AI reasoning evaluation (4 tests)
- `test_finalize.py` - End-to-end pipeline (3 tests)

Run all tests:
```bash
pytest tests/ -v
```

## How It Works

1. A developer's IDE sends a trace (JSON) containing their debugging session
2. FastAPI validates the trace structure using Pydantic schemas
3. The trace is stored as a JSON file in the `data/` directory
4. When finalized, the system:
   - Clones the repo and runs its tests in an isolated Docker container
   - Extracts reasoning steps and sends them to GPT-4o-mini for quality evaluation
   - Combines both results into a `qa_results` object
5. The enriched trace is returned with test outcomes and reasoning scores
