#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower()).strip("-._")
    return slug or "boost-task"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_material(src: Path, materials_dir: Path) -> dict[str, Any]:
    src = src.expanduser().resolve()
    target = materials_dir / src.name
    if src.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)
        kind = "directory"
        size = None
        digest = None
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        kind = "file"
        size = target.stat().st_size
        digest = sha256_file(target)
    return {
        "source": str(src),
        "stored_at": str(target),
        "kind": kind,
        "bytes": size,
        "sha256": digest,
    }


def cmd_init(args: argparse.Namespace) -> None:
    if args.run:
        run = Path(args.run).expanduser().resolve()
        slug = safe_slug(args.slug or run.name)
    else:
        if not args.slug:
            raise SystemExit("--slug is required unless --run is provided.")
        slug = safe_slug(args.slug)
        base = Path(args.base).expanduser()
        run = (base / slug).resolve()
    original = run / "original"
    materials_dir = original / "materials"
    rounds = run / "rounds"
    reviews = run / "reviews"
    export = run / "export"
    for path in (original, materials_dir, rounds, reviews, export):
        path.mkdir(parents=True, exist_ok=True)

    prompt_path = Path(args.prompt_file).expanduser().resolve()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    (original / "user_prompt.md").write_text(prompt_text, encoding="utf-8")

    materials = []
    for item in args.material or []:
        materials.append(copy_material(Path(item), materials_dir))
    write_json(original / "materials_manifest.json", {"created_at": utc_now(), "materials": materials})

    state_path = run / "task.json"
    if state_path.exists() and not args.force:
        raise SystemExit(f"task.json already exists: {state_path}. Pass --force to overwrite.")
    write_json(
        state_path,
        {
            "schema_version": "expert_boost_loop.v1",
            "task_id": slug,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "status": "initialized",
            "package_root": str(run),
            "original_prompt": str(original / "user_prompt.md"),
            "materials_manifest": str(original / "materials_manifest.json"),
            "current_round": None,
            "next_review_index": 1,
            "review_governance": {
                "min_strengths_default": 1,
                "scores_required": [
                    "latest_deliverables_satisfaction",
                    "latest_deliverables_aligns_user_score",
                ],
                "quality_gate_required": True,
                "host_sets_min_weaknesses_each_round": True,
            },
            "rounds": [],
            "reviews": [],
        },
    )
    print(str(run))


def next_review_id(state: dict[str, Any]) -> str:
    index = int(state.get("next_review_index") or 1)
    return f"r{index:03d}_review"


def section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^#+\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^#+\s+", text[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def bullets(value: str) -> list[str]:
    result: list[str] = []
    for line in value.splitlines():
        match = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if not match:
            continue
        item = match.group(1).strip()
        if item and item not in {"_", "TBD", "N/A", "n/a"}:
            result.append(item)
    return result


def score_from_named_section(text: str, heading: str, max_value: int) -> Optional[dict[str, float]]:
    value = section(text, heading)
    if not value:
        return None
    match = re.search(r"\(?\s*([0-9]+(?:\.[0-9]+)?)\s*\)?\s*/\s*([0-9]+(?:\.[0-9]+)?)", value)
    if not match:
        return None
    return {"value": float(match.group(1)), "max": float(match.group(2) or max_value)}


def parse_review_text(text: str) -> dict[str, Any]:
    scores = {}
    satisfaction = score_from_named_section(text, "Latest Deliverables Satisfaction", 5)
    if satisfaction:
        scores["latest_deliverables_satisfaction"] = satisfaction
    aligns_user = score_from_named_section(text, "Latest Deliverables Aligns User Scores", 10)
    if aligns_user:
        scores["latest_deliverables_aligns_user_score"] = aligns_user
    return {
        "strengths": bullets(section(text, "Strengths")),
        "weaknesses": bullets(section(text, "Weaknesses")),
        "scores": scores,
        "notes": section(text, "Notes"),
    }


