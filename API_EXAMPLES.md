# API Quick Reference

Copy-paste examples for testing the API.

**Before running these:** Make sure the API is running with `uvicorn main:app --reload`

---

## Health Check

**Windows:**
```powershell
Invoke-WebRequest http://localhost:8000/health
```

**Mac/Linux:**
```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

---

## Create a Trace

The API will auto-generate a trace ID for you.

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
    start_time = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri http://localhost:8000/traces -Method POST -ContentType "application/json" -Body $body
$traceId = ($response.Content | ConvertFrom-Json).trace_id
Write-Host "Created trace: $traceId"
```

**Mac/Linux:**
```bash
response=$(curl -s -X POST http://localhost:8000/traces \
  -H "Content-Type: application/json" \
  -d "{
    \"developer_id\": \"dev-001\",
    \"repo\": {
      \"name\": \"my-app\",
      \"url\": \"https://github.com/user/repo\",
      \"branch\": \"main\",
      \"commit_before\": \"abc123\",
      \"commit_after\": \"def456\",
      \"test_command\": \"pytest\"
    },
    \"start_time\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }")

trace_id=$(echo $response | grep -o '"trace_id":"[^"]*' | cut -d'"' -f4)
echo "Created trace: $trace_id"
```

Save the `trace_id` - you'll need it for the next steps!

---

## Add Events to Your Trace

Replace `<trace-id>` with your actual trace ID from above.

**Windows:**
```powershell
$events = @{
    events = @(
        @{
            event_type = "reasoning_step"
            timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
            data = @{ content = "Found the bug in auth.py line 45" }
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-WebRequest -Uri "http://localhost:8000/traces/<trace-id>/events" -Method POST -ContentType "application/json" -Body $events
```

**Mac/Linux:**
```bash
curl -X POST http://localhost:8000/traces/<trace-id>/events \
  -H "Content-Type: application/json" \
  -d "{
    \"events\": [
      {
        \"event_type\": \"reasoning_step\",
        \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
        \"data\": {
          \"content\": \"Found the bug in auth.py line 45\"
        }
      }
    ]
  }"
```

You can call this endpoint multiple times to add more events.

---

## Run Quality Analysis (Finalize)

This runs the tests in Docker and evaluates reasoning with GPT-4o-mini.

**Windows:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/traces/<trace-id>/finalize" -Method POST
```

**Mac/Linux:**
```bash
curl -X POST http://localhost:8000/traces/<trace-id>/finalize
```

This returns the full trace with `qa_results` populated.

---

## Retrieve a Trace

**Windows:**
```powershell
Invoke-WebRequest http://localhost:8000/traces/<trace-id>
```

**Mac/Linux:**
```bash
curl http://localhost:8000/traces/<trace-id>
```

---

## Supported Event Types

**reasoning_step** - Developer's thought process
- Required: `content` (string)

**file_open** - Developer opens a file
- Required: `file_path` (string)

**file_close** - Developer closes a file
- Required: `file_path` (string)

**code_edit** - Code modification
- Required: `file_path` (string), `diff` (string)

**terminal_command** - Shell command execution
- Required: `command` (string), `exit_code` (int), `output` (string), `duration_ms` (int)

**test_result** - Test suite results
- Required: `tests_passed` (bool), `test_command` (string), `failed_tests` (array), `summary` (string)

All events also need: `event_type` and `timestamp` (ISO 8601 format like "2025-11-27T10:00:00Z")
