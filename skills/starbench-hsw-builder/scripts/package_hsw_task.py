#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


TASK_KEYS = [
    "id",
    "name",
    "prompt",
    "rubrics",
    "human_reference",
    "timeout_seconds",
    "allow_web_search",
]
TASK_KEYS_WITH_MATERIALS = [
    "id",
    "name",
    "prompt",
    "rubrics",
    "human_reference",
    "materials",
    "timeout_seconds",
    "allow_web_search",
]
RUBRIC_KEYS = ["id", "fail_fast", "expected", "question"]
HUMAN_STEP_KEYS = ["step_id", "step_type", "instruction", "reasoning"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def rank_key(item: dict[str, Any]) -> tuple[int, int, str]:
    rank = item.get("rank")
    if isinstance(rank, int):
        return (0, rank, str(item.get("id") or ""))
    if isinstance(rank, str) and rank.isdigit():
        return (0, int(rank), str(item.get("id") or ""))
    return (1, 10**9, str(item.get("id") or ""))


def active_curated_rubrics(path: Path, limit: int) -> list[dict[str, Any]]:
    data = read_json(path)
    rubrics = data.get("rubrics")
    if not isinstance(rubrics, list):
        raise SystemExit(f"{path} must contain a top-level `rubrics` list")
    active = []
    for item in rubrics:
        if not isinstance(item, dict):
            raise SystemExit("each curated rubric must be an object")
        status = str(item.get("status") or "candidate")
        if status in {"deleted_by_user", "rejected", "not_crystallized"}:
            continue
        active.append(item)
    active = sorted(active, key=rank_key)
    if len(active) < limit:
        raise SystemExit(f"need at least {limit} active curated rubrics, found {len(active)}")
    return active[:limit]


def bench_rubrics(curated_path: Path, limit: int) -> dict[str, Any]:
    selected = active_curated_rubrics(curated_path, limit)
    rubrics = []
    for item in selected:
        bench_item = {
            "id": str(item.get("id") or "").strip(),
            "fail_fast": item.get("fail_fast"),
            "expected": item.get("expected"),
            "question": str(item.get("question") or "").strip(),
        }
        if list(bench_item.keys()) != RUBRIC_KEYS:
            raise SystemExit("internal rubric key order mismatch")
        if not bench_item["id"]:
            raise SystemExit("rubric id must be non-empty")
        if not isinstance(bench_item["fail_fast"], bool):
            raise SystemExit(f"rubric {bench_item['id']} fail_fast must be boolean")
        if not isinstance(bench_item["expected"], bool):
            raise SystemExit(f"rubric {bench_item['id']} expected must be boolean")
        if not bench_item["question"].endswith("?"):
            raise SystemExit(f"rubric {bench_item['id']} question must end with `?`")
        rubrics.append(bench_item)
    return {"rubrics": rubrics}


def validate_human_reference(path: Path) -> dict[str, Any]:
    data = read_json(path)
    steps = data.get("steps")
    if set(data.keys()) != {"steps"} or not isinstance(steps, list) or not steps:
        raise SystemExit("human_reference.json must contain only a non-empty `steps` list")
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise SystemExit("each human reference step must be an object")
        if list(step.keys()) != HUMAN_STEP_KEYS:
            raise SystemExit(
                f"human_reference step {index} keys must be exactly: {', '.join(HUMAN_STEP_KEYS)}"
            )
        for key in HUMAN_STEP_KEYS:
            if not isinstance(step[key], str) or not step[key].strip():
                raise SystemExit(f"human_reference step {index}.{key} must be a non-empty string")
    return data


def copy_task_materials(materials_src: Path, task_dir: Path) -> list[str]:
    if not materials_src.exists():
        return []
    if not materials_src.is_dir():
        raise SystemExit(f"materials path must be a directory: {materials_src}")
    materials_dest = task_dir / "materials"
    if materials_dest.exists():
        shutil.rmtree(materials_dest)
    shutil.copytree(
        materials_src,
        materials_dest,
        ignore=lambda _dir, names: {name for name in names if name == ".DS_Store"},
    )
    files = []
    for path in sorted(item for item in materials_dest.rglob("*") if item.is_file()):
        files.append(path.relative_to(task_dir).as_posix())
    return files


def copy_trace(run: Path, trace_dir: Path, out_root: Path) -> None:
    trace_dir.mkdir(parents=True, exist_ok=True)
    for name in ("task.json",):
        src = run / name
        if src.exists():
            shutil.copy2(src, trace_dir / name)
    for name in ("audit", "original", "rounds", "reviews"):
        src = run / name
        if src.exists():
            shutil.copytree(src, trace_dir / name)
    export_src = run / "export"
    if export_src.exists():
        def ignore_export(_dir: str, names: list[str]) -> set[str]:
            return {
                name
                for name in names
                if name == out_root.name
                or name.startswith("final_package")
                or name.endswith("_hsw_package")
                or name.endswith(".zip")
            }

        shutil.copytree(export_src, trace_dir / "export", ignore=ignore_export)


def make_zip(root: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(root).as_posix())


def cmd_package(args: argparse.Namespace) -> None:
    run = Path(args.run).expanduser().resolve()
    if not (run / "task.json").exists():
        raise SystemExit(f"not an Expert Boost run package: {run}")

    curated = Path(args.curated_rubrics).expanduser().resolve() if args.curated_rubrics else run / "export" / "rubrics_curated.json"
    human_ref = Path(args.human_reference).expanduser().resolve() if args.human_reference else run / "export" / "human_reference.json"
    prompt_src = Path(args.prompt_file).expanduser().resolve() if args.prompt_file else run / "original" / "user_prompt.md"
    materials_src = Path(args.materials_dir).expanduser().resolve() if args.materials_dir else run / "original" / "materials"
    if not curated.exists():
        raise SystemExit(f"missing curated rubrics: {curated}")
    if not human_ref.exists():
        raise SystemExit(f"missing human reference: {human_ref}")
    if not prompt_src.exists():
        raise SystemExit(f"missing prompt file: {prompt_src}")

    task_id = args.task_id
    name = args.name
    out_root = Path(args.out_dir).expanduser().resolve() if args.out_dir else run / "export" / "final_package"
    if out_root.exists():
        shutil.rmtree(out_root)
    trace_dir = out_root / "trace"
    task_dir = out_root / "task_package"
    task_dir.mkdir(parents=True, exist_ok=True)

    copy_trace(run, trace_dir, out_root)
    shutil.copy2(prompt_src, task_dir / "prompt.md")
    materials = copy_task_materials(materials_src, task_dir)
    write_json(task_dir / "rubrics.json", bench_rubrics(curated, int(args.limit)))
    write_json(task_dir / "human_reference.json", validate_human_reference(human_ref))
    task = {
        "id": task_id,
        "name": name,
        "prompt": "prompt.md",
        "rubrics": "rubrics.json",
        "human_reference": "human_reference.json",
    }
    if materials:
        task["materials"] = materials
    task["timeout_seconds"] = int(args.timeout_seconds)
    task["allow_web_search"] = bool(args.allow_web_search)
    expected_task_keys = TASK_KEYS_WITH_MATERIALS if materials else TASK_KEYS
    if list(task.keys()) != expected_task_keys:
        raise SystemExit("internal task key order mismatch")
    write_json(task_dir / "task.json", task)

    zip_path = Path(args.zip).expanduser().resolve() if args.zip else run / "export" / f"{task_id}_hsw_package.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    make_zip(out_root, zip_path)
    print(str(zip_path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="package_hsw_task.py")
    sub = parser.add_subparsers(dest="command", required=True)

    package = sub.add_parser("package")
    package.add_argument("--run", required=True, help="Expert Boost task package root.")
    package.add_argument("--task-id", required=True)
    package.add_argument("--name", required=True)
    package.add_argument("--curated-rubrics", default=None)
    package.add_argument("--human-reference", default=None)
    package.add_argument("--prompt-file", default=None)
    package.add_argument("--materials-dir", default=None)
    package.add_argument("--timeout-seconds", type=int, default=1800)
    package.add_argument("--allow-web-search", type=parse_bool, default=True)
    package.add_argument("--limit", type=int, default=15)
    package.add_argument("--out-dir", default=None)
    package.add_argument("--zip", default=None)
    package.set_defaults(func=cmd_package)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
