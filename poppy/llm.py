"""Anthropic client wrapper for the lesson-plan pipeline.

One LLM call per stage. Uses tool-use structured output so each stage's response
is validated against a Pydantic schema. Tracks token usage and cost.
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError


MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000

# Sonnet 4.6 pricing per 1M tokens
INPUT_PRICE_PER_MTOK = 3.00
OUTPUT_PRICE_PER_MTOK = 15.00


T = TypeVar("T", bound=BaseModel)


@dataclass
class CostMeter:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    by_stage: dict[str, dict[str, int]] = field(default_factory=dict)

    def record(self, stage: str, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.calls += 1
        self.by_stage[stage] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    @property
    def cost_usd(self) -> float:
        return (
            self.input_tokens * INPUT_PRICE_PER_MTOK / 1_000_000
            + self.output_tokens * OUTPUT_PRICE_PER_MTOK / 1_000_000
        )


def _strip_pydantic_extras(schema: dict) -> dict:
    """Pydantic emits a `title` field on every property and on the root object.
    The Anthropic API tolerates these, but stripping them keeps the input_schema
    lean and matches the API's preferred shape.
    """
    if not isinstance(schema, dict):
        return schema
    cleaned = {k: v for k, v in schema.items() if k != "title"}
    if "properties" in cleaned and isinstance(cleaned["properties"], dict):
        cleaned["properties"] = {
            k: _strip_pydantic_extras(v) for k, v in cleaned["properties"].items()
        }
    if "$defs" in cleaned and isinstance(cleaned["$defs"], dict):
        cleaned["$defs"] = {
            k: _strip_pydantic_extras(v) for k, v in cleaned["$defs"].items()
        }
    if "items" in cleaned and isinstance(cleaned["items"], dict):
        cleaned["items"] = _strip_pydantic_extras(cleaned["items"])
    return cleaned


def _try_parse_listish_string(s: str) -> list | None:
    """Try multiple parsers to recover a list from a string the model emitted
    in place of a list field. Returns None if no parser succeeds.
    """
    # 1. Strict JSON — what we want
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    # 2. Python literal — handles single-quoted strings, trailing commas in some cases
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, list):
            return parsed
    except (SyntaxError, ValueError):
        pass
    # 3. Last resort: if it looks like ["...", "..."], extract by splitting on
    # `","` boundary patterns. Brittle but recovers from unescaped inner quotes.
    stripped = s.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if inner.startswith('"') and inner.endswith('"'):
            # split on `","` (close-quote, comma, optional whitespace, open-quote)
            import re
            parts = re.split(r'"\s*,\s*"', inner[1:-1])
            return [p.replace('\\"', '"').replace("\\n", "\n") for p in parts]
    return None


def _coerce_list_artifacts(data: Any, schema_dict: dict) -> Any:
    """Fix a common LLM artifact: a list-shaped string emitted into a list field.

    The model occasionally returns `'["a", "b"]'` (a string) instead of `["a", "b"]`
    for a `list[str]` field. We try several parsers to recover the list. Other
    coercions are NOT done here — bigger structural problems should fail loud
    and trigger a retry.
    """
    if not isinstance(data, dict):
        return data
    properties = schema_dict.get("properties", {})
    out = dict(data)
    for key, value in data.items():
        prop = properties.get(key, {})
        if prop.get("type") == "array" and isinstance(value, str):
            parsed = _try_parse_listish_string(value)
            if parsed is not None:
                out[key] = parsed
    return out


def _dump_raw_input(stage: str, attempt: int, raw_input: Any) -> Path:
    """Persist the model's raw tool input for post-mortem debugging."""
    debug_dir = Path("outputs") / "_debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    path = debug_dir / f"{stage}_attempt{attempt}.json"
    try:
        path.write_text(json.dumps(raw_input, indent=2, default=str), encoding="utf-8")
    except (TypeError, ValueError):
        path.write_text(repr(raw_input), encoding="utf-8")
    return path


def call_structured(
    client: anthropic.Anthropic,
    *,
    stage: str,
    system: str,
    user: str,
    schema: type[T],
    tool_name: str,
    tool_description: str,
    cost: CostMeter,
) -> T:
    """Invoke Claude with a single forced tool call. Return a validated Pydantic instance.

    Retries once on validation failure with the error message appended to the
    user prompt — Sonnet 4.6 occasionally emits malformed structured output that
    a single feedback round trip resolves.
    """
    input_schema = _strip_pydantic_extras(schema.model_json_schema())

    # Note: adaptive thinking is incompatible with forced tool_choice on Sonnet 4.6
    # ("Thinking may not be enabled when tool_choice forces tool use"). Forced
    # tool use is the right choice here (we always want structured output), so
    # thinking is off. Phase 0 stages are constrained generation, not deep
    # reasoning, so this trade-off is fine.
    base_kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        tools=[
            {
                "name": tool_name,
                "description": tool_description,
                "input_schema": input_schema,
            }
        ],
        tool_choice={"type": "tool", "name": tool_name},
    )

    messages: list[dict] = [{"role": "user", "content": user}]

    for attempt in (1, 2):
        response = client.messages.create(messages=messages, **base_kwargs)
        cost.record(
            f"{stage}-retry" if attempt == 2 else stage,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        tool_use = next(
            (block for block in response.content if block.type == "tool_use"),
            None,
        )
        if tool_use is None:
            raise RuntimeError(
                f"Stage {stage}: no tool_use block in response "
                f"(stop_reason={response.stop_reason}). "
                f"Content blocks: {[b.type for b in response.content]}"
            )

        coerced = _coerce_list_artifacts(tool_use.input, input_schema)
        try:
            return schema.model_validate(coerced)
        except ValidationError as e:
            dump_path = _dump_raw_input(stage, attempt, tool_use.input)
            print(
                f"  [stage={stage} attempt={attempt}] validation failed; "
                f"raw input saved to {dump_path}",
                file=sys.stderr,
            )
            if attempt == 2:
                raise
            # Retry: feed the assistant's tool call back, then a tool_result
            # explaining the validation error so the model can fix its output.
            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "is_error": True,
                            "content": (
                                f"The previous tool call failed schema validation. "
                                f"Pydantic errors:\n{e}\n\n"
                                "Re-emit the same tool call with the errors fixed. "
                                "Pay close attention to field types — list fields must "
                                "be JSON arrays, not strings containing JSON."
                            ),
                        }
                    ],
                }
            )

    # Unreachable — both branches above either return or raise.
    raise RuntimeError(f"Stage {stage}: retry loop exited without resolution")
