#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STEP_KEYS = ["step_id", "step_type", "instruction", "reasoning"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{label} must be a non-empty string")
    return value.strip()


def normalize_reference(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SystemExit("human reference draft must be a JSON object")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise SystemExit("human reference draft must contain a non-empty `steps` list")

    normalized_steps: list[dict[str, str]] = []
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise SystemExit(f"steps[{index - 1}] must be an object")
        step_id = step.get("step_id") or f"H{index:03d}"
        step_type = step.get("step_type", step.get("type"))
        normalized_steps.append(
            {
                "step_id": require_text(step_id, f"steps[{index - 1}].step_id"),
                "step_type": require_text(step_type, f"steps[{index - 1}].step_type"),
                "instruction": require_text(step.get("instruction"), f"steps[{index - 1}].instruction"),
                "reasoning": require_text(step.get("reasoning"), f"steps[{index - 1}].reasoning"),
            }
        )
    return {"steps": normalized_steps}


def validate_reference(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or list(data.keys()) != ["steps"]:
        raise SystemExit("human_reference.json must contain only the top-level key `steps`")
    steps = data["steps"]
    if not isinstance(steps, list) or not steps:
        raise SystemExit("human_reference.json must contain a non-empty `steps` list")
    seen: set[str] = set()
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise SystemExit(f"steps[{index}] must be an object")
        if list(step.keys()) != STEP_KEYS:
            raise SystemExit(f"steps[{index}] keys must be exactly: {', '.join(STEP_KEYS)}")
        for key in STEP_KEYS:
            require_text(step[key], f"steps[{index}].{key}")
        if step["step_id"] in seen:
            raise SystemExit(f"duplicate step_id: {step['step_id']}")
        seen.add(step["step_id"])
    return data


def cmd_save_raw(args: argparse.Namespace) -> None:
    run = Path(args.run).expanduser().resolve()
    out = Path(args.out).expanduser().resolve() if args.out else run / "export" / "human_reference_raw.md"
    if args.text_file:
        text = Path(args.text_file).expanduser().read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    if not text.strip():
        raise SystemExit("raw human reference text is empty")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.rstrip() + "\n", encoding="utf-8")
    print(str(out))


def cmd_normalize(args: argparse.Namespace) -> None:
    draft = read_json(Path(args.draft).expanduser().resolve())
    normalized = validate_reference(normalize_reference(draft))
    write_json(Path(args.out).expanduser().resolve(), normalized)
    print(str(Path(args.out).expanduser().resolve()))


def cmd_validate(args: argparse.Namespace) -> None:
    data = read_json(Path(args.file).expanduser().resolve())
    validated = validate_reference(data)
    print(f"valid: {len(validated['steps'])} steps")


def cmd_markdown(args: argparse.Namespace) -> None:
    data = validate_reference(read_json(Path(args.file).expanduser().resolve()))
    lines = [args.title, ""]
    for step in data["steps"]:
        lines.append(f"## {step['step_id']}: {step['step_type']}")
        lines.append("")
        lines.append(f"**Instruction:** {step['instruction']}")
        lines.append("")
        lines.append(f"**Reasoning:** {step['reasoning']}")
        lines.append("")
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(str(out))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="human_reference_store.py")
    sub = parser.add_subparsers(dest="command", required=True)

    save_raw = sub.add_parser("save-raw")
    save_raw.add_argument("--run", required=True)
    save_raw.add_argument("--text-file", default=None)
    save_raw.add_argument("--out", default=None)
    save_raw.set_defaults(func=cmd_save_raw)

    normalize = sub.add_parser("normalize")
    normalize.add_argument("--draft", required=True)
    normalize.add_argument("--out", required=True)
    normalize.set_defaults(func=cmd_normalize)

    validate = sub.add_parser("validate")
    validate.add_argument("--file", required=True)
    validate.set_defaults(func=cmd_validate)

    markdown = sub.add_parser("markdown")
    markdown.add_argument("--file", required=True)
    markdown.add_argument("--out", required=True)
    markdown.add_argument("--title", default="# Human Reference")
    markdown.set_defaults(func=cmd_markdown)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
