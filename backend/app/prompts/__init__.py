from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    prompt_path = PROMPTS_DIR / f"{name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {name}")
    return prompt_path.read_text(encoding="utf-8")
