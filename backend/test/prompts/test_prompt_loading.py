from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from typing import Callable

import pytest

PROMPTS_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "prompts" / "__init__.py"
)
spec = spec_from_loader(
    "prompts_module",
    SourceFileLoader("prompts_module", str(PROMPTS_MODULE_PATH))
)
if spec is None or spec.loader is None:
    raise ImportError("Unable to load prompts module")
module = module_from_spec(spec)
spec.loader.exec_module(module)
load_prompt: Callable[[str], str] = module.load_prompt


def test_load_prompt_returns_content():
    content = load_prompt("cv_extraction_v1")
    assert isinstance(content, str)
    assert content.strip()


def test_load_prompt_summary_returns_content():
    content = load_prompt("cv_summary_v1")
    assert isinstance(content, str)
    assert content.strip()


def test_load_prompt_missing_raises():
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent")
