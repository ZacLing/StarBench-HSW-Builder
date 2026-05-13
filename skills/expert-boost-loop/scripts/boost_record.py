#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
            "rounds": [],
            "reviews": [],
        },
    )
    print(str(run))


def next_review_id(state: dict[str, Any]) -> str:
    index = int(state.get("next_review_index") or 1)
    return f"r{index:03d}_review"


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

    record = {
        "review_id": review_id,
        "created_at": utc_now(),
        "round_under_review": args.round_under_review,
        "raw_text": raw_text,
        "strengths": [],
        "weaknesses": [],
        "scores": {},
        "notes": "",
    }
    write_json(review_dir / "review.json", record)

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
    review.set_defaults(func=cmd_record_review)

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
