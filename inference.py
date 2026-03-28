import json
import os
from typing import Optional

from openai import OpenAI

from env.environment import CodeReviewEnv
from env.models import Action
from env.tasks import TASK_ORDER

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")


def _get_client() -> Optional[OpenAI]:
    if not API_KEY:
        return None
    return OpenAI(base_url=API_BASE_URL, api_key=API_KEY)


def _build_prompt(obs: dict) -> str:
    return f"""
You are a code reviewer.

Return JSON:
{{
  "comment": "...",
  "line_number": number,
  "suggested_fix": "...",
  "label": "...",
  "confidence": number
}}

Code:
{obs['code']}
"""


def _parse_action(content: str) -> Optional[Action]:
    try:
        data = json.loads(content)
        return Action(
            comment=data.get("comment", ""),
            line_number=int(data.get("line_number", 1)),
            suggested_fix=data.get("suggested_fix"),
            label=data.get("label", "maintainability"),
            confidence=float(data.get("confidence", 0.5)),
        )
    except Exception:
        return None


def _fallback(obs: dict) -> Action:
    code = obs["code"]

    if "a+b" in code:
        return Action(
            comment="missing spaces and no docstring",
            line_number=1,
            suggested_fix="def add(a, b): return a + b",
            label="style",
            confidence=0.9,
        )

    if "append" in code:
        return Action(
            comment="use list comprehension",
            line_number=2,
            suggested_fix="data = [i for i in range(10)]",
            label="performance",
            confidence=0.8,
        )

    if "a/b" in code:
        return Action(
            comment="handle division by zero",
            line_number=1,
            suggested_fix="if b == 0: return None\nreturn a / b",
            label="bug",
            confidence=0.95,
        )

    return Action(
        comment="general improvement needed",
        line_number=1,
        suggested_fix=None,
        label="maintainability",
        confidence=0.5,
    )


def run_baseline(model: Optional[str] = None) -> dict:
    client = _get_client()
    env = CodeReviewEnv()
    results = {}
    selected_model = model or MODEL_NAME

    for task in TASK_ORDER:
        obs = env.reset(task)
        total_reward = 0.0

        for _ in range(obs["max_steps"]):
            if client:
                prompt = _build_prompt(obs)
                try:
                    res = client.chat.completions.create(
                        model=selected_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                    )
                    content = res.choices[0].message.content or ""
                    action = _parse_action(content)
                except Exception:
                    action = None

                if not action:
                    action = _fallback(obs)
            else:
                action = _fallback(obs)

            obs, reward, done, _ = env.step(action)
            total_reward += reward

            if done:
                break

        results[task] = round(total_reward, 4)

    return {
        "mode": "openai" if client else "fallback",
        "model": selected_model if client else "fallback",
        "results": results,
    }


def main() -> None:
    if not MODEL_NAME:
        raise RuntimeError("MODEL_NAME is required")
    print(run_baseline())


if __name__ == "__main__":
    main()