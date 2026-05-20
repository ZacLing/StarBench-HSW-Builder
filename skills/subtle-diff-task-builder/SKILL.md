---
name: subtle-diff-task-builder
description: Guide experts through a low-friction assumption-breaking interview to create candidate StarBench-HSW subtle-diff task variants. Use when the user has an existing task prompt, standard task package, baseline agent output, or Expert Boost trace and wants to explore "small input change, different expert path" variants without asking the expert to directly design subtle-diff tasks.
---

# Subtle Diff Task Builder

## Purpose

Use this skill to explore candidate subtle-diff task variants for StarBench-HSW.

The skill does not ask the expert to "write a subtle diff task." That is too abstract. Instead, it directs the expert to read the original agent output, asks what hidden assumptions make that output look reasonable, and then helps the expert break one important assumption with a small, explicit task-condition change.

The target pattern is:

```text
small input change -> common template fails -> expert path changes
```

This is an exploration workflow, not a replacement for `expert-boost-loop`, `human-reference-collector`, or `rubric-crystallizer`.

## Workflow Position

This skill is a sidecar that can attach to the normal HSW flow without modifying other skills.

Use it after one of these exists:

- a baseline agent output for a task;
- a completed or partial `expert-boost-loop` trace;
- a standard task package with previous model-test outputs;
- a strong JSG task candidate from `jsg-task-miner` plus at least one agent answer.

Natural handoffs:

- From `jsg-task-miner`: when a task seed seems promising but needs a path-changing variant.
- From `expert-boost-loop`: use `v0` or another agent output as the conventional answer to inspect.
- To `expert-boost-loop`: run the selected subtle-diff variant as a new task if it passes gates.
- To `human-reference-collector`: collect how the expert would solve the selected variant.
- To `rubric-crystallizer`: crystallize rubrics only after the variant has real expert feedback or trace evidence.
- To `starbench-hsw-builder`: package only after the variant has passed validation and rubric work.

Do not edit other skill files to register this handoff. Keep integration in this skill's own instructions and outputs.

## Core Rules

- Do not ask the expert to define subtle diff.
- Do not ask the expert to design a benchmark.
- Do not let the agent invent the path change alone. The key assumption break must be confirmed by the expert.
- Do not treat "harder" as better. A valid variant is not merely more complex.
- Do not create trick questions, brain teasers, or unfair hidden constraints.
- Do not modify the original task package or Expert Boost trace.
- Do not reuse original rubrics as final variant rubrics unless the user explicitly asks and the rubric still fits.
- Do not bypass `rubric-crystallizer` for final benchmark rubrics.
- Keep expert interaction light: short summaries, one question at a time, and concrete choices.

## Expert-Facing Voice

Follow the same interaction style as the rest of the HSW skill pack:

- Speak to the expert as a collaborator, not as a system explaining its own workflow.
- Ask one practical question at a time.
- Use plain working language. Avoid benchmark-construction terms unless the user already uses them.
- Keep internal mechanics invisible. Do not mention skill names, manifests, traces, run IDs, model-test folders, score files, or framework structure in expert-facing messages.
- Do not tell the expert what not to read, what Codex has summarized, or what internal step is happening. Just point them to the original task, materials, and output.
- Do not show JSON files as expert reading material. If JSON is needed to locate something, read it internally and surface only the human-readable source or the actual task input.
- Do not show the expert a long checklist unless they ask. Convert gates into small natural questions.
- When showing local files in Codex, use Markdown links with absolute paths so the user can open them in the right-side preview, for example `[prompt.md](/absolute/path/to/prompt.md)`. If a path contains spaces, wrap the link target in angle brackets, for example `[prompt.md](</absolute/path with spaces/prompt.md>)`.
- If the interaction is running in a plain terminal where clickable preview is unavailable, keep paths short and readable, with a plain label.

Good first-step tone:

```text
我已经找到这个任务的原始任务和 Agent 产出。

请先阅读：
- 原始任务：<clickable prompt link>
- 输入材料：<clickable materials link or "这个任务没有额外输入材料">
- Agent 原始产出：<clickable output link>

读完后，请告诉我：这份方案要成立，背后默认了哪些条件？

列 3-8 条即可，用你的日常工作语言写。
```