def validate_review(parsed: dict[str, Any], min_strengths: int, min_weaknesses: int) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    strengths = parsed.get("strengths") or []
    weaknesses = parsed.get("weaknesses") or []
    scores = parsed.get("scores") or {}
    if len(strengths) < min_strengths:
        warnings.append(f"Expected at least {min_strengths} strengths, found {len(strengths)}")
    if len(weaknesses) < min_weaknesses:
        errors.append(f"Expected at least {min_weaknesses} weaknesses, found {len(weaknesses)}")
    satisfaction = scores.get("latest_deliverables_satisfaction")
    aligns_user = scores.get("latest_deliverables_aligns_user_score")
    if not satisfaction:
        errors.append("Missing Latest Deliverables Satisfaction score in the form `()/5`")
    elif satisfaction.get("max") != 5 or not float(satisfaction.get("value", 0)).is_integer() or not 1 <= int(satisfaction["value"]) <= 5:
        errors.append("Latest Deliverables Satisfaction must be an integer from 1 to 5")
    if not aligns_user:
        errors.append("Missing Latest Deliverables Aligns User Scores score in the form `()/10`")
    elif aligns_user.get("max") != 10 or not float(aligns_user.get("value", 0)).is_integer() or not 1 <= int(aligns_user["value"]) <= 10:
        errors.append("Latest Deliverables Aligns User Scores must be an integer from 1 to 10")
    duplicate_strengths = sorted({item for item in strengths if strengths.count(item) > 1})
    duplicate_weaknesses = sorted({item for item in weaknesses if weaknesses.count(item) > 1})
    if duplicate_strengths:
        warnings.append(f"Duplicate strengths found: {duplicate_strengths}")
    if duplicate_weaknesses:
        errors.append(f"Duplicate weaknesses found: {duplicate_weaknesses}")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def cmd_review_template(args: argparse.Namespace) -> None:
    run = Path(args.run).expanduser().resolve()
    state = read_json(run / "task.json")
    review_id = args.review_id or next_review_id(state)
    review_dir = run / "reviews" / review_id
    review_dir.mkdir(parents=True, exist_ok=True)
    round_under_review = args.round_under_review or state.get("current_round") or ""
    deliverables_path = args.deliverables_path or (run / "rounds" / str(round_under_review) / "outputs")
    min_strengths = max(0, int(args.min_strengths))
    min_weaknesses = max(0, int(args.min_weaknesses))
    strengths = "\n".join("- " for _ in range(max(min_strengths, 1)))
    weaknesses = "\n".join("- " for _ in range(min_weaknesses))
    text = f"""# Expert Boost Comments - Reviewing `{round_under_review}`

## Round Information

| Field | Value |
| --- | --- |
| Review ID | `{review_id}` |
| Round under review | `{round_under_review}` |
| Deliverables path | `{deliverables_path}` |
| Minimum strengths requested | `{min_strengths}` |
| Minimum weaknesses requested | `{min_weaknesses}` |
| Created at | `{utc_now()}` |

## Strengths

> Strengths are useful for audit context, but keep this lightweight. Distinct bullets are best.

{strengths}

## Weaknesses

> Please provide at least {min_weaknesses} distinct, actionable weaknesses for this round.
> The next executor will see only these weaknesses, not the strengths, scores, or notes.
> If you believe no useful weaknesses remain, say so clearly and use the scores below.
> Good weaknesses are objective, specific, clear, and grounded in the deliverable or task materials.
> Avoid vague comments like "make it better", "too shallow", or "bad tone" unless you name the concrete issue and why it matters.
> If a weakness relies on an unstated industry rule, senior convention, or external constraint, include a short reason why that rule applies to this task.

{weaknesses}

## Latest Deliverables Satisfaction

> Score the current deliverables only. Use an integer from 1 to 5, where 5 means very satisfied and 1 means very dissatisfied.

()/5

## Latest Deliverables Aligns User Scores

> Score the current deliverables against your own expected performance on this task. Use an integer from 1 to 10. Treat 5 as about the level you personally would have achieved on this task.

()/10

## Notes

> Optional context for the host Codex. The next executor will not see this section.

"""
    path = review_dir / "comments_template.md"
    path.write_text(text, encoding="utf-8")
    write_json(
        review_dir / "comments_request.json",
        {
            "review_id": review_id,
            "created_at": utc_now(),
            "round_under_review": round_under_review,
            "deliverables_path": str(deliverables_path),
            "min_strengths": min_strengths,
            "min_weaknesses": min_weaknesses,
            "rationale": args.rationale or "",
        },
    )
    print(str(path))


