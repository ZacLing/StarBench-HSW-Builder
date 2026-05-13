---
name: expert-boost-loop
description: StarBoost-style expert-in-the-loop iteration for Codex conversations. Use when a user provides an initial task prompt and materials, wants Codex to create a complete output package, then repeatedly records human strengths and weaknesses verbatim and regenerates full improved packages using only the weaknesses as revision targets with an auditable local history.
---

# Expert Boost Loop

Use this skill to run a lightweight StarBoost-style improvement harness inside a Codex conversation.

## Core Rules

- Save the user's original task prompt exactly before acting on it.
- Save every review-like user message exactly before interpreting it.
- Produce complete output packages for every round, never only patches.
- Feed only the latest parsed weaknesses into the next revision round.
- Do not feed strengths, scores, hidden notes, private reasoning, rubrics, or inferred references into the next round.
- Preserve previous outputs for inspection, but write a full replacement package each boosted round.
- Continue until the user provides no weaknesses, says the output is acceptable, or explicitly asks to finish.

## Storage

Default run root:

```text
.codex-starboost/<task_slug>/
```

Use the current workspace unless the user requests another location. Keep this structure:

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

## Starting A Task

When the user gives the initial task and materials:

1. Choose a short filesystem-safe `task_slug`.
2. Save the initial user prompt verbatim. Prefer:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py init --slug <task_slug> --prompt-file <verbatim_prompt_file> --material <path> ...
```

If the prompt is only in chat, create a temporary file containing the exact text first, then run `init`.

3. Copy or reference user-provided material paths under `original/materials/` when possible.
4. Create `rounds/v000_cold_start/prompt.md` with the cold-start prompt below.
5. Produce the full deliverable package under `rounds/v000_cold_start/outputs/`.
6. Write `rounds/v000_cold_start/final.md` with a concise completion note and output paths.
7. Run:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py manifest --run .codex-starboost/<task_slug> --round v000_cold_start --stage cold_start
```

8. Ask the user for strengths and weaknesses of the latest output.

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
  .codex-starboost/<task_slug>/rounds/v000_cold_start/outputs/
- Do not produce a draft unless the user asked for a draft.
- Do not mention this harness in the deliverable unless the user asked for process notes.
```

## Recording A Review

When the user provides strengths, weaknesses, scores, comments, or any review-like feedback:

1. Before interpreting the message, save it verbatim:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py record-review --run .codex-starboost/<task_slug> --round-under-review <latest_round_id> --raw-file <verbatim_review_file>
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
5. Produce a complete replacement deliverable package under:

```text
rounds/<new_round>/outputs/
```

6. Write `final.md`, run `boost_record.py manifest`, update `task.json`, and ask for the next review.

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

- After first output: report the output path and ask for strengths and weaknesses.
- After each review: say the review was recorded, then create the next complete package.
- After termination: report the final output path and export summary path.

Do not claim files were recorded unless they exist.