## Inputs

Accept any of these:

```text
task_package/
  task.json
  prompt.md
  rubrics.json
  materials/
  human_reference.json optional

Expert Boost run root/
  original/user_prompt.md
  original/materials/
  rounds/*/outputs/
  reviews/*
  export/

model_tests/<run_id>/
  result_summary.json
  framework_runs/
```

If no agent output exists, tell the user that subtle-diff mining needs a conventional answer to inspect. Ask whether to run or provide one baseline output first.

## Output Files

When a working directory is available, save under:

```text
export/subtle_diff/
  assumption_inventory_raw.md
  assumption_inventory.json
  candidate_variants.md
  selected_variant.md
  validation_checklist.md
  candidates/
    <variant_id>/
      task_package/                 when a standard package can be copied
      task_seed/                    fallback when no standard package exists
      subtle_diff_notes.md
  selected/
    task_package/                   copied from the expert-confirmed candidate when ready
    task_seed/                      fallback when the selected candidate is only a seed
    subtle_diff_task_package.zip    final shareable zip when a task package exists
    subtle_diff_task_seed.zip       final shareable zip when only a seed exists
```

Use this minimal structure for `assumption_inventory.json`:

```json
{
  "source_task": "",
  "source_materials": [],
  "agent_output": "",
  "raw_assumptions": [
    {
      "id": "A1",
      "text": "",
      "source": "expert"
    }
  ],
  "selected_assumption": {
    "id": "",
    "text": "",
    "expert_rationale": ""
  },
  "old_path": "",
  "new_path": "",
  "expert_confirmation": ""
}
```

For a standard package variant, copy the source package and change only what is required:

- `prompt.md`: add the selected explicit condition change.
- `task.json`: update task id/name only if needed for uniqueness.
- Add `subtle_diff_notes.md` as trace documentation if useful.

Do not alter source materials unless the selected condition must be represented as a new material. If a new material is needed, make it explicit and document why the prompt alone is insufficient.

## Step 1: Locate The Expert Reading Sources

Read only enough project structure to locate the original task prompt, input materials, and one representative original task output.

Do not summarize the agent answer as a substitute for expert reading. The expert must inspect the original output, because subtle-diff signal often lives in the answer's actual framing, omissions, emphasis, and path choice.

Do not create a separate reading brief file. Do not ask the expert to read framework metadata or internal run files.

Expert-facing reading sources must be limited to:

- the original task prompt, usually `prompt.md`;
- the actual input materials used by the task;
- the original agent output being inspected.

Use internal JSON files only to locate the real materials or outputs. Do not show these files as expert reading targets:

- `task.json`;
- `rubrics.json`;
- `human_reference.json`;
- `materials_manifest.json`;
- `result_summary.json`;
- framework manifests, logs, traces, or score files.

If the only available pointer to materials is a JSON manifest, read it yourself and point the expert to the underlying human-readable files or materials folder. If the actual task input itself is JSON and no human-readable material exists, say that the task input appears to be structured data and ask whether to convert or extract the relevant content for review. Do not simply tell the expert to read the JSON.

Do not tell the expert what assumptions you think the output makes before they answer. If needed, mention only that they should look for hidden assumptions behind the agent's solution path.

Avoid internal workflow language in expert-facing messages. Do not mention skill names, `trace`, `model_tests`, weak models, run IDs, manifests, framework paths, or "according to the skill". Keep the message as a normal working instruction.

First expert message template:

```text
我已经找到这个任务的原始任务和 Agent 产出。

请先阅读：

- 原始任务：<prompt path>
- 输入材料：<human-readable materials path or "这个任务没有额外输入材料">
- Agent 原始产出：<agent output path>

读完后，请告诉我：

如果这份 Agent 方案要成立，它背后默认了哪些条件？

请列 3-8 条，用你的日常工作语言写即可。
```

## Step 2: Assumption Interview

Ask the expert to identify assumptions behind the agent answer.

Chinese prompt:

```text
请先阅读这个任务的原始内容和 Agent 原始产出。

读完后，请告诉我：

如果这套方案要成立，它背后默认了哪些条件？

请直接列 3-8 条，用你的日常工作语言写即可。
```

English prompt:

```text
Please read the original task materials and the original agent output. After reading them, answer:

For this solution to work, what conditions does it silently assume are true?

Please list 3-8 assumptions in your normal working language.
```

If the answer is thin, ask once for more specific assumptions:

- What budget, authority, timing, stakeholder, market, risk, data, compliance, or trust condition is being assumed?
- Which assumption would a junior or generic agent most likely miss?
- Which assumption do real cases often violate?

Preserve the raw expert response in `assumption_inventory_raw.md`.

## Step 3: Pick A Path-Breaking Assumption

Do not ask the expert to write the variant. Ask them to choose the assumption with the most leverage.

Expert-facing prompt:

```text
在你列出的这些默认条件里，哪一个最关键？

也就是说：如果这个条件不成立，原方案会在哪些地方不适用？真正专业的处理会转向什么方向？

请选 1 条，并用一两句话说明。不需要写完整方案。
```

Accept only assumptions where the expert can explain the path change.

Weak answer:

```text
It gets harder.
```

Strong answer:

```text
The task stops being a sourcing problem and becomes a candidate-risk-reversal problem, because higher pay is unavailable and candidates doubt the business direction.
```

## Step 4: Generate Candidate Task Packages

Generate 2-4 candidate variants from the selected assumption and immediately materialize each one as a candidate task package when possible.

Do not stop at describing candidate changes in chat. The useful artifact is a concrete package the expert and later tester can open, inspect, and run.

For a standard source package, copy it to:

```text
export/subtle_diff/candidates/<variant_id>/task_package/
```

Then change only what is required:

- `prompt.md`: add or minimally integrate the selected explicit condition change.
- `task.json`: update task id/name only if needed for uniqueness.
- `materials/`: copy unchanged unless the selected condition must be represented as a material.
- `subtle_diff_notes.md`: write the assumption, small change, expected path change, and fairness risks.

If the source is not a standard task package, create a task seed instead:

```text
export/subtle_diff/candidates/<variant_id>/task_seed/
  prompt.md
  materials_reference.md
  expected_path_change.md
```

Also write a compact `candidate_variants.md` index that points to each generated package or seed using clickable local file links when available.

Each candidate entry should include:

```text
Variant ID:
Small change:
Candidate package:
Revised task condition:
Old template likely to fail:
New expert path:
Why it is real:
Fairness risks:
Recommended status: keep / revise / reject
```

Keep the task change minimal. Prefer one explicit sentence or one compact paragraph over a rewritten task.

Examples of good change shapes:

- "However, the company cannot increase cash compensation this year."
- "Assume the customer has already failed once with a similar migration."
- "The provided data excludes churned customers."
- "The target audience is a regulator, not an internal executive."

Bad change shapes:

- adding many unrelated constraints;
- changing the entire domain;
- making the task impossible without saying so;
- hiding the controlling fact outside the provided materials;
- using a gotcha condition that no professional would reasonably expect.

## Step 5: Expert Confirmation

Show the generated candidate packages and ask the expert to choose or revise in plain language.

Expert-facing prompt:

```text
我已经生成了几个候选测试包。请你打开看一下，不需要帮我写完整任务，只判断它们是否像真实工作。

请重点看四点：

1. 哪个变化最小？
2. 哪个最能让原来的方案不再适用？
3. 哪个最像真实工作，不像故意刁难？
4. 哪一句需要删掉或改写，才能避免误解？
```

Do not treat any generated package as validated until the expert confirms one selected variant or asks to keep it as exploratory notes only.

When saving `selected_variant.md`, use this structure:

```md
# Selected Variant

- Variant ID:
- Source task:
- Source materials:
- Source agent output:
- Candidate package:
- Selected assumption:
- Expert-confirmed old path:
- Expert-confirmed new path:
- Final explicit condition:
- Gate results:
- Status:
- Remaining risks:
- Expert confirmation quote:
```

## Step 6: Validation Gates

Before creating a package, check all gates:

- **Small change**: the variant is recognizably the same task.
- **Path change**: the expert path changes, not just the amount of detail.
- **Old-template failure**: a generic or prior agent answer would plausibly continue down the wrong path.
- **Reality**: the condition can occur in real work.
- **Reader fairness**: the prompt or materials explicitly provide the controlling condition.
- **Non-trick**: the failure is not caused by wordplay, ambiguity, or missing information.
- **Evaluability**: later rubrics or pairwise analysis can observe whether the answer changed path.
- **Expert confirmation**: the domain expert endorses the condition and path change.

