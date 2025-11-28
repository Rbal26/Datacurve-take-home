import json
from pathlib import Path
from uuid import uuid4
from app.models import Trace

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def save_trace(trace: Trace) -> str:
    if not trace.trace_id:
        trace.trace_id = str(uuid4())
    
    file_path = DATA_DIR / f"{trace.trace_id}.json"
    with open(file_path, "w") as f:
        json.dump(json.loads(trace.model_dump_json()), f, indent=2)
    
    return trace.trace_id


def load_trace(trace_id: str) -> Trace:
    file_path = DATA_DIR / f"{trace_id}.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Trace {trace_id} not found")
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    return Trace.model_validate(data)


def trace_exists(trace_id: str) -> bool:
    file_path = DATA_DIR / f"{trace_id}.json"
    return file_path.exists()