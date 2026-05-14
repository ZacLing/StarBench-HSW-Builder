---
name: expert-boost-loop
description: StarBoost-style expert-in-the-loop iteration for Codex conversations with an explicit user-chosen task package location and a fresh isolated executor subagent for every output round. Use when a user provides an initial task prompt and materials, wants Codex to create a complete output package, then repeatedly records human strengths and weaknesses verbatim and regenerates full improved packages using only the weaknesses as revision targets with an auditable local history.
---

# Expert Boost Loop

Use this skill to run a lightweight StarBoost-style improvement harness inside a Codex conversation.

## Core Rules

- Decide the task package location before initializing a run.
- Main Codex orchestrates the run; a fresh executor subagent produces each cold-start or boosted output package.
- Save the user's original task prompt exactly before acting on it.
- Save every review-like user message exactly before interpreting it.
- Produce complete output packages for every round, never only patches.
- Feed only the latest parsed weaknesses into the next revision round.
- Do not feed strengths, scores, hidden notes, private reasoning, rubrics, or inferred references into the next round.
- Preserve previous outputs for inspection, but write a full replacement package each boosted round.
- Continue until the user provides no weaknesses, says the output is acceptable, or explicitly asks to finish.

## Executor Agent Architecture

Use a separate executor subagent for every production round. The executor is the only agent that should create the substantive deliverable artifacts for cold start and boosted rounds. Main Codex remains the host and record keeper.

Main Codex responsibilities:

- Save the original task, reviews, prompts, weaknesses, manifests, and summaries.
- Decide exactly what the executor may see.
- Create the round prompt file before launching the executor.
- Launch one fresh executor per round.
- Verify the executor wrote a complete package under the target `outputs/` directory.
- Inspect outputs for existence, completeness, and obvious file-placement errors, but do not substantially improve the deliverable locally in place of the executor.
- Write the round `final.md`, run `boost_record.py manifest`, update state, ask the user for the next review, and close the executor.

Executor requirements:

- Use a fresh subagent for every round; do not reuse an executor across rounds.
- Use `agent_type="worker"`, `model="gpt-5.5"`, and `reasoning_effort="high"` when the environment supports those controls.
- Do not fork the current conversation context into the executor. Use `fork_context=false` or the closest available equivalent.
- Give the executor only the round prompt text and explicit filesystem paths it needs.
- Instruct the executor to inspect only the task package and provided material paths. This is not a hard sandbox, so state the boundary plainly in the executor prompt.
- Instruct the executor that it is not alone in the workspace, must not revert unrelated edits, and must write only inside the target round `outputs/` directory unless the prompt explicitly names other allowed write paths.
- Close the executor after the round is complete.

If fresh executor subagents are unavailable, do not silently produce the deliverable locally. Tell the user that this trace workflow requires a fresh executor agent for each round and ask whether to pause or run a degraded local fallback.

### Executor Lifecycle

Use this lifecycle for every cold-start or boosted round:

1. Main Codex writes the round prompt and any round input files first.
2. Main Codex spawns exactly one fresh executor for the round with no forked context.
3. Main Codex waits for the executor to finish the deliverable package.
4. If the executor succeeds, Main Codex closes that executor before moving to manifest/review steps.
5. If the executor fails, stalls, writes outside the allowed location, or exposes that it is relying on unavailable context, Main Codex closes it and starts a new fresh executor for the same round. The retry prompt may mention only concrete filesystem facts such as missing files or wrong output location.
6. If the executor needs a user clarification, Main Codex pauses, asks the user, records any review-like response when applicable, then starts a fresh executor with the minimal clarified task package context.

Never carry an executor from one round into another. Never let multiple executors write the same round outputs concurrently.

Use this executor launch pattern:

```text
Spawn a fresh worker executor with:
- fork_context: false
- model: gpt-5.5
- reasoning_effort: high

Give it:
- The round prompt from <task_package_dir>/rounds/<round_id>/prompt.md
- The allowed read paths
- The exact output directory
- The instruction to write a complete deliverable package under that output directory
```

## Storage

The task package is the run root directory that contains `task.json`, `original/`, `rounds/`, `reviews/`, and `export/`.

Strongly recommend that the user choose this location before the run starts so they can find the package later. The user may provide either:

- An exact task package directory, such as `/path/to/my-hsw-task-package`.
- A parent directory plus a task name; create `<parent>/<task_slug>/`.

If the user does not provide a location, ask once before initialization:

```text
Where should I save this task package? I strongly recommend choosing a stable folder now so the trace is easy to find later. You can give me an exact directory, or say "you decide" and I will create one in the current workspace.
```

If the user still asks Codex to decide, use the current workspace default:

```text
.codex-starboost/<task_slug>/
```

Keep this structure inside the chosen task package:

```text
task.json
original/user_prompt.md
original/materials/
original/materials_manifest.json
rounds/v000_cold_start/
  prompt.md
  outputs/
  final.md
  manifest.json
reviews/r001_review/
  raw_user_input.md
  review.json
export/
  run_summary.json
  run_summary.md
```

Use `scripts/boost_record.py` for deterministic initialization, review recording, and manifests.

When the user provides an exact package directory, initialize with:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py init --run <task_package_dir> --prompt-file <verbatim_prompt_file> --material <path> ...
```

When using a parent directory plus slug, initialize with:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py init --base <parent_dir> --slug <task_slug> --prompt-file <verbatim_prompt_file> --material <path> ...
```

