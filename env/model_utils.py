from __future__ import annotations

import os
from typing import Any, Tuple

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

PREFERRED_TRAIN_MODEL = "sshleifer/tiny-gpt2"


def load_tiny_model_and_tokenizer(model_name: str = PREFERRED_TRAIN_MODEL) -> Tuple[Any, Any]:
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name, local_files_only=True)
    model.config.pad_token_id = tokenizer.pad_token_id
    model.eval()
    return model, tokenizer
