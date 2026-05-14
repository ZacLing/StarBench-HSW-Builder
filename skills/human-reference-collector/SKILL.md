---
name: human-reference-collector
description: Collect, preserve, structure, judge, and save human reference solution steps after rubrics have been curated and before final StarBench-HSW packaging. Use when a completed Expert Boost trace already has curated rubrics and the project needs the user's own step-by-step solution process converted into an OpenAI-bench-compatible `human_reference.json`, while also saving the raw user explanation into the trace.
---

# Human Reference Collector

## Purpose

Use this skill after `rubric-crystallizer` has saved curated rubrics and before `starbench-hsw-builder` creates the final zip.

The goal is to collect how the human expert would solve the task themselves, preserve that raw explanation, then convert it into a structured `human_reference.json` that matches the benchmark task package schema.

This is not another rubric workflow. It is a human solution process workflow.

The collection posture matters: guide the expert to mentally replay how they would solve the task if they were doing it themselves. The raw answer should preserve rich details; the later structured `instruction` fields should become abstract.

## Core Rules

- Ask the user for their own step-by-step solution process for the task.
- Encourage detailed reconstruction of the user's actual thinking and solving process, but do not make collection overly strict. The user may write natural prose, bullets, or numbered steps.
- Show a simple answer format example such as `步骤1: ... / 步骤2: ... / 步骤n: ...` so the user knows how to respond.
- The user does not need to write `instruction`, `reasoning`, or `step_type`.
- Preserve the raw user text exactly in the trace before restructuring it.
- Treat raw detail as valuable: concrete evidence, intermediate conclusions, decision rules, false starts, checks, and expert assumptions should remain in `human_reference_raw.md` and later appear in `reasoning` when relevant.
- Use an English internal structuring prompt, but communicate with the user and write user-visible content in the user's language unless the user requested another language.
- Produce `human_reference.json` with exactly `steps`, where each step has `step_id`, `step_type`, `instruction`, and `reasoning`.
- `step_type` is a concise summarized label for the step. It is not limited to a fixed taxonomy.
- Run one independent judge pass using `human-reference-judge` in a fresh no-context subagent when subagents are available.
- Revise once from judge feedback, then save the final reference.
- Do not package the final zip here. Hand off to `starbench-hsw-builder` after saving `export/human_reference.json`.
- Do not interrupt the user-facing collection prompt to explain that curated rubrics are missing. If `export/rubrics_curated.json` is missing, still collect and save raw human reference and draft/final `human_reference` files; note internally that independent judge context or final packaging may be completed after rubrics are available.

## Files

Use the Expert Boost run root as the working directory. Save:

```text
export/human_reference_raw.md
export/human_reference_draft.json
export/human_reference_judge.json
export/human_reference_revision_notes.md
export/human_reference.json
export/human_reference.md
```

`human_reference_raw.md` is trace evidence. It may be copied into final zip `trace/export/`, but it must not be referenced by `task_package/task.json`.

`human_reference.json` is the benchmark file that `starbench-hsw-builder` copies into `task_package/human_reference.json`.

## Expert Elicitation

Do not only ask "what are the steps?" Help the expert remember the real solving process.

Useful prompts:

- "If you were doing this yourself, what would you look at first?"
- "What detail in the prompt or materials would you treat as controlling?"
- "What would you check before committing to the answer?"
- "Where would a junior or agent likely jump too fast?"
- "What intermediate conclusion would you need before moving on?"
- "Which industry rule, hidden convention, or personal expert habit would you apply here?"
- "What would make you revise or reject an early direction?"

Ask for detail in the raw collection, then abstract later. The user should feel invited to write the messy expert path: observations, checks, material references, judgment calls, intermediate conclusions, and why each next step follows.

Do not ask the user to make `instruction` abstract. That is the collector's job during structuring.

## Collection Prompt

Ask in the user's language. Chinese style:

```text
接下来需要收集 human reference：也就是如果你自己来解决这个 task，你会如何一步步完成。

请尽量把自己代入真实工作状态：如果是你亲自做，你会先看什么、抓住哪些材料或信息、做什么判断、怎么推导、得到哪些中间结论、如何检查方向是否对、然后为什么进入下一步。

不用管 instruction、step_type 或 JSON 格式，也不用写得特别规整。请尽量按 step-by-step 还原你的真实解题过程，越详细越好。这里宁可写细一点：包括你会参考的材料位置、隐含判断、行业规则、容易出错的地方、你会如何排除错误方向，以及每一步得到的中间结论。

如果某些步骤依赖行业经验、隐含规则、材料里的具体信息，也请直接写出来。你可以自己分 step；如果分得不完美也没关系，我后面会自动整理，并把最终 instruction 抽象化。

你可以直接按这个形式写：

步骤1: ...
步骤2: ...
步骤3: ...
...
步骤n: ...
```

English style:

```text
Next I need to collect the human reference: how you personally would solve this task step by step.

Please mentally replay the real work process. If you were solving this yourself, what would you inspect first, what material or information would control the answer, what judgment would you apply, what intermediate conclusions would you reach, how would you check whether the direction is right, and why would you move to the next step?

You do not need to write `instruction`, `step_type`, or JSON. It also does not need to be perfectly formatted. Please reconstruct your real solution process in as much step-by-step detail as possible. More detail is better here: include material references, hidden judgments, industry rules, likely error traps, how you would rule out wrong directions, and the concrete intermediate conclusion from each step.

If a step depends on industry experience, hidden rules, or specific information from the materials, include that directly. You can split the steps yourself; if the split is imperfect, I will structure it afterward and make the final instructions abstract.

You can write in this format:

Step 1: ...
Step 2: ...
Step 3: ...
...
Step n: ...
```

