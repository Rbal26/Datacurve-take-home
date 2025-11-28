import pytest
from unittest.mock import patch, MagicMock
from app.qa import evaluate_reasoning


def test_evaluate_reasoning_with_steps():
    reasoning_steps = [
        "I suspect the bug is in login.py line 45",
        "Checked the code and user.profile can be null",
        "Added null check before accessing email",
        "Ran tests and they all passed"
    ]
    
    with patch('app.qa.llm_judge.client') as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"score": 4.5, "feedback": "Clear and methodical reasoning"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = evaluate_reasoning(reasoning_steps)
        
        assert result["reasoning_score"] == 4.5
        assert "Clear" in result["reasoning_feedback"]


def test_evaluate_reasoning_empty_steps():
    result = evaluate_reasoning([])
    
    assert result["reasoning_score"] is None
    assert "No reasoning" in result["reasoning_feedback"]


def test_evaluate_reasoning_api_error():
    reasoning_steps = ["Test reasoning"]
    
    with patch('app.qa.llm_judge.client') as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        result = evaluate_reasoning(reasoning_steps)
        
        assert result["reasoning_score"] is None
        assert "unavailable" in result["reasoning_feedback"].lower()


def test_evaluate_reasoning_formats_steps_correctly():
    reasoning_steps = ["First step", "Second step", "Third step"]
    
    with patch('app.qa.llm_judge.client') as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"score": 3.0, "feedback": "Adequate"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        result = evaluate_reasoning(reasoning_steps)
        
        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args.kwargs['messages'][0]['content']
        
        assert "[1] First step" in prompt
        assert "[2] Second step" in prompt
        assert "[3] Third step" in prompt