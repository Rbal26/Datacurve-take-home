import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JUDGE_PROMPT_TEMPLATE = """You are evaluating a software developer's reasoning process while fixing a bug.

Below is their chronological reasoning log:

---
{reasoning_text}
---

Evaluate their reasoning on these five dimensions (0-1 point each):

1. **Hypothesis Formation**: Did they form clear, testable hypotheses about the root cause?
2. **Evidence Gathering**: Did they systematically explore files/logs/commands to validate hypotheses?
3. **Logical Coherence**: Is the reasoning chain clear and logical?
4. **Validation**: Did they test their fix and verify it works?
5. **Depth**: Did they consider edge cases or alternative explanations?

Respond with JSON in this exact format:
{{
  "score": <sum of dimensions, 1.0-5.0>,
  "feedback": "<2-3 sentence explanation of the score>"
}}"""


def evaluate_reasoning(reasoning_steps: list[str]) -> dict:
    if not reasoning_steps:
        return {
            "reasoning_score": None,
            "reasoning_feedback": "No reasoning steps provided"
        }
    
    reasoning_text = "\n\n".join([f"[{i+1}] {step}" for i, step in enumerate(reasoning_steps)])
    
    prompt = JUDGE_PROMPT_TEMPLATE.format(reasoning_text=reasoning_text)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            timeout=30
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "reasoning_score": float(result.get("score", 3.0)),
            "reasoning_feedback": result.get("feedback", "No feedback provided")
        }
        
    except Exception as e:
        return {
            "reasoning_score": None,
            "reasoning_feedback": f"Reasoning evaluation unavailable: {str(e)}"
        }