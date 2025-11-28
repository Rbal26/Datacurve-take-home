from fastapi import APIRouter, HTTPException
from app.models import Trace
from app.storage import save_trace, load_trace, append_events

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

@router.post("/traces/{trace_id}/events")
def append_trace_events(trace_id: str, payload: dict):
    try:
        events = payload.get("events", [])
        
        if not events:
            raise HTTPException(status_code=400, detail="No events provided")
        
        from app.models import Event
        validated_events = []
        for event_data in events:
            if isinstance(event_data, dict):
                from app.models import (
                    FileOpenEvent,
                    FileCloseEvent,
                    CodeEditEvent,
                    TerminalCommandEvent,
                    TestResultEvent,
                    ReasoningStepEvent
                )
                
                event_type = event_data.get("event_type")
                event_map = {
                    "file_open": FileOpenEvent,
                    "file_close": FileCloseEvent,
                    "code_edit": CodeEditEvent,
                    "terminal_command": TerminalCommandEvent,
                    "test_result": TestResultEvent,
                    "reasoning_step": ReasoningStepEvent
                }
                
                if event_type in event_map:
                    validated_events.append(event_map[event_type].model_validate(event_data))
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")
            else:
                validated_events.append(event_data)
        
        count = append_events(trace_id, validated_events)
        return {"trace_id": trace_id, "appended_events": count}
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))