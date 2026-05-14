---
name: rubric-crystallizer
description: Convert a completed Expert Boost trace and any collected human-reference follow-up notes into objective yes/no evaluation rubrics. Use after expert-boost-loop has produced a trace, preferably after human-reference-collector has captured the user's own solution process, and the user wants to crystallize accepted weaknesses, unresolved expert concerns, hidden senior rules, human-reference insights, and deliverable evidence into at least 15 lettered rubrics, discuss ranking and edits with the user, classify each rubric as fail-fast or make-better, and save both original and curated rubric sets.
---

# Rubric Crystallizer

Use this skill after an `expert-boost-loop` trace exists. In the normal HSW flow, `human-reference-collector` should run first so the user's own solution process can surface additional expert signals before rubric generation. The purpose is to turn the trace and any human-reference follow-up notes into objective benchmark rubrics that catch agent failure modes.

Crystallization is not a summary of what improved from `v0` to `vN`. A rubric may describe a concern that remains unfixed in the final deliverable. The test is whether the point is objective, task-grounded, yes/no evaluable, and useful for identifying agents that would fail this task.

## Core Rules

- Generate at least 15 candidate rubrics before asking the user to rank or prune, unless the trace genuinely lacks enough objective signal.
- Do not ask the user to simply "approve this top 15". The user must be asked to review and order the rubrics, and must be shown the allowed reply format.
- Letter the original candidate rubrics `A`, `B`, `C`, and so on. After `Z`, continue with `AA`, `AB`, etc.
- Write every rubric as a single yes/no question with an objective expected answer.
- Each rubric must test one concrete point. Split multi-condition questions unless the condition is an inseparable basic compliance check.
- Do not require the final deliverable to pass the rubric. Unresolved expert concerns can become strong rubrics.
- Use accepted weaknesses and accepted hidden-rule rationales as the primary signal.
- Use `export/human_reference_rubric_notes_raw.md`, when present, as supplemental expert signal. These notes may produce rubrics only when they satisfy the same objective, task-grounded, yes/no evaluable standard.
- Use adjacent deliverable changes and `v0` versus final comparisons as supporting evidence, not as the main eligibility rule.
- Drop or quarantine subjective, vague, unsupported, or non-evaluable feedback instead of forcing it into a rubric.
- Classify every rubric as `fail_fast` or make-better and explain the classification to the user. Let the user change the type.
- Save the full original generated set and the user-curated set as separate files. Never overwrite the original set after the user begins editing.
- Internal rubric reasoning and canonical stored questions may be English, but any rubric list shown directly to the user must be in the user's language.
- When showing rubrics to the user, show the complete text of every rubric. Do not use abbreviated, summarized, or placeholder forms such as `Does the deliverable ...?`.

## Rubric Types

Use `fail_fast: true` for baseline pass/fail requirements. These are roughly the "60-point line": an agent that fails them has violated core task form, language, format, tooling, safety, or must-have constraints.

Examples:

- The task asks for C++ code and the deliverable is Python.
- The required output file is missing.
- The deliverable ignores a required data source.
- The task prohibits web search but the answer cites unsupported external facts.
- The task requires exactly one artifact and the output creates a different artifact shape.

Use `fail_fast: false` for make-better rubrics. These distinguish stronger agents after basic compliance is met: senior judgment, risk control, concrete coverage, hidden constraints, tradeoffs, and domain-specific quality.

Examples:

- The deliverable distinguishes the buyer's metric from the end user's outcome.
- The plan names a realistic rollback path for the riskiest operational step.
- The analysis identifies a leakage risk implied by the provided dataset.

If uncertain, default to make-better and ask the user whether the point should be a baseline failure.

## Inputs

The usual input is an Expert Boost task package directory with:

