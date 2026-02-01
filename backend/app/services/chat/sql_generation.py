"""SQL generation service using Ollama LLM."""
import re
from app.prompts import load_prompt
from app.services.llm.ollama import OllamaProvider
from app.config import settings


def generate_sql(question: str, history: list[dict] | None = None) -> str:
    """Generate SQL query from natural language question.
    
    Args:
        question: Natural language question from user
        history: Optional conversation history (list of {role, content} dicts)
        
    Returns:
        Raw SQL query string
        
    Raises:
        RuntimeError: If LLM call fails
    """
    system_prompt = load_prompt("sql_generation_v1")
    
    # Build user prompt with question and optional history context
    user_prompt = question
    if history:
        # Include last 3 turns for context
        recent_history = history[-3:]
        history_text = "\n".join([
            f"{turn['role']}: {turn['content']}" 
            for turn in recent_history
        ])
        user_prompt = f"Previous conversation:\n{history_text}\n\nCurrent question: {question}"
    
    # Call Ollama for text generation (no JSON schema)
    client = OllamaProvider()
    try:
        response = client.client.chat(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        sql = response["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"SQL generation failed: {e}") from e
    
    # Extract SQL from response (handle markdown code blocks)
    sql = _extract_sql(sql)
    
    return sql.strip()


def _extract_sql(text: str) -> str:
    """Extract SQL from LLM response, handling markdown code blocks."""
    # Check for ```sql code blocks
    sql_block = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if sql_block:
        return sql_block.group(1)
    
    # Check for generic ``` code blocks
    code_block = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if code_block:
        return code_block.group(1)
    
    # Return raw response if no code blocks found
    return text
