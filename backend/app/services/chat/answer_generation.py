"""Answer generation service using Ollama LLM."""
import json
from app.prompts import load_prompt
from app.services.llm.ollama import OllamaProvider
from app.config import settings


def generate_answer(question: str, rows: list[dict], columns: list[str]) -> str:
    """Generate natural language answer from SQL query results.
    
    Args:
        question: Original user question
        rows: Retrieved data rows (list of dicts)
        columns: List of column names in results
        
    Returns:
        Natural language answer string
        
    Raises:
        RuntimeError: If LLM call fails
    """
    system_prompt = load_prompt("answer_generation_v1")
    
    # Format rows as readable JSON
    rows_json = json.dumps(rows, indent=2, default=str)
    
    # Build user prompt with all context
    user_prompt = f"""Question: {question}

Row Count: {len(rows)}
Columns: {', '.join(columns)}

Data Rows:
{rows_json}

Generate a natural language answer based only on the data above."""
    
    # Call Ollama for text generation
    client = OllamaProvider()
    try:
        response = client.client.chat(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        answer = response["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(f"Answer generation failed: {e}") from e
    
    return answer
