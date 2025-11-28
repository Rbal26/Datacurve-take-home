from fastapi import APIRouter, HTTPException
from app.models import Trace
from app.storage import save_trace, load_trace

router = APIRouter()


@router.post("/traces", status_code=201)
def create_trace(trace: Trace):
    trace_id = save_trace(trace)
    return {"trace_id": trace_id, "status": "stored"}


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str):
    try:
        trace = load_trace(trace_id)
        return trace
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")