```text
task.json
original/user_prompt.md
original/materials/
original/materials_manifest.json
rounds/*/outputs/
rounds/*/manifest.json
reviews/*/review.json
reviews/*/raw_user_input.md
export/human_reference_raw.md
export/human_reference.json
export/human_reference_rubric_notes_raw.md
export/
```

Read only the trace package and explicitly provided supporting material paths. Preserve raw user text exactly when citing source weaknesses or rationales.

## Workflow

### 1. Build A Trace Map

Inspect the package and summarize:

- original task and materials;
- all rounds and output directories;
- accepted weaknesses and quality issues;
- hidden-rule rationales admitted during review;
- human reference summary, if available;
- any extra rubric-signal notes produced after the human reference step;
- final output path;
- any unresolved risks already recorded.

Do not produce rubrics yet if key trace files are missing. Ask for the correct package path.

### 2. Extract Failure Signals

Treat accepted weaknesses as the main source. For each weakness, identify:

- the concrete failure mode;
- the artifact, section, claim, behavior, or omission it targets;
- why it matters to the original task or end user;
- whether it relies on a hidden senior/domain rule;
- whether the signal is objective, subjective, unsupported, too broad, or duplicate.

Also scan for repeated patterns across weaknesses, such as missing risk framing, wrong stakeholder objective, unsafe data handling, weak evidence checks, or failure to clarify ambiguity.

Then read `export/human_reference_rubric_notes_raw.md` if it exists. Treat it like expert feedback produced after the user mentally solved the task themselves:

- identify any new agent failure, likely misunderstanding, should-do point, or hidden requirement;
- check whether the point is grounded in the original task, materials, accepted review context, or the human reference solution process;
- convert it into candidate rubrics only if it can become objective yes/no evaluation;
- quarantine points that are subjective, too broad, unsupported, or merely process narration.

Do not force every human-reference note into a rubric.

### 3. Use Deliverables As Evidence

Use deliverables in two supporting ways:

- Compare `v{i-1}` to `v{i}` to locate how a weakness manifested and whether a later output addressed it.
- Compare `v0` to the final output to discover discriminative candidate rubrics and evidence spans.

These comparisons help with evidence and wording. They are not required for eligibility. A rubric may remain valid when all versions fail it, if the expert concern is objective and task-grounded.

### 4. Draft Candidate Rubrics

Generate at least 15 candidate rubrics. Prefer 15-25 if there is enough signal.

Each candidate should have this rich internal shape:

```json
{
  "id": "A",
  "rank": null,
  "question": "Does the deliverable identify the specific customer segment affected by the pricing change?",
  "display_question": "交付物是否识别了受定价变化影响的具体客户群体？",
  "expected": true,
  "fail_fast": false,
  "type_rationale": "Make-better because ...",
  "source_weaknesses": ["r001_review: weakness 2"],
  "source_evidence": {
    "prompt_or_materials": [],
    "reviews": [],
    "human_reference": [],
    "deliverables": []
  },
  "v0_status": "fail|pass|unclear|not_checked",
  "final_status": "fail|pass|unclear|not_checked",
  "judge_guidance": "What an evaluator should look for.",
  "reject_if": "Boundary conditions that should not count as a pass.",
  "status": "candidate"
}
```

Use `question` for the canonical machine-readable yes/no question. It may be English. Use `display_question` for the full user-facing version in the user's language. If the user's language is English, `display_question` may equal `question`.

Use `expected: true` for most positive rubrics. Use `expected: false` for prohibited behavior, such as "Does the deliverable claim that X alone solves Y?".

### 5. Quality Gate

Reject, revise, or ask the user before accepting any candidate that:

- bundles multiple unrelated checks;
- asks whether the answer is "good", "deep", "professional", or "comprehensive";
- requires private intent or process knowledge to judge;
- depends on unsupported external facts;
- contradicts the original prompt or materials;
- rewards verbosity rather than a concrete correct result;
- cannot be answered yes/no from the output and task materials.

Do not hide rejected signals. Summarize them separately as `not_crystallized` with the reason.

### 6. Present For User Ranking

Show the user the complete candidate list in lettered form. Use the user's language for every displayed rubric question, even if the stored canonical `question` is English. Do not collapse, shorten, summarize, or show only a sample of the rubric list.

```text
A: 交付物是否识别了受定价变化影响的具体客户群体？ [make-better]
B: 交付物是否包含题目要求的唯一输出文件路径？ [fail-fast]
C: 交付物是否明确指出了最高风险操作步骤的回滚或缓解方案？ [make-better]
```

Then ask the user to reorder, edit, delete, or add rubrics. Make the expected reply format explicit. Tell the user to list rubrics in their preferred order, one per line, and to include any edits/deletions/additions/type changes in the same message. The user may reply like:

```text
C: 交付物是否明确指出了最高风险操作步骤的回滚或缓解方案？
B: 交付物是否包含题目要求的唯一输出文件路径？
A: 交付物是否识别了受定价变化影响的具体客户群体？
D: <完整 rubric 文本>
Remove F
Change C to: <完整修改后的 rubric 文本>
Add: <完整新增 rubric 文本>
Type B: make-better
Type H: fail-fast
```

If the user responds only with "approved", "looks good", "批准", "批准这个 top15", or similar without ranking or explicit confirmation of the current full order, do not finalize curated rubrics yet. Ask them to either provide the ordered list or explicitly say that the displayed full order should be used as-is after reviewing it.

When discussing edits, protect objective yes/no judgeability. If the user proposes a subjective rubric, help tighten it into an observable question.

### 7. Save Original And Curated Sets

After the first candidate set is generated, save:

```text
export/rubrics_original.json
export/rubrics_original.md
```

After the user provides an ordered review response or explicitly confirms that the displayed full order should be used as-is, and after any edits, deletions, additions, and fail-fast labels are resolved, save:

```text
export/rubrics_curated.json
export/rubrics_curated.md
```

Use the helper when useful:

```bash
python3 ~/.codex/skills/rubric-crystallizer/scripts/rubric_store.py validate --file <rubrics_curated.json> --min-active 15
python3 ~/.codex/skills/rubric-crystallizer/scripts/rubric_store.py markdown --file <rubrics_curated.json> --out <rubrics_curated.md> --title <title-in-user-language> --rank-label <rank-label-in-user-language> --deleted-title <deleted-section-title-in-user-language>
python3 ~/.codex/skills/rubric-crystallizer/scripts/rubric_store.py bench-rubrics --file <rubrics_curated.json> --out <rubrics.json> --limit 15
```

The original file should preserve every first-pass candidate. The curated file should preserve user edits, ranking, deletions, additions, canonical questions, and user-language `display_question` values. Deleted rubrics may remain in curated JSON with `status: "deleted_by_user"` but must not be exported to the final bench `rubrics.json`.

## User-Facing Style

Be collaborative and editorial. The user is the domain expert; Codex is the crystallization assistant.

Keep the first presentation structured but complete: show every generated rubric with its letter, full user-language question, and type label, then invite ranking and edits. Save detailed evidence in files rather than flooding the chat.

When the user changes ranking or type labels, accept domain judgment unless it breaks objective evaluation. If it does break evaluation, explain the issue and offer a tighter wording.

## Handoff To Builder

When the curated rubrics have been ranked/reviewed and saved, tell the user that `starbench-hsw-builder` can do final packaging if `export/human_reference.json` already exists. If the human reference file is missing, use `human-reference-collector` before packaging.

The final bench package uses only the top 15 active curated rubrics, preserving the user's ranked order. It must match the demo task schema:

```text
task.json
prompt.md
rubrics.json
human_reference.json
```

The final `rubrics.json` contains only:

```json
{
  "rubrics": [
    {
      "id": "A",
      "fail_fast": false,
      "expected": true,
      "question": "Does the deliverable ...?"
    }
  ]
}
```
