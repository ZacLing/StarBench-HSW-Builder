#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def active_rubrics(data: dict[str, Any]) -> list[dict[str, Any]]:
    rubrics = data.get("rubrics")
    if not isinstance(rubrics, list):
        raise SystemExit("rubric file must contain a top-level `rubrics` list")
    active = []
    for item in rubrics:
        if not isinstance(item, dict):
            raise SystemExit("each rubric must be an object")
        status = str(item.get("status") or "candidate")
        if status in {"deleted_by_user", "rejected", "not_crystallized"}:
            continue
        active.append(item)
    return sorted(active, key=lambda item: (rank_key(item), str(item.get("id") or "")))


def rank_key(item: dict[str, Any]) -> tuple[int, int]:
    rank = item.get("rank")
    if isinstance(rank, int):
        return (0, rank)
    if isinstance(rank, str) and rank.isdigit():
        return (0, int(rank))
    return (1, 10**9)


def validate_item(item: dict[str, Any], index: int) -> list[str]:
    errors = []
    prefix = f"rubrics[{index}]"
    for key in ("id", "question"):
        if not isinstance(item.get(key), str) or not item.get(key, "").strip():
            errors.append(f"{prefix}.{key} must be a non-empty string")
    if not isinstance(item.get("expected"), bool):
        errors.append(f"{prefix}.expected must be boolean")
    if not isinstance(item.get("fail_fast"), bool):
        errors.append(f"{prefix}.fail_fast must be boolean")
    question = str(item.get("question") or "").strip()
    if question and not question.endswith(("?", "？")):
        errors.append(f"{prefix}.question should be a question ending with `?` or `？`")
    display_question = item.get("display_question")
    if display_question is not None:
        if not isinstance(display_question, str) or not display_question.strip():
            errors.append(f"{prefix}.display_question must be a non-empty string when present")
    return errors


def cmd_validate(args: argparse.Namespace) -> None:
    path = Path(args.file).expanduser().resolve()
    data = read_json(path)
    active = active_rubrics(data)
    errors: list[str] = []
    if len(active) < int(args.min_active):
        errors.append(f"expected at least {args.min_active} active rubrics, found {len(active)}")
    seen = set()
    for index, item in enumerate(data.get("rubrics") or []):
        rid = item.get("id")
        if rid in seen:
            errors.append(f"duplicate rubric id: {rid}")
        seen.add(rid)
        if str(item.get("status") or "candidate") not in {"deleted_by_user", "rejected", "not_crystallized"}:
            errors.extend(validate_item(item, index))
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"valid: {len(active)} active rubrics")


def cmd_markdown(args: argparse.Namespace) -> None:
    src = Path(args.file).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    data = read_json(src)
    active = active_rubrics(data)
    lines = [f"# {args.title}", ""]
    if data.get("task_id"):
        lines.extend([f"Task ID: `{data['task_id']}`", ""])
    for item in active:
        label = "fail-fast" if item.get("fail_fast") else "make-better"
        rank = item.get("rank")
        rank_text = f"{args.rank_label} {rank}. " if rank is not None else ""
        question = str(item.get("display_question") or item.get("question") or "").strip()
        lines.append(f"- {rank_text}{item.get('id')}: {question} [{label}]")
    deleted = [item for item in data.get("rubrics", []) if str(item.get("status") or "") == "deleted_by_user"]
    if deleted:
        lines.extend(["", f"## {args.deleted_title}", ""])
        for item in deleted:
            question = str(item.get("display_question") or item.get("question") or "").strip()
            lines.append(f"- {item.get('id')}: {question}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out))


def cmd_bench_rubrics(args: argparse.Namespace) -> None:
    src = Path(args.file).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    data = read_json(src)
    selected = active_rubrics(data)[: int(args.limit)]
    if len(selected) < int(args.limit) and not args.allow_fewer:
        raise SystemExit(f"need {args.limit} active rubrics for bench export, found {len(selected)}")
    errors: list[str] = []
    for index, item in enumerate(selected):
        errors.extend(validate_item(item, index))
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    bench = {
        "rubrics": [
            {
                "id": str(item["id"]),
                "fail_fast": item["fail_fast"],
                "expected": item["expected"],
                "question": str(item["question"]).strip(),
            }
            for item in selected
        ]
    }
    write_json(out, bench)
    print(str(out))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rubric_store.py")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--file", required=True)
    validate.add_argument("--min-active", type=int, default=15)
    validate.set_defaults(func=cmd_validate)

    markdown = sub.add_parser("markdown")
    markdown.add_argument("--file", required=True)
    markdown.add_argument("--out", required=True)
    markdown.add_argument("--title", default="Curated Rubrics")
    markdown.add_argument("--rank-label", default="Rank")
    markdown.add_argument("--deleted-title", default="Deleted By User")
    markdown.set_defaults(func=cmd_markdown)

    bench = sub.add_parser("bench-rubrics")
    bench.add_argument("--file", required=True)
    bench.add_argument("--out", required=True)
    bench.add_argument("--limit", type=int, default=15)
    bench.add_argument("--allow-fewer", action="store_true")
    bench.set_defaults(func=cmd_bench_rubrics)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