## Starting A Task

When the user gives the initial task and materials:

1. Resolve the task package location:
   - If the user already gave an exact location, use it.
   - If the user gave only a parent folder or project folder, choose a short filesystem-safe `task_slug` and create the package under that parent.
   - If no location was provided, ask once using the Storage prompt above.
   - If the user says Codex should decide, choose `.codex-starboost/<task_slug>/` in the current workspace.
2. Choose a short filesystem-safe `task_slug` when needed.
3. Save the initial user prompt verbatim. Prefer one of:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py init --run <task_package_dir> --prompt-file <verbatim_prompt_file> --material <path> ...
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py init --base <parent_dir> --slug <task_slug> --prompt-file <verbatim_prompt_file> --material <path> ...
```

If the prompt is only in chat, create a temporary file containing the exact text first, then run `init`.

4. Copy or reference user-provided material paths under `original/materials/` when possible.
5. Create `rounds/v000_cold_start/prompt.md` with the cold-start prompt below.
6. Launch a fresh executor subagent using the Executor Agent Architecture. The executor produces the full deliverable package under `rounds/v000_cold_start/outputs/`.
7. After the executor finishes, close it and verify that `outputs/` contains the expected complete package.
8. Write `rounds/v000_cold_start/final.md` with a concise completion note and output paths.
9. Run:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py manifest --run <task_package_dir> --round v000_cold_start --stage cold_start
```

10. Ask the user for strengths and weaknesses of the latest output.

## Cold-Start Prompt

Use this pattern internally for `rounds/v000_cold_start/prompt.md`:

```text
You are producing the first complete deliverable package for the user's task.

Original user prompt:
<verbatim original prompt>

Available materials:
<list material paths>

Instructions:
- Use only the original prompt and provided materials.
- Produce a complete, polished deliverable package.
- Save all final deliverables under:
  <task_package_dir>/rounds/v000_cold_start/outputs/
- You are a fresh executor agent. You do not have the host conversation context.
- Inspect only the task package paths and material paths listed here. Do not browse the wider workspace.
- You are not alone in the workspace; do not revert unrelated edits or modify files outside the target output directory.
- Do not produce a draft unless the user asked for a draft.
- Do not mention this harness in the deliverable unless the user asked for process notes.
```

## Recording A Review

When the user provides strengths, weaknesses, scores, comments, or any review-like feedback:

1. Before interpreting the message, save it verbatim:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py record-review --run <task_package_dir> --round-under-review <latest_round_id> --raw-file <verbatim_review_file>
```

2. Parse strengths and weaknesses conservatively from the raw text.
3. Update `review.json` with parsed `strengths`, `weaknesses`, `scores`, and `notes` while keeping `raw_text` unchanged.
4. If weaknesses are ambiguous, preserve the raw review first, then ask a concise clarification.

Never summarize instead of saving the raw user review.

## Boosted Round

If the review contains one or more weaknesses:

1. Create the next round id: `v001_boosted`, `v002_boosted`, and so on.
2. Copy the previous round outputs into:

```text
rounds/<new_round>/inputs/previous_outputs/
```

3. Write only the parsed weaknesses to:

```text
rounds/<new_round>/inputs/review_weaknesses.md
```

4. Create `rounds/<new_round>/prompt.md` with the boosted prompt below.
5. Launch a fresh executor subagent using the Executor Agent Architecture. The executor produces a complete replacement deliverable package under:

```text
rounds/<new_round>/outputs/
```

6. After the executor finishes, close it and verify that `outputs/` contains a complete replacement package.
7. Write `final.md`, run `boost_record.py manifest`, update `task.json`, and ask for the next review.

## Boosted Prompt

Use this pattern internally:

```text
You are working on a StarBoost-style revision round.

Your job is to produce a polished, complete replacement deliverable package for the original user task.

Original user prompt:
<verbatim original prompt>

Previous deliverables are available at:
<previous outputs path>

Latest expert weaknesses:
<bullet list from review_weaknesses.md>

Instructions:
- Treat the original prompt as the task you still need to satisfy.
- Use the latest weaknesses as required revision targets.
- You are a fresh executor agent. You do not have the host conversation context.
- Inspect only the task package paths, previous output path, and material paths listed here. Do not browse the wider workspace.
- You are not alone in the workspace; do not revert unrelated edits or modify files outside the target output directory.
- Do not answer the reviewer.
- Do not write a change log unless the original task asks for one.
- Do not mention weaknesses, review, feedback, previous versions, or this harness in the deliverable.
- Preserve correct useful work from the previous deliverable.
- Fix the substantive issues behind the weaknesses.
- Produce a complete replacement package, not a patch.
- Save all final deliverables under the current round's outputs directory.
```

## Termination

If the user provides no weaknesses, says the output is acceptable, or asks to finish:

1. Record the final review verbatim first.
2. Set `task.json.status` to `terminated`.
3. Write `export/run_summary.json` and `export/run_summary.md`.
4. Include original task path, round ids, review ids, final outputs path, and unresolved risks if any.

## User-Facing Replies

Keep replies compact:

- After first output: report the task package path, output path, and ask for strengths and weaknesses.
- After each review: say the review was recorded, then create the next complete package.
- After termination: report the task package path, final output path, and export summary path.

Do not claim files were recorded unless they exist.