If the user gives a very short answer, ask once for more detail unless they clearly want to proceed. When asking, name the missing detail type, such as source details, intermediate conclusions, checks, hidden rules, or decision criteria.

Save the raw answer before restructuring it. Use the helper when convenient:

```bash
python3 ~/.codex/skills/human-reference-collector/scripts/human_reference_store.py save-raw --run <run> --text-file <raw-answer.md>
```

If using stdin instead of a file, omit `--text-file`.

## Structuring Method

After saving the raw user text, transform it into a draft structured reference using this English internal prompt. Adapt only the output language, not the method:

```text
You are a senior data annotation specialist. Convert the user's human solution process into a structured `steps` array for a benchmark human reference.

Follow these step-level principles:

1. A step is a minimal key reasoning unit on the shortest credible solution path.
2. Split by newly introduced core bottlenecks. Prefer 6-12 steps when the task has enough substance, but do not force the count if the task is much simpler or more complex.
3. Each step must contain:
   - `instruction`: abstract guidance only. It must describe what to do, not the specific answer, value, named source result, intermediate result, or final conclusion. It should be reusable guidance for a solver.
   - `reasoning`: concrete reasoning. It must preserve the user's useful details: what information is used, how it is used, what expert judgment or check is applied, and what specific intermediate conclusion is reached.
   - `step_type`: a concise summary label for the nature of the step. Use a short word or phrase derived from the actual step, not a fixed taxonomy.

Important:
- Preserve raw expert detail in `reasoning`, not `instruction`.
- If the raw user explanation contains concrete values, material facts, conclusions, examples, hidden rules, or error checks, keep them in `reasoning` when relevant.
- If one user-written step mixes multiple bottlenecks, split it.
- If one step both applies a domain rule and performs extraction/calculation, split those into separate reasoning units when that improves clarity.
- Do not invent solving steps that are not supported by the user's raw process, the prompt, or the provided materials.
- Keep the final JSON compatible with:
  {
    "steps": [
      {
        "step_id": "H001",
        "step_type": "...",
        "instruction": "...",
        "reasoning": "..."
      }
    ]
  }
- Use the user's language for `instruction`, `reasoning`, and `step_type` unless the user requested another language.
- Output complete JSON only.
```

## Step Quality

Good `instruction`:

- abstract;
- reusable as guidance;
- does not reveal the concrete answer;
- does not include exact values, named material facts, named intermediate conclusions, or final results;
- may name the kind of operation, such as identify, compare, verify, calculate, prioritize, map, filter, synthesize, or decide.

Good `reasoning`:

- names the task information, materials, expert rule, or output evidence being used;
- explains how the human derives the conclusion;
- includes concrete intermediate conclusions;
- preserves useful raw details from the expert's explanation;
- is detailed enough for a reviewer to understand the expert's path.

Good `step_type`:

- is a concise label, such as `source_alignment`, `domain_rule`, `evidence_extraction`, `risk_check`, `calculation`, `structure_planning`, or an equivalent label in the user's language;
- summarizes the step after reading it;
- is not limited to any three-category taxonomy.

## Independent Judge Pass

After creating `export/human_reference_draft.json`, spawn one fresh independent judge subagent when available.

If `export/rubrics_curated.json` is missing, do not complain to the user during collection. Either omit that input from the judge prompt or skip the judge pass with a note in `export/human_reference_revision_notes.md`. The priority is to preserve the user's raw human reference while it is available.

Use:

```text
agent_type: worker
fork_context: false
```

Do not pass the current conversation. Give only:

- the path to `skills/human-reference-judge/SKILL.md`;
- the Expert Boost run root;
- `original/user_prompt.md`;
- `original/materials_manifest.json`;
- `original/materials/` if present;
- `export/rubrics_curated.json`;
- `export/human_reference_raw.md`;
- `export/human_reference_draft.json`;
- the desired output language.

Ask the judge to write feedback as JSON and not to rewrite the full final human reference unless a correction is necessary to explain a point. Save its output to:

```text
export/human_reference_judge.json
```

Use the feedback for exactly one revision pass. Save a concise note of what changed in:

```text
export/human_reference_revision_notes.md
```

If subagents are unavailable, do a local self-check, save the notes, and explicitly record that judge review was skipped.

## Final Save

Use the helper for schema normalization and validation:

```bash
python3 ~/.codex/skills/human-reference-collector/scripts/human_reference_store.py normalize --draft <draft.json> --out <run>/export/human_reference.json
python3 ~/.codex/skills/human-reference-collector/scripts/human_reference_store.py markdown --file <run>/export/human_reference.json --out <run>/export/human_reference.md
python3 ~/.codex/skills/human-reference-collector/scripts/human_reference_store.py validate --file <run>/export/human_reference.json
```

The final JSON must be:

```json
{
  "steps": [
    {
      "step_id": "H001",
      "step_type": "source_alignment",
      "instruction": "Identify the task objective and the source material that controls the response.",
      "reasoning": "The prompt asks for a specific output grounded in the provided material, so the solution must first determine which source document governs the response and what deliverable shape is required."
    }
  ]
}
```

After saving, tell the user that `starbench-hsw-builder` can now create the final zip.
