from fastapi import APIRouter, HTTPException
from app.models import Trace
from app.storage import save_trace, load_trace, append_events
from app.qa import run_tests_in_docker, evaluate_reasoning
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/traces", status_code=201)
def create_trace(trace: Trace):
    logger.info(f"Received trace from developer {trace.developer_id} with {len(trace.events)} events")
    trace_id = save_trace(trace)
    logger.info(f"Trace {trace_id} stored successfully")
    return {"trace_id": trace_id, "status": "stored"}


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str):
    try:
        trace = load_trace(trace_id)
        logger.info(f"Retrieved trace {trace_id}")
        return trace
    except FileNotFoundError:
        logger.warning(f"Trace {trace_id} not found")
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

@router.post("/traces/{trace_id}/events")
def append_trace_events(trace_id: str, payload: dict):
    try:
        events = payload.get("events", [])
        
        if not events:
            raise HTTPException(status_code=400, detail="No events provided")
        
        logger.info(f"Appending {len(events)} events to trace {trace_id}")
        
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
        logger.info(f"Successfully appended {count} events to trace {trace_id}")
        return {"trace_id": trace_id, "appended_events": count}
        
    except FileNotFoundError:
        logger.warning(f"Attempted to append events to non-existent trace {trace_id}")
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    except Exception as e:
        logger.error(f"Failed to append events to trace {trace_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/traces/{trace_id}/finalize")
def finalize_trace(trace_id: str):
    try:
        logger.info(f"Starting QA pipeline for trace {trace_id}")
        trace = load_trace(trace_id)
        
        logger.info(f"Running Docker tests for trace {trace_id}")
        test_results = run_tests_in_docker("sample_repo", trace.repo.test_command)
        logger.info(f"Docker tests completed for trace {trace_id}: tests_passed={test_results['tests_passed']}")
        
        reasoning_steps = [
            event.data.content 
            for event in trace.events 
            if event.event_type == "reasoning_step"
        ]
        
        logger.info(f"Evaluating {len(reasoning_steps)} reasoning steps for trace {trace_id}")
        reasoning_results = evaluate_reasoning(reasoning_steps)
        logger.info(f"LLM evaluation completed for trace {trace_id}: score={reasoning_results['reasoning_score']}")
        
        from app.models import QAResults
        trace.qa_results = QAResults(
            tests_passed=test_results["tests_passed"],
            test_exit_code=test_results["test_exit_code"],
            test_output_snippet=test_results["test_output_snippet"],
            reasoning_score=reasoning_results["reasoning_score"],
            reasoning_feedback=reasoning_results["reasoning_feedback"]
        )
        
        save_trace(trace)
        logger.info(f"QA pipeline completed for trace {trace_id}")
        
        return trace
        
    except FileNotFoundError:
        logger.error(f"Trace {trace_id} not found for finalization")
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    except Exception as e:
        logger.error(f"Finalization failed for trace {trace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Finalization failed: {str(e)}")