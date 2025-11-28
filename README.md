# PR Telemetry Trace API

## Project Overview

This is a backend system for collecting and evaluating developer debugging traces. When a developer fixes a bug, their IDE can send a structured trace containing their actions (file edits, terminal commands, test results) and reasoning steps. The system validates traces, stores them, runs tests in isolated Docker containers, and uses GPT-4o-mini to evaluate the quality of the developer's reasoning process.

The goal is to collect high-fidelity data for training AI systems to understand not just what code changed, but how developers arrived at their solutions.

## Table of Contents

1. [Project Plan](#project-plan)
2. [Quick Start](#quick-start)
3. [API Documentation](#api-documentation)
4. [Testing](#testing)
5. [Security](#security)
6. [Architecture](#architecture)

---

## Project Plan

### 0. Motivation

Most existing bug-fix datasets only capture the final code change (a diff or PR). This loses the developer's process: which files they explored, what commands and tests they ran, what hypotheses they formed, and how their reasoning evolved over time.

This project builds a system that:
- Captures a "PR Telemetry Trace" containing actions and reasoning
- Runs automatic QA by executing tests in Docker
- Uses an LLM to evaluate reasoning quality
- Persists enriched traces for downstream ML training

This simulates a core loop of data collection for AI coding capabilities: collecting high-fidelity traces, validating them, and annotating them with rich labels.

### 1. Goals and Non-Goals

**Goals:**
- Define a clear PR Telemetry Trace schema with session metadata, chronological events, and QA results
- Build a Python backend using FastAPI that accepts traces, stores them, and serves them via REST API
- Support incremental ingestion so large traces can be uploaded in batches
- Attach automatic QA: run tests in Docker and evaluate reasoning with an LLM
- Make it easy to run with `docker-compose up`
- Include comprehensive testing (unit and integration tests)

**Non-Goals (to keep scope realistic for 3-4 hours):**
- Building an IDE plugin or UI (backend only)
- Supporting all programming languages (demo with Python/pytest)
- Production-grade security, auth, or multi-tenancy (though we implement basic security measures)
- Building a full streaming system with retries and deduplication
- Dashboards or analytics

### 2. Clarifying Questions & Assumptions

**Q1: What level of granularity should the telemetry capture?**

Assumption: High-level developer actions (file open/close, code edits, commands, tests, reasoning steps), not keystroke-level data. The IDE aggregates low-level interactions into these high-level events.

**Q2: How is the developer's reasoning captured?**

Assumption: Developers write explicit reasoning_step events. We don't try to infer reasoning from actions. The IDE emits these as structured events.

**Q3: What makes a "good" trace?**

Assumption: A good trace has tests passing AND clear reasoning. The qa_results section provides both hard labels (tests_passed, exit code) and soft labels (reasoning score 1-5, feedback).

**Q4: What is the contract for QA execution?**

Assumption: Each trace includes repo metadata with a test_command field. For this demo, we assume the repo code is available locally and mounted into Docker. We demonstrate with a sample Python project using pytest.

**Q5: Do we need incremental ingestion?**

Assumption: Yes. Large debugging sessions might produce traces too big to upload at once. We support POST /traces/{id}/events to append events incrementally.

**Privacy:** We assume the IDE redacts PII and secrets before sending. The backend uses anonymous developer IDs and doesn't log full trace contents.

### 3. Proposed Data Schema

The PR Telemetry Trace is a JSON document representing one bug-fixing session.

**Top-Level Structure:**

```json
{
  "schema_version": "1.0",
  "trace_id": "abcd-1234-efgh-5678",
  "developer_id": "anon-dev-42",
  "bug_id": "BUG-123",
  "repo": {
    "name": "example-project",
    "url": "https://github.com/org/example-project",
    "branch": "bugfix/login-error",
    "commit_before": "a1b2c3d",
    "commit_after": "d4e5f6a",
    "test_command": "pytest"
  },
  "start_time": "2025-11-27T15:00:00Z",
  "end_time": "2025-11-27T15:30:00Z",
  "events": [],
  "qa_results": {}
}
```

**Event Types Supported:**
- file_open / file_close: Track which files developer examines
- code_edit: Contains file path and unified diff
- terminal_command: Command, exit code, output, and duration
- test_result: Summary of test run
- reasoning_step: Developer's explicit thought process

**QA Results Schema:**

```json
"qa_results": {
  "tests_passed": true,
  "test_exit_code": 0,
  "test_output_snippet": "All tests passed.",
  "reasoning_score": 4.5,
  "reasoning_feedback": "Clear and methodical reasoning..."
}
```

### 4. High-Level Technical Plan

**Architecture Components:**

1. **API Service (FastAPI)**: Receives traces, triggers QA, serves results
2. **Persistence Layer**: JSON files (one per trace) in the data/ directory
3. **QA Engine (Docker)**: Runs test_command in isolated container
4. **LLM Judge**: Evaluates reasoning using GPT-4o-mini
5. **Orchestration**: docker-compose for one-command startup

**Why Python + FastAPI?**
- Python dominates ML/data workflows
- Rich ecosystem for LLM APIs (OpenAI SDK)
- Docker SDK makes container orchestration straightforward
- FastAPI provides built-in Pydantic validation, type hints, and auto-generated docs
- Async support for good performance

**API Endpoints:**
- POST /traces: Ingest a full trace
- POST /traces/{id}/events: Incrementally append events
- POST /traces/{id}/finalize: Run QA pipeline (tests + LLM judge)
- GET /traces/{id}: Retrieve stored trace

### 5. LLM Judge Design

**Model Selection: GPT-4o-mini**

We chose GPT-4o-mini because:
- Strong at evaluating logical reasoning and meta-cognitive tasks
- JSON mode ensures reliable structured output
- Cost-effective at approximately $0.15 per 1M input tokens
- OpenAI API is mature and well-documented

**Reasoning Quality Rubric (5 dimensions, 0-1 point each):**

1. **Hypothesis Formation**: Did they form clear, testable hypotheses?
2. **Evidence Gathering**: Did they systematically explore files/logs/commands?
3. **Logical Coherence**: Is the reasoning chain clear and logical?
4. **Validation**: Did they test their fix and verify it works?
5. **Depth**: Did they consider edge cases or alternative explanations?

Total score: 1.0-5.0 (sum of dimensions)

**LLM Prompt Template:**

The system concatenates all reasoning_step events chronologically and sends them to GPT-4o-mini with this prompt:

```
You are evaluating a software developer's reasoning process while fixing a bug.

Below is their chronological reasoning log:

---
[1] First reasoning step content
[2] Second reasoning step content
...
---

Evaluate their reasoning on these five dimensions (0-1 point each):

1. **Hypothesis Formation**: Did they form clear, testable hypotheses about the root cause?
2. **Evidence Gathering**: Did they systematically explore files/logs/commands to validate hypotheses?
3. **Logical Coherence**: Is the reasoning chain clear and logical?
4. **Validation**: Did they test their fix and verify it works?
5. **Depth**: Did they consider edge cases or alternative explanations?

Respond with JSON in this exact format:
{
  "score": <sum of dimensions, 1.0-5.0>,
  "feedback": "<2-3 sentence explanation of the score>"
}
```

**API Call Configuration:**
- Model: `gpt-4o-mini`
- Temperature: 0.3 (for consistency)
- Response format: JSON mode (ensures valid output)
- Timeout: 30 seconds

This rubric is objective (clear criteria per dimension), actionable (developers can learn what makes good reasoning), and ML-friendly (numerical score enables filtering high-quality traces).

### 6. Security Considerations

While this is a prototype, we implemented several security measures:

**Implemented:**
- **Input Validation**: Pydantic schemas validate all incoming JSON
- **Path Sanitization**: File paths are checked for path traversal attempts (../, absolute paths)
- **Command Sanitization**: Test commands are validated to prevent shell injection (; | & $() etc.)
- **API Authentication**: Simple Bearer token auth protects all endpoints
- **Input Size Limits**: 10MB max request body to prevent DOS attacks
- **Docker Resource Limits**: Containers limited to 2GB RAM and 2 CPU cores
- **Structured Logging**: Logs avoid storing sensitive data, only trace IDs and status

**Threat Model:**
- Untrusted JSON traces from clients
- Untrusted code running inside Docker
- API keys for LLM provider
- Potentially sensitive developer data

**Future Production Needs (documented but not implemented):**
- OAuth/JWT instead of simple API tokens
- Rate limiting per API key
- Network isolation for Docker containers
- Advanced secret redaction from logs
- Database with proper ACID guarantees

### 7. Scope & Trade-offs

**MVP (Implemented):**
- PR Telemetry Trace schema
- FastAPI service with all planned endpoints
- JSON file persistence
- Docker-based test runner for Python/pytest
- LLM judge with GPT-4o-mini
- API authentication and input validation
- Comprehensive test suite (53 tests)
- docker-compose setup
- This README with complete documentation

**Nice-to-Have (Descoped):**
- Database persistence (PostgreSQL/MongoDB)
- Async QA with job queue (Celery/RQ)
- Multi-language test support beyond Python
- Rich querying API with filters
- Web UI dashboard
- LLM judge ensemble

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker Desktop installed and running
- OpenAI API key (get one at https://platform.openai.com/api-keys)

### Installation Steps

**Step 1: Get the code**

```bash
git clone https://github.com/Rbal26/Datacurve-take-home.git
cd Datacurve-take-home
```

**Step 2: Create and activate virtual environment**

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Mac/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

**Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 4: Configure environment variables**

Windows:
```powershell
Copy-Item .env.example .env
notepad .env
```

Mac/Linux:
```bash
cp .env.example .env
nano .env
```

Update the .env file with your keys:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
API_TOKEN=datacurve-takehome-token
```

Note: The API_TOKEN should be set to `datacurve-takehome-token` for this demo. All example API calls in this README and API_EXAMPLES.md use this token. You'll need to include it in the Authorization header: `Authorization: Bearer datacurve-takehome-token`

**Step 5: Start the API**

```bash
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Step 6: Verify it works**

Open a new terminal and test the health endpoint:

Windows (PowerShell):
```powershell
Invoke-WebRequest http://localhost:8000/health
```

Mac/Linux:
```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"healthy"}`

**Step 7: Run tests**

```bash
pytest tests/ -v
```

Expected: `53 passed`

### End-to-End Testing Example

Once the API is running and tests pass, you can test the complete pipeline:

**1. Create a trace with reasoning steps:**

Windows (PowerShell):
```powershell
$headers = @{"Authorization"="Bearer datacurve-takehome-token"; "Content-Type"="application/json"}
$body = @{
    developer_id = "test-dev"
    repo = @{
        name = "sample-repo"
        url = "https://github.com/test/repo"
        branch = "main"
        commit_before = "abc"
        commit_after = "def"
        test_command = "pytest"
    }
    start_time = "2025-11-28T10:00:00Z"
    events = @(
        @{
            event_type = "reasoning_step"
            timestamp = "2025-11-28T10:01:00Z"
            data = @{ content = "I suspect the bug is in the login validation" }
        },
        @{
            event_type = "reasoning_step"
            timestamp = "2025-11-28T10:02:00Z"
            data = @{ content = "Added null check for user.profile before accessing email" }
        },
        @{
            event_type = "reasoning_step"
            timestamp = "2025-11-28T10:03:00Z"
            data = @{ content = "Ran tests and confirmed the fix works" }
        }
    )
} | ConvertTo-Json -Depth 10

$response = Invoke-WebRequest -Uri http://localhost:8000/traces -Method POST -Headers $headers -Body $body
$traceId = ($response.Content | ConvertFrom-Json).trace_id
Write-Host "Created trace: $traceId"
```

**2. Run QA pipeline (tests + LLM judge):**

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/traces/$traceId/finalize" -Method POST -Headers @{"Authorization"="Bearer datacurve-takehome-token"}
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

You should see the complete trace with `qa_results` showing:
- `tests_passed: true` (Docker tests ran successfully)
- `reasoning_score: 3.0-5.0` (LLM evaluation of reasoning quality)
- `reasoning_feedback` (explanation from GPT-4o-mini)

See `API_EXAMPLES.md` for more examples with curl commands for Mac/Linux.

---

## API Documentation

All API endpoints (except `/health` and `/`) require authentication. Include the Authorization header with your API token:

```
Authorization: Bearer datacurve-takehome-token
```

For this demo, the token is `datacurve-takehome-token` (set in your `.env` file). This is documented in all examples.

### Endpoints

**POST /traces**
Submit a new debugging trace.

Request body example:
```json
{
  "developer_id": "dev-001",
  "repo": {
    "name": "my-app",
    "url": "https://github.com/user/repo",
    "branch": "main",
    "commit_before": "abc123",
    "commit_after": "def456",
    "test_command": "pytest"
  },
  "start_time": "2025-11-27T10:00:00Z",
  "events": []
}
```

Response:
```json
{
  "trace_id": "generated-uuid",
  "status": "stored"
}
```

**GET /traces/{trace_id}**
Retrieve a stored trace.

Response: Full trace JSON

**POST /traces/{trace_id}/events**
Append events to an existing trace (incremental ingestion).

Request body:
```json
{
  "events": [
    {
      "event_type": "reasoning_step",
      "timestamp": "2025-11-27T10:01:00Z",
      "data": {"content": "I think the bug is in login.py"}
    }
  ]
}
```

**POST /traces/{trace_id}/finalize**
Run QA pipeline (Docker tests + LLM judge).

Response: Full trace with qa_results populated

See API_EXAMPLES.md for complete examples with PowerShell and curl.

---

## Testing

The project includes 53 tests across 7 test files:

- `test_models.py` (11 tests): Pydantic model validation
- `test_storage.py` (6 tests): File persistence operations
- `test_api.py` (8 tests): HTTP endpoint behavior
- `test_incremental.py` (7 tests): Incremental event appending
- `test_qa_runner.py` (5 tests): Docker test execution
- `test_llm_judge.py` (4 tests): LLM reasoning evaluation
- `test_finalize.py` (3 tests): End-to-end QA pipeline
- `test_security.py` (9 tests): Security validation

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_security.py -v
```

Test environment uses isolated tokens and mocks external dependencies (Docker, OpenAI API) where appropriate.

---

## Security

### Authentication

All API endpoints (except /health and /) require Bearer token authentication. Set your token in the .env file and include it in the Authorization header:

```
Authorization: Bearer your-secure-token-here
```

### Input Validation

**File Path Sanitization:**
- Rejects paths containing ".." (parent directory traversal)
- Rejects absolute paths (/, C:\)
- Only allows relative paths within project

**Command Sanitization:**
- Blocks dangerous shell operators: ; | & && || $() `
- Prevents command injection attacks

**Size Limits:**
- Maximum request body: 10MB
- Prevents DOS attacks via large JSON payloads

### Docker Isolation

Tests run in isolated Docker containers with:
- Read-only filesystem access to repository
- Resource limits: 2GB RAM, 2 CPU cores
- 5-minute timeout per test execution
- Containers automatically removed after execution

### Logging

Structured logging includes:
- Timestamp, endpoint, trace_id, severity
- Security events (rejected paths, invalid tokens)
- QA pipeline status
- Errors with context

Logs explicitly avoid:
- Full trace contents
- Full test output
- API keys or tokens

### Known Limitations

This is a prototype. Production deployments would need:
- OAuth2/JWT instead of static tokens
- Rate limiting per API key
- HTTPS/TLS for all traffic
- Database with proper authentication
- Network isolation for Docker containers
- Regular security audits

---

## Architecture

### Project Structure

```
Datacurve-take-home/
├── app/
│   ├── models/               # Pydantic schemas
│   │   ├── trace.py          # Trace and RepoInfo
│   │   ├── events.py         # Event types
│   │   └── qa_results.py     # QA results schema
│   ├── storage/              # Persistence layer
│   │   └── file_store.py     # JSON file operations
│   ├── api/                  # REST endpoints
│   │   └── routes.py         # FastAPI routes
│   ├── qa/                   # Quality assurance
│   │   ├── test_runner.py    # Docker test execution
│   │   └── llm_judge.py      # GPT-4o-mini evaluation
│   └── utils/                # Utilities
│       ├── logger.py         # Structured logging
│       ├── auth.py           # API authentication
│       └── security.py       # Input sanitization
├── tests/                    # 53 unit & integration tests
├── sample_repo/              # Example Python project
├── data/                     # Stored traces (created at runtime)
├── main.py                   # FastAPI application
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container definition
├── docker-compose.yml        # Orchestration
├── .env                      # Environment variables (not in git)
└── README.md                 # This file
```

### Data Flow

1. **Ingestion**: Client POSTs trace to /traces
2. **Validation**: Pydantic validates schema, security checks file paths and commands
3. **Storage**: Trace written to data/{trace_id}.json
4. **QA Trigger**: Client POSTs to /traces/{id}/finalize
5. **Test Execution**: Docker container runs test_command and captures results
6. **Reasoning Evaluation**: LLM receives reasoning steps, returns score and feedback
7. **Enrichment**: qa_results added to trace and persisted
8. **Response**: Client receives complete trace with QA results

### Technology Stack

- **Python 3.11**: Language
- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **Docker SDK**: Container orchestration
- **OpenAI API**: LLM judge (GPT-4o-mini)
- **pytest**: Testing framework
- **Uvicorn**: ASGI server
- **Docker Compose**: Multi-container orchestration

### Scalability Considerations

Current implementation uses JSON files and synchronous QA for simplicity. For production scale I would add:

**Database Layer:**
- PostgreSQL for metadata and qa_results (fast filtering/querying)
- S3/blob storage for large event arrays

**Asynchronous QA:**
- Celery with Redis for job queue
- Background workers for Docker tests and LLM judge
- Immediate response with qa_status: "pending"
- Polling or webhooks for completion notification

**Horizontal Scaling:**
- Stateless FastAPI service behind load balancer
- Independent scaling of API servers and QA workers
- Distributed job queue

**Streaming Ingestion:**
- Kafka or Kinesis for append-only event log
- Real-time trace building
- Near-real-time monitoring

**Cost Optimization:**
- Cache LLM results for similar reasoning patterns
- Batch QA jobs to amortize Docker startup
- Fine-tune smaller models after collecting ground truth

---

## Alternative: Run with Docker Compose

Skip the manual setup and run everything with Docker:

```bash
docker-compose up
```

This starts the API on port 8000. All dependencies are included in the container.

---

## How It Works

1. A developer's IDE sends a trace (JSON) containing their debugging session
2. FastAPI validates the trace using Pydantic and security checks
3. The trace is stored as a JSON file in data/
4. When finalized, the system:
   - Runs the repo's test command in an isolated Docker container
   - Extracts reasoning steps and sends them to GPT-4o-mini
   - Combines test results and reasoning evaluation into qa_results
5. The enriched trace is returned with both test outcomes and reasoning quality score

---

## Project Files

Key dependencies from requirements.txt:
- fastapi: Web framework
- uvicorn[standard]: ASGI server
- pydantic>=2.0: Data validation
- python-dotenv: Environment variables
- httpx: HTTP client
- openai: LLM API client
- docker: Docker SDK
- pytest: Testing framework

---

## Support

For issues or questions, please refer to the API_EXAMPLES.md file for detailed usage examples.

