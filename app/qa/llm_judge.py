import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from app.utils.logger import setup_logger

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = setup_logger(__name__)

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
        logger.warning("No reasoning steps provided for evaluation")
        return {
            "reasoning_score": None,
            "reasoning_feedback": "No reasoning steps provided"
        }
    
    logger.info(f"Evaluating {len(reasoning_steps)} reasoning steps with GPT-4o-mini")
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
        score = float(result.get("score", 3.0))
        
        logger.info(f"LLM evaluation successful: score={score}")
        
        return {
            "reasoning_score": score,
            "reasoning_feedback": result.get("feedback", "No feedback provided")
        }
        
    except Exception as e:
        logger.error(f"LLM evaluation failed: {str(e)}")
        return {
            "reasoning_score": None,
            "reasoning_feedback": f"Reasoning evaluation unavailable: {str(e)}"
        }