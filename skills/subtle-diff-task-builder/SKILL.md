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
  intake_summary.md
  assumption_inventory_raw.md
  assumption_inventory.json
  candidate_variants.md
  selected_variant.md
  validation_checklist.md
  task_package_<variant_id>/        optional, only when a standard package can be copied
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

## Step 1: Prepare The Expert Reading Brief

Read the task prompt, materials manifest if present, and one representative agent output.

Do not summarize the agent answer as a substitute for expert reading. The expert must inspect the original output, because subtle-diff signal often lives in the answer's actual framing, omissions, emphasis, and path choice.

Create a short reading brief that points the expert to the original files and tells them what to look for:

- original task prompt path;
- materials path or manifest path;
- agent output path;
- optional run/result path;
- the exact question they should answer after reading.

Do not tell the expert what assumptions you think the output makes before they answer. If needed, mention only that they should look for hidden assumptions behind the agent's solution path.

First expert message template:

```text
我们先不设计新任务，也不写 rubric。

请先打开并阅读下面这些原始材料，不要先看我的总结：

- 原始任务：<prompt path>
- 材料/manifest：<materials or manifest path>
- Agent 原始产出：<agent output path>
- 可选测试结果：<run/result path>

读完后请只回答一个问题：

如果这份 Agent 方案要成立，它背后默认了哪些条件？

请列 3-8 条。可以写得很自然，不需要使用任何术语。
```

## Step 2: Assumption Interview

Ask the expert to identify assumptions behind the agent answer.

Chinese prompt:

```text
我们先不设计新任务，也不写 rubric。

请先阅读 Agent 的原始产出，不要只看我的转述。读完后请回答：

如果这套方案要成立，它背后默认了哪些条件？

你可以直接列 3-8 条，例如：默认预算可以增加、默认客户愿意迁移、默认候选人相信公司未来、默认问题主要是渠道不足。
```

English prompt:

```text
Let's not design a new task or write rubrics yet.

Please read the original agent output first, not only my description. After reading it, answer:

For this solution to work, what conditions does it silently assume are true?

Please list 3-8 assumptions, such as budget can increase, customers are willing to migrate, candidates trust the company's future, or the problem is mainly a sourcing problem.
```

If the answer is thin, ask once for more specific assumptions:

- What budget, authority, timing, stakeholder, market, risk, data, compliance, or trust condition is being assumed?
- Which assumption would a junior or generic agent most likely miss?
- Which assumption do real cases often violate?

Preserve the raw expert response in `assumption_inventory_raw.md`.

## Step 3: Pick A Path-Breaking Assumption

Do not ask the expert to write the variant. Ask them to choose the assumption with the most leverage.

Prompt:

```text
如果只能打掉一个默认前提，哪个最能让这套常规方案失效？

更重要的是：这个前提不成立时，专业解法会换到哪条路？请用一两句话说明新路径，不需要写完整方案。
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

## Step 4: Generate Candidate Variants

Generate 2-4 candidate variants from the selected assumption. Each candidate should include:

```text
Variant ID:
Small change:
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

Show the candidates and ask the expert to choose or revise.

Prompt:

```text
请只判断这几个候选变体：

1. 哪个变化最小？
2. 哪个最能让普通答案失效？
3. 哪个最真实、最公平，不像陷阱题？
4. 需要删掉或改写哪一句，才能避免歧义？
```

Do not proceed to package creation until the expert confirms one selected variant or asks to keep it as exploratory notes only.

When saving `selected_variant.md`, use this structure:

```md
# Selected Variant

- Variant ID:
- Source task:
- Source materials:
- Source agent output:
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

## Step 7: Create A Variant Package Or Seed

If the source is a standard task package, create a copied package under `export/subtle_diff/task_package_<variant_id>/`.

Suggested prompt patch:

```md
Additional task condition for this variant:

<selected explicit condition>
```

Use this only when it preserves the original task shape. If the condition naturally belongs in the original task body, rewrite the prompt minimally and document the exact change in `selected_variant.md`.

If the source is an Expert Boost trace without a packaged benchmark task, create a task seed instead:

```text
export/subtle_diff/task_seed_<variant_id>/
  prompt.md
  materials_reference.md
  expected_path_change.md
```

Then hand off to `expert-boost-loop` for a fresh run on that variant.

## Step 8: Report What Was Learned

End with a short status:

- selected assumption;
- selected variant;
- why old template fails;
- what expert path should replace it;
- whether it is ready for a new Expert Boost run, needs expert revision, or should be discarded.

Use cautious language. Subtle-diff production is exploratory; a candidate is not a validated benchmark task until it has been run, reviewed, and crystallized.

## Quality Heuristic

The best concise test:

```text
Can a strong agent produce a polished answer that still follows the wrong old path?
```

If yes, the variant may expose a real HSW boundary.

If no, the variant is probably just a harder task, a clearer instruction, or a normal rubric improvement.