def cmd_record_review(args: argparse.Namespace) -> None:
    run = Path(args.run).expanduser().resolve()
    state_path = run / "task.json"
    state = read_json(state_path)
    review_id = args.review_id or next_review_id(state)
    review_dir = run / "reviews" / review_id
    review_dir.mkdir(parents=True, exist_ok=True)

    raw_path = Path(args.raw_file).expanduser().resolve()
    raw_text = raw_path.read_text(encoding="utf-8")
    (review_dir / "raw_user_input.md").write_text(raw_text, encoding="utf-8")
    parsed = parse_review_text(raw_text)
    if args.strength:
        parsed["strengths"] = args.strength
    if args.weakness:
        parsed["weaknesses"] = args.weakness
    if args.satisfaction is not None:
        parsed.setdefault("scores", {})["latest_deliverables_satisfaction"] = {"value": float(args.satisfaction), "max": 5.0}
    if args.aligns_user_score is not None:
        parsed.setdefault("scores", {})["latest_deliverables_aligns_user_score"] = {"value": float(args.aligns_user_score), "max": 10.0}
    if args.notes:
        parsed["notes"] = args.notes
    validation = validate_review(parsed, max(0, int(args.min_strengths)), max(0, int(args.min_weaknesses)))

    record = {
        "review_id": review_id,
        "created_at": utc_now(),
        "round_under_review": args.round_under_review,
        "raw_text": raw_text,
        "strengths": parsed["strengths"],
        "weaknesses": parsed["weaknesses"],
        "scores": parsed["scores"],
        "notes": parsed["notes"],
        "review_gate": {
            "min_strengths": max(0, int(args.min_strengths)),
            "min_weaknesses": max(0, int(args.min_weaknesses)),
            "validation": validation,
            "quality_decision": args.quality_decision,
            "quality_issues": args.quality_issue,
            "host_decision": args.host_decision,
            "host_rationale": args.host_rationale or "",
            "forced_by_user": bool(args.forced_by_user),
        },
    }
    write_json(review_dir / "review.json", record)
    write_json(review_dir / "validation.json", validation)

    reviews = state.setdefault("reviews", [])
    if not any(item.get("review_id") == review_id for item in reviews):
        reviews.append(
            {
                "review_id": review_id,
                "round_under_review": args.round_under_review,
                "path": str(review_dir / "review.json"),
                "raw_input": str(review_dir / "raw_user_input.md"),
                "created_at": record["created_at"],
            }
        )
    state["next_review_index"] = max(int(state.get("next_review_index") or 1), int(review_id[1:4]) + 1)
    state["updated_at"] = utc_now()
    write_json(state_path, state)
    print(str(review_dir / "review.json"))


def artifact_manifest(root: Path) -> dict[str, Any]:
    files = []
    if root.exists():
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return {"root": str(root), "files": files, "file_count": len(files), "created_at": utc_now()}


def cmd_manifest(args: argparse.Namespace) -> None:
    run = Path(args.run).expanduser().resolve()
    round_dir = run / "rounds" / args.round
    outputs = round_dir / "outputs"
    manifest = {
        "round_id": args.round,
        "stage": args.stage,
        "created_at": utc_now(),
        "prompt": str(round_dir / "prompt.md"),
        "outputs": str(outputs),
        "final": str(round_dir / "final.md"),
        "artifact_manifest": artifact_manifest(outputs),
    }
    write_json(round_dir / "manifest.json", manifest)

    state_path = run / "task.json"
    state = read_json(state_path)
    rounds = state.setdefault("rounds", [])
    rounds = [item for item in rounds if item.get("round_id") != args.round]
    rounds.append({"round_id": args.round, "stage": args.stage, "manifest": str(round_dir / "manifest.json")})
    state["rounds"] = rounds
    state["current_round"] = args.round
    state["status"] = "awaiting_review"
    state["updated_at"] = utc_now()
    write_json(state_path, state)
    print(str(round_dir / "manifest.json"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="boost_record.py")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--slug", default=None)
    init.add_argument("--base", default=".codex-starboost")
    init.add_argument("--run", default=None, help="Exact task package directory to create/use.")
    init.add_argument("--prompt-file", required=True)
    init.add_argument("--material", action="append", default=[])
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    review = sub.add_parser("record-review")
    review.add_argument("--run", required=True)
    review.add_argument("--round-under-review", required=True)
    review.add_argument("--raw-file", required=True)
    review.add_argument("--review-id", default=None)
    review.add_argument("--min-strengths", type=int, default=0)
    review.add_argument("--min-weaknesses", type=int, default=0)
    review.add_argument("--quality-decision", choices=["accepted", "forced"], default="accepted")
    review.add_argument("--quality-issue", action="append", default=[])
    review.add_argument("--host-decision", choices=["request_more", "continue", "terminate"], default="continue")
    review.add_argument("--host-rationale", default="")
    review.add_argument("--forced-by-user", action="store_true")
    review.add_argument("--strength", action="append", default=[])
    review.add_argument("--weakness", action="append", default=[])
    review.add_argument("--satisfaction", type=int, default=None)
    review.add_argument("--aligns-user-score", type=int, default=None)
    review.add_argument("--notes", default="")
    review.set_defaults(func=cmd_record_review)

    template = sub.add_parser("review-template")
    template.add_argument("--run", required=True)
    template.add_argument("--round-under-review", default=None)
    template.add_argument("--deliverables-path", default=None)
    template.add_argument("--review-id", default=None)
    template.add_argument("--min-strengths", type=int, default=1)
    template.add_argument("--min-weaknesses", type=int, required=True)
    template.add_argument("--rationale", default="")
    template.set_defaults(func=cmd_review_template)

    manifest = sub.add_parser("manifest")
    manifest.add_argument("--run", required=True)
    manifest.add_argument("--round", required=True)
    manifest.add_argument("--stage", choices=["cold_start", "boosted"], required=True)
    manifest.set_defaults(func=cmd_manifest)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
