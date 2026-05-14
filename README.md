# StarBench-HSW Skills

StarBench-HSW is a Codex skill pack for building Humans-Still-Win benchmark tasks. The pack routes users through task discovery, trace production, rubric crystallization, and final benchmark package export.

## Install For Codex

These instructions are intended for Codex to execute.

Clone this repository, then run:

```bash
./install.sh
```

The installer links the skills in this repository into:

```text
${CODEX_HOME:-$HOME/.codex}/skills/
```

Installed skills:

```text
starbench-hsw-builder
jsg-task-miner
expert-boost-loop
rubric-crystallizer
```

After installation, start with:

```text
Use $starbench-hsw-builder
```

## Install From A GitHub URL

When given a GitHub repository URL, Codex should:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skill-packs"
cd "${CODEX_HOME:-$HOME/.codex}/skill-packs"
git clone <github-repo-url> starbench-hsw
cd starbench-hsw
./install.sh
```

If `starbench-hsw` already exists, update it instead:

```bash
cd "${CODEX_HOME:-$HOME/.codex}/skill-packs/starbench-hsw"
git pull --ff-only
./install.sh
```

## Update

From the cloned repository:

```bash
./update.sh
```

Or manually:

```bash
git pull --ff-only
./install.sh
```

## Copy Install

Symlink install is the default and recommended mode. If symlinks are not desired:

```bash
./install.sh --copy
```

Copy installs do not update automatically when the repository is pulled; run `./install.sh --copy` again after updates.

## Developer Notes

Use these notes as the behavior contract when updating the skill pack.

### Recommended Model

`starbench-hsw-builder` should remind users at the start of HSW onboarding:

```text
For high-quality task construction, please confirm you are using GPT-5.5 High. This workflow can use substantial tokens/credits, so keep an eye on usage.
```

For Chinese users, show the same note in Chinese:

```text
为确保任务的高质量完成，请确认当前使用 GPT-5.5-High 模式；这个流程可能消耗较多 token/credit，请随时注意用量。
```

### Skill Responsibilities

The pack is intentionally structured as a total-part-total workflow:

```text
starbench-hsw-builder
-> jsg-task-miner
-> expert-boost-loop
-> rubric-crystallizer
-> starbench-hsw-builder
```

- `starbench-hsw-builder` owns onboarding, routing, startup update checks, and final zip packaging.
- `jsg-task-miner` owns Senior-Junior Gap task ideation before a concrete task exists.
- `expert-boost-loop` owns trace production from an existing prompt/materials package.
- `rubric-crystallizer` owns turning a completed trace into ranked, objective yes/no rubrics.

### Expert Boost Loop Contract

`expert-boost-loop` must preserve a clean boundary between the user-facing trace, executor-visible task context, and host-only intake/audit context.

- Save the raw initial user request exactly in `audit/raw_user_prompt.md`.
- Save the executor-visible clean task prompt in `original/user_prompt.md`.
- Remove chat scaffolding, skill invocation text, local file-path listings, package-location discussion, and host-only intake context from `original/user_prompt.md`.
- Save removed host/intake context in `audit/prompt_intake_notes.md` when present.
- Do not pass audit files, prompt-cleaning notes, packaging notes, hidden notes, scores, strengths, rubrics, or host-only transcript context to executor agents.
- Give executors only the round prompt, explicit allowed material paths, and the output directory.
- Use a fresh executor subagent for every round when available: `model="gpt-5.5"`, `reasoning_effort="high"`, and no forked conversation context.
- Each round must produce a complete replacement output package, not only a patch.
- Feed only accepted weaknesses into the next round.

Review governance is part of the trace contract:

- Vague, subjective, unsupported, or non-actionable comments should be revised before formal recording.
- If a weakness introduces facts, requirements, hidden rules, senior conventions, or domain assumptions beyond the original prompt/materials, ask the user for a plausible rationale before accepting it.
- If the claimed rule conflicts with the original prompt/materials, or the user cannot explain why the hidden rule applies, keep rejecting that weakness.
- If only some weaknesses pass, record/use the grounded ones and ask the user to revise or justify the rest.

The review template must ask for two scores with these meanings:

```text
Latest Deliverables Satisfaction
Current-version satisfaction only. Use 1-5, where 5 means very satisfied and 1 means very dissatisfied.
()/5

