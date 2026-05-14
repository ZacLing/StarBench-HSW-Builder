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


def strip_code_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return value.strip()


def clean_prompt(raw_text: str) -> tuple[str, str, dict[str, Any]]:
    """Split chat scaffolding from the task prompt.

    The clean prompt is what executors and benchmark task packages should see.
    Removed scaffolding remains audit-only and must not be passed as execution context.
    """

    normalized = raw_text.replace("\r\n", "\n")
    notes: list[str] = []
    transformations: list[str] = []
    text = normalized

    request_heading = re.search(r"(?im)^##\s*My request for Codex:\s*$", text)
    if request_heading:
        before = text[: request_heading.start()].strip()
        after = text[request_heading.end() :].strip()
        if before:
            notes.append("## Removed pre-request scaffolding\n\n" + before)
        text = after
        transformations.append("extracted_body_after_my_request_heading")

    kept_lines: list[str] = []
    removed_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        is_skill_invocation = bool(
            re.fullmatch(r"(use\s+)?\$?expert-boost-loop(\s+skill)?", lower)
            or re.fullmatch(r"用\s*expert-boost-loop\s*skill", stripped, flags=re.IGNORECASE)
            or re.fullmatch(r"使用\s*expert-boost-loop\s*skill", stripped, flags=re.IGNORECASE)
        )
        is_file_heading = bool(re.fullmatch(r"#*\s*files mentioned by the user:\s*", lower))
        is_empty_file_marker = bool(re.fullmatch(r"##\s*[^:]+:\s*[A-Za-z]:[\\/].*", stripped))
        if is_skill_invocation or is_file_heading or is_empty_file_marker:
            removed_lines.append(line)
            continue
        kept_lines.append(line)

    if removed_lines:
        notes.append("## Removed inline scaffolding\n\n" + "\n".join(removed_lines).strip())
        transformations.append("removed_skill_invocations_or_file_scaffolding")

    clean = strip_code_fence("\n".join(kept_lines))
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    if not clean:
        clean = normalized.strip()
        transformations.append("fallback_to_raw_prompt_because_clean_was_empty")

    metadata = {
        "clean_prompt_changed": clean != normalized.strip(),
        "transformations": transformations,
    }
    return clean + "\n", ("\n\n".join(notes).strip() + "\n" if notes else ""), metadata


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
    audit = run / "audit"
    materials_dir = original / "materials"
    rounds = run / "rounds"
    reviews = run / "reviews"
    export = run / "export"
    for path in (original, audit, materials_dir, rounds, reviews, export):
        path.mkdir(parents=True, exist_ok=True)

    prompt_path = Path(args.prompt_file).expanduser().resolve()
    raw_prompt_text = prompt_path.read_text(encoding="utf-8")
    (audit / "raw_user_prompt.md").write_text(raw_prompt_text, encoding="utf-8")
    if args.clean_prompt_file:
        clean_prompt_path = Path(args.clean_prompt_file).expanduser().resolve()
        prompt_text = clean_prompt_path.read_text(encoding="utf-8")
        intake_notes = ""
        prompt_cleaning = {
            "clean_prompt_changed": prompt_text.strip() != raw_prompt_text.strip(),
            "transformations": ["used_explicit_clean_prompt_file"],
            "clean_prompt_source": str(clean_prompt_path),
        }
    else:
        prompt_text, intake_notes, prompt_cleaning = clean_prompt(raw_prompt_text)
    (original / "user_prompt.md").write_text(prompt_text, encoding="utf-8")
    if intake_notes:
        (audit / "prompt_intake_notes.md").write_text(intake_notes, encoding="utf-8")

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
            "raw_user_prompt": str(audit / "raw_user_prompt.md"),
            "prompt_intake_notes": str(audit / "prompt_intake_notes.md") if (audit / "prompt_intake_notes.md").exists() else None,
            "prompt_cleaning": prompt_cleaning,
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
    first_review_guidance = ""
    if review_id == "r001_review":
        first_review_guidance = """
## First Review Guidance

> For the first review, compare the current deliverables against the original task and materials.
> Focus on concrete places where an agent is likely to fail: missing constraints, wrong assumptions, unsafe shortcuts, weak evidence, shallow reasoning, or hidden senior/domain rules.
> If a weakness depends on an unstated industry rule or senior convention, include a short reason why that rule applies here.
> If anything is unclear, you can ask a question first, then continue filling the comments.

"""
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

{first_review_guidance}## How To Fill This Out

> Review only the current deliverables for this round.
> Strengths are optional and lightweight; weaknesses should be specific enough for the next executor to act on.
> The two scores mean different things: satisfaction is your satisfaction with this current version, while the 1-10 user-relative score uses your own work on this same task as the 5/10 anchor.

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
> This is only about this version, not the whole trace or whether the task is finished.

()/5

## Latest Deliverables Aligns User Scores

> Score the current deliverables on a 1-10 scale, using your own performance on this same task as the 5/10 anchor.
> Put an integer in the parentheses. A 5 means about as good as you personally would produce for this task; above 5 is better than your own likely work, below 5 is worse.

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
    init.add_argument("--clean-prompt-file", default=None)
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
