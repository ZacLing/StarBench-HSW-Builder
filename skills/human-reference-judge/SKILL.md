---
name: human-reference-judge
description: Internal helper skill for independently reviewing a draft StarBench-HSW `human_reference.json` created by `human-reference-collector`. Use only when asked to judge step splitting, instruction abstraction, reasoning specificity, step_type labels, raw-fidelity, and benchmark schema fit for human reference steps.
---

# Human Reference Judge

## Purpose

Review a draft `human_reference.json` independently. This skill is normally invoked by `human-reference-collector` inside a fresh no-context subagent.

The job is to judge whether the human reference steps are well split, abstracted correctly, faithful to the raw human explanation, and compatible with final benchmark packaging.

## Inputs

Expect explicit paths to:

```text
original/user_prompt.md
original/materials_manifest.json
original/materials/
export/rubrics_curated.json
export/human_reference_raw.md
export/human_reference_draft.json
```

Read only the files provided. Do not rely on any prior conversation.

## Review Criteria

Check:

- **Schema**: top-level object contains only `steps`; each step has exactly `step_id`, `step_type`, `instruction`, and `reasoning`.
- **Step split**: each step is a minimal key reasoning unit; steps are split by newly introduced bottlenecks.
- **Instruction abstraction**: `instruction` says what to do, but does not include concrete answers, exact values, specific intermediate conclusions, or final results.
- **Reasoning specificity**: `reasoning` states what information is used, how it is used, and what concrete intermediate conclusion is reached.
- **Step type**: `step_type` is a concise summary label, not a fixed taxonomy. Do not require categories such as `source`, `common_knowledge`, or `professional_knowledge`.
- **Raw fidelity**: the draft does not invent steps unsupported by the raw human process, prompt, or materials.
- **Task fit**: the steps describe how a human solves the task, not how an evaluator scores a submission.
- **Language**: the strings use the requested output language unless the user requested otherwise.

## Output

Return JSON only:

```json
{
  "verdict": "revise",
  "issues": [
    {
      "severity": "blocking",
      "step_id": "H001",
      "field": "instruction",
      "issue": "The instruction includes a concrete intermediate conclusion.",
      "suggestion": "Rewrite it as abstract guidance without naming the conclusion."
    }
  ],
  "global_notes": [
    "The step split is mostly clear, but two reasoning units combine domain judgment and calculation."
  ],
  "revision_priorities": [
    "Remove answer leakage from instructions.",
    "Split mixed domain-rule and calculation steps."
  ]
}
```

Use `verdict: "pass"` only when remaining issues are minor. Use `verdict: "revise"` when any issue should be fixed before final save.

Use the requested output language for all string values except JSON keys and enum-like values.