Latest Deliverables Aligns User Scores
Score the current deliverables on a 1-10 scale where the user's own performance on this same task is the 5/10 anchor.
()/10
```

For the first review request, give enough guidance for useful comments: ask for concrete weaknesses tied to sections, claims, omissions, behaviors, risks, missing constraints, wrong assumptions, or hidden senior/domain rules. Also tell the user they can ask clarifying questions first, then continue filling the comments.

### Rubric Crystallization Contract

`rubric-crystallizer` should convert a completed trace into rubrics that catch agent failure modes. Rubrics are not merely a summary of what changed from `v0` to `vN`; a concern can become a rubric even if the final deliverable still fails it.

- Generate at least 15 candidate rubrics when the trace has enough objective signal.
- Letter original candidates `A`, `B`, `C`, and so on; after `Z`, continue with `AA`, `AB`, etc.
- Each rubric must be a single objective yes/no question with an expected answer.
- Each rubric should test one concrete point.
- Accepted weaknesses and hidden-rule rationales are the primary signal.
- Adjacent deliverable comparisons and `v0` versus final comparisons are supporting evidence, not the eligibility rule.
- Subjective, vague, unsupported, duplicate, or non-evaluable signals should be quarantined instead of forced into rubrics.
- Classify every rubric as `fail_fast` or make-better, explain the classification, and let the user adjust it.
- `fail_fast: true` is for the baseline pass line, such as wrong language, wrong artifact shape, missing required output, ignored required material, or forbidden web use.
- `fail_fast: false` is for make-better rubrics that distinguish senior-quality agents after baseline compliance.

User-facing rubric presentation must stay complete and localized:

- Internal reasoning and canonical stored questions may be English.
- Any rubric list shown to the user must use the user's language.
- Show the complete text of every rubric, not abbreviated placeholders such as `Does the deliverable ...?`.
- Do not ask the user to simply "approve this top15".
- Ask the user to rank, edit, delete, add, and optionally reclassify rubrics.

Use a ranking prompt like:

```text
请按你认为最能挑出 agent 错误的顺序回复，格式如下：

C: <完整 rubric 文本>
B: <完整 rubric 文本>
A: <完整 rubric 文本>
D: <完整 rubric 文本>
Remove F
Change C to: <完整修改后的 rubric 文本>
Add: <完整新增 rubric 文本>
Type B: make-better
Type H: fail-fast

如果你已经逐条看过，并且想完全沿用我展示的当前顺序，请明确说：
使用当前完整顺序，不做修改。
```

Save both rubric sets independently:

```text
export/rubrics_original.json
export/rubrics_original.md
export/rubrics_curated.json
export/rubrics_curated.md
```

The original set preserves first-pass candidates. The curated set preserves user ranking, edits, deletions, additions, type changes, canonical questions, and user-language display questions.

### Final Packaging Contract

Final zip packaging belongs to `starbench-hsw-builder`, not `expert-boost-loop`. Packaging should happen only after curated rubrics and a human reference exist.

Preconditions:

- `original/user_prompt.md` exists and is the clean prompt.
- `original/materials/` contains copied task materials when the task depends on source files.
- `export/rubrics_original.json` exists.
- `export/rubrics_curated.json` exists with at least 15 active rubrics.
- `export/human_reference.json` exists and matches the benchmark schema.

The final zip must contain two top-level parts:

```text
trace/
task_package/
```

`trace/` contains the auditable record:

```text
trace/
  task.json
  audit/
  original/
  rounds/
  reviews/
  export/
```

`task_package/` must be compatible with `OpenAI_bench_tasks/tasks/demo_instruction_reference`:

```text
task_package/
  task.json
  prompt.md
  materials/
  rubrics.json
  human_reference.json
```

`task_package/prompt.md` must be copied from the clean `original/user_prompt.md`. It must not include raw chat scaffolding, local file paths, skill-routing text, packaging instructions, review instructions, or prompt-cleaning notes.

If `original/materials/` contains files, copy them into `task_package/materials/` and include a `materials` array in `task_package/task.json` with paths relative to `task_package/`. If there are no materials, omit the `materials` key.

`task_package/task.json` should use this shape:

```json
{
  "id": "task_id",
  "name": "Task Name",
  "prompt": "prompt.md",
  "rubrics": "rubrics.json",
  "human_reference": "human_reference.json",
  "materials": [
    "materials/source_document.pdf"
  ],
  "timeout_seconds": 1800,
  "allow_web_search": false
}
```

`task_package/rubrics.json` uses the top 15 active curated rubrics in user-ranked order:

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

`task_package/human_reference.json` uses:

```json
{
  "steps": [
    {
      "step_id": "H001",
      "step_type": "structure",
      "instruction": "...",
      "reasoning": "..."
    }
  ]
}
```

### Validation Before Commit

After changing skill files or scripts, run the relevant checks:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/starbench-hsw-builder
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/expert-boost-loop
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/rubric-crystallizer
git diff --check
```