### Who Screens What

Screening has two layers.

**Codex screens mechanical gates first.** Codex can reject or flag a candidate when:

- the task was rewritten too much to count as a small change;
- the controlling condition is not explicitly present in the revised prompt or materials;
- the variant introduces ambiguity, missing information, or an impossible task without saying so;
- the old and new tasks are so different that comparison is no longer meaningful;
- there is no observable way to tell whether the answer changed path.

Codex may label these as `revise` or `exploratory_not_ready` without expert judgment, because they are benchmark-construction and reader-fairness checks.

**The expert screens domain gates.** Only the expert can decide:

- whether the broken assumption is a real workplace assumption;
- whether this assumption matters enough to change professional quality;
- whether the new solution path is truly different rather than merely more detailed;
- whether a strong senior would recognize this as a fair and important condition.

If the expert cannot explain the path change, the candidate must not be treated as a validated subtle-diff task, even if Codex can write a polished variant.

### Gate Logic

Use the gates in order:

1. **Same-task gate**: if the change creates a new task rather than a variant, reject or shrink it.
2. **Reader-fairness gate**: if the key condition is not visible in the prompt/materials, revise before testing.
3. **Reality gate**: ask the expert whether this condition occurs in real work. If not, reject.
4. **Path-change gate**: ask the expert to name the old path and the new path. If they can only say "it is harder," reject.
5. **Old-template failure gate**: Codex first compares the original answer against the revised condition and checks whether it would plausibly fail if reused. If the failure depends on domain judgment, the expert must confirm it. If not, the variant may be a normal improvement task, not subtle diff.
6. **Evaluability gate**: decide whether a later reviewer can observe the path difference in outputs. If not, keep as research notes rather than benchmark material.

If any gate fails, save notes but label the variant `exploratory_not_ready`. If a gate is uncertain, label it `needs_expert_review` and ask the expert the smallest clarifying question.

## Step 7: Finalize And Zip The Selected Candidate

After expert confirmation, copy the selected candidate into:

```text
export/subtle_diff/selected/task_package/
```

If only a task seed exists, copy it into:

```text
export/subtle_diff/selected/task_seed/
```

Update `selected_variant.md` with the expert-confirmed old path, new path, gate results, remaining risks, and the selected package or seed path.

Then create a shareable zip automatically:

- If `export/subtle_diff/selected/task_package/` exists, zip that folder as `export/subtle_diff/selected/subtle_diff_task_package.zip`.
- If only `export/subtle_diff/selected/task_seed/` exists, zip that folder as `export/subtle_diff/selected/subtle_diff_task_seed.zip`.
- Include `selected_variant.md` and `validation_checklist.md` in the zip when they exist, so reviewers can see why this variant was selected.
- Do not ask the expert to run zip commands or manually collect files.

After zipping, show only the final zip link and the selected package link. Use clickable Markdown absolute-path links when the user is in Codex.

Then hand off to `expert-boost-loop` for a fresh run on that selected variant if the user wants to continue testing.

## Step 8: Report What Was Learned

End with a short closeout status:

- selected assumption;
- selected variant;
- why old template fails;
- what expert path should replace it;
- final selected task package or seed path;
- final shareable zip path;
- whether it is ready for a new Expert Boost run, needs expert revision, or should be discarded.

Expert-facing closeout template:

```text
这个 subtle diff 候选任务已经整理完成。

- 选中的变化：<one-line selected variant>
- 为什么原方案会失效：<one-line old path failure>
- 新的专业处理方向：<one-line new path>
- 可检查的任务包：<clickable selected package link>
- 可直接发送的 zip：<clickable zip link>
```

Use cautious language. Subtle-diff production is exploratory; a candidate is not a validated benchmark task until it has been run, reviewed, and crystallized.

## Quality Heuristic

The best concise test:

```text
Can a strong agent produce a polished answer that still follows the wrong old path?
```

If yes, the variant may expose a real HSW boundary.

If no, the variant is probably just a harder task, a clearer instruction, or a normal rubric improvement.
