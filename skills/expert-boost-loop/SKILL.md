---
name: expert-boost-loop
description: StarBoost-style expert-in-the-loop iteration for Codex conversations with an explicit user-chosen task package location, fresh isolated executor subagents for every output round, and host-Codex review governance. Use when a user provides an initial task prompt and materials, wants Codex to create a complete output package, then repeatedly collects human comments, scores, strengths, and weaknesses, rejects vague or subjective comments for revision before formal recording, gates whether accepted comments contain enough expert signal, and regenerates full improved packages using only accepted weaknesses as revision targets with an auditable local history.
---

# Expert Boost Loop

Use this skill to run a lightweight StarBoost-style improvement harness inside a Codex conversation.

## Core Rules

- Decide the task package location before initializing a run.
- Main Codex orchestrates the run; a fresh executor subagent produces each cold-start or boosted output package.
- Save the user's original task prompt exactly before acting on it.
- Save accepted review-like user messages exactly before sending them into the formal trace.
- If comments are too vague, subjective, or unactionable, ask the user to revise before creating the formal review record.
- If a weakness introduces facts, requirements, or hidden rules beyond the original prompt and materials, require a plausible user rationale before accepting it.
- After each executor output, show the user a comments template before asking for review.
- Require the two review scores in every round: current-version satisfaction and current deliverable performance relative to the user's own work, where the user's own level on this task is the `5/10` anchor.
- Main Codex judges both weakness quality and minimum useful weakness count for each round; do not use a purely mechanical round number rule.
- Produce complete output packages for every round, never only patches.
- Feed only the latest parsed weaknesses into the next revision round.
- Do not feed strengths, scores, hidden notes, private reasoning, rubrics, or inferred references into the next round.
- Preserve previous outputs for inspection, but write a full replacement package each boosted round.
- Continue until the user provides no weaknesses, says the output is acceptable, or explicitly asks to finish.
- Do not create the final benchmark task package or zip. After termination, hand off to `rubric-crystallizer` for rubrics and `starbench-hsw-builder` for final packaging.

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

## Review Governance

Main Codex hosts the review loop. The goal is not to maximize the number of rounds; it is to collect enough expert signal for the next executor to make a meaningful improvement, and to stop when additional review is unlikely to add value.

Use judgment, not a rigid formula. Gate comments in this order:

1. **Scope and hidden-rule gate**: are the proposed weaknesses grounded in the original prompt, provided materials, current deliverable, or a plausibly explained senior/domain rule?
2. **Quality gate**: are the proposed weaknesses objective, concrete, clear, and actionable enough to guide the next executor?
3. **Quantity gate**: after low-quality weaknesses are excluded, are there enough useful weaknesses for this round?
4. **Continuation gate**: given task difficulty, scores, comments, and remaining leverage, should another executor round run?

The scope gate comes first. A review with five precise-looking weaknesses is not usable if they smuggle in unsupported external requirements that the executor cannot justify from the task package.

### Scope And Hidden-Rule Gate

Before accepting review feedback, compare each weakness against the known task boundary:

- the original user prompt;
- the provided materials and their manifest;
- the current deliverable under review;
- prior accepted review weaknesses, if they were already admitted into the trace.

Use a low tolerance for unsupported external claims. A weakness is suspect when it:

- adds a new factual claim, requirement, constraint, target audience, policy, standard, metric, market assumption, or evaluation criterion that does not appear in the original prompt or materials;
- contradicts the original prompt, materials, or an already accepted task constraint;
- depends on a hidden industry rule, senior norm, or domain convention that is not obvious from the task package;
- asks the next executor to optimize for a goal that a fresh executor could not infer from the allowed context.

If the new claim is a plausible hidden senior/domain rule, do not reject it outright. Ask the user for a brief rationale explaining why the rule applies to this task. Accept it only if the explanation is self-consistent, compatible with the original prompt and materials, and specific enough for a fresh executor to apply. Record both the original feedback and the user's rationale verbatim when the review is accepted.

If the claim clearly conflicts with the original prompt or materials, or the hidden rule is too far outside the known task context to evaluate safely, reject that weakness and ask for the user's reason. If the user cannot give a coherent reason, continues to rely only on authority, or simply insists without explaining the domain logic, keep rejecting that weakness and do not pass it to the executor. User insistence alone is not enough to force this gate.

When only some weaknesses fail this gate, accept the grounded ones and ask the user to revise or justify the out-of-scope ones before they can enter the formal trace.

### Weakness Quality Standard

Judge weaknesses like serious OpenReview-style or academic reviewer comments. A good weakness should usually:

- point to a concrete artifact location, section, claim, behavior, omission, assumption, or failure mode;
- explain why it matters for the original task or end user;
- be grounded in the current deliverable, task prompt, or provided materials rather than personal taste alone;
- be specific enough that a fresh executor can act on it without seeing the host conversation;
- avoid hidden answer leakage while still naming the substantive issue;
- include a rationale when it relies on an unstated senior/domain convention;
- be distinct from other weaknesses.

Poor weaknesses include:

- "make it better";
- "too vague" without naming what is vague;
- "I do not like the tone" without tying tone to audience, task, or deliverable goal;
- "missing details" without naming which details or where;
- duplicated comments with different wording;
- preferences that contradict the original task or provided materials.
- hidden-rule claims that are not justified when asked for a reason.

If comments do not pass this quality standard, do not create the formal `review.json` yet and do not launch the executor. Ask the user to revise, giving brief rewrite suggestions. Example:

```text
These comments are not quite actionable enough for the next executor yet. Could you rewrite them so each weakness names the specific section/claim/problem and why it matters? For example, instead of "too vague", write "The Risk Analysis section says the data should be minimized but does not identify which fields should be removed before vendor upload."
```

If only some weaknesses are good, tell the user which ones are usable and ask them to revise or replace the vague ones. If the user strongly insists on continuing anyway, record the review as forced and pass only the actionable weaknesses to the executor.

Decide the minimum weakness count for the current round from:

- **Task difficulty**: harder, more expert-heavy, or more ambiguous tasks need more weaknesses, especially in early rounds.
- **Round maturity**: first and second reviews usually need more concrete weaknesses; later rounds may need fewer.
- **User satisfaction language**: comments like "basically good", "acceptable", "only small issues", or "I am satisfied" lower the minimum; comments like "still far", "not usable", or "misses the point" raise it.
- **Two scores**:
  - `Latest Deliverables Satisfaction` is only about the current version of the deliverables. It is an integer from `1-5`, where `5` means very satisfied and `1` means very dissatisfied.
  - `Latest Deliverables Aligns User Scores` is the current deliverables' performance relative to the user's own work on this same task. It is an integer from `1-10`; the user's own level is the `5/10` anchor, so `5` means about as good as the user would personally produce on this task.
- **Weakness specificity**: one precise, high-leverage weakness can be worth more than several vague complaints.
- **Remaining leverage**: if the user is repeating prior feedback, only naming polish, or cannot identify actionable weaknesses despite high scores, the loop may be ready to terminate.

Default starting points:

- Easy task: ask for at least `2-3` weaknesses in the first review.
- Medium task: ask for at least `3-5` weaknesses in the first review.
- Hard or highly expert task: ask for at least `5-7` weaknesses in the first review.
- Strengths are lenient: usually ask for `0-1`; ask for more only when useful for audit context.

Adjust from there. High satisfaction (`4-5/5`) and a high user-relative score (`8-10/10`) can reduce the next minimum to `0-1`. Low satisfaction (`1-2/5`) or a low user-relative score (`1-4/10`) should usually require several actionable weaknesses before another executor round.

These numbers are only anchors. Main Codex may override them when the user's natural-language comments clearly indicate more or less remaining expert signal than the scores alone suggest. Prefer thoughtful judgment over arithmetic.

Do not explicitly tell the user "you can no longer contribute" or similar. If the loop appears exhausted, phrase it naturally:

```text
This looks close enough that we can either finish the trace here, or you can give me one last concrete weakness if there is still something important to improve.
```

If the user provides too few actionable weaknesses for the current minimum, record the message first, then ask for more. Do not launch the next executor until the review gate is satisfied, unless the user clearly and strongly asks to continue anyway. If they force continuation, mark the review as forced and use only the actionable weaknesses actually provided.

### Comments Template

After every executor output, create and show a blank comments template. Prefer:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py review-template --run <task_package_dir> --round-under-review <latest_round_id> --deliverables-path <outputs_path> --min-strengths <min_strengths> --min-weaknesses <min_weaknesses> --rationale <brief_host_rationale>
```

Then show the user the important parts directly in chat:

```text
For this round, please give at least <min_weaknesses> concrete weaknesses. Strengths are optional/lightweight, but helpful for context. Please also fill in the two scores.

A useful weakness should name the specific section, claim, omission, behavior, or failure mode, and explain why it matters. Avoid vague comments like "make it better" or "too shallow" unless you specify what is shallow and what the next version should address.

For the first review, compare the current deliverables against the original task and materials. Focus on concrete places where an agent is likely to fail: missing constraints, wrong assumptions, unsafe shortcuts, weak evidence, shallow reasoning, or hidden senior/domain rules. If a weakness depends on an unstated industry rule or senior convention, include a short reason why that rule applies here. It is okay if the first pass is not perfectly phrased; I can help tighten it.

If anything is unclear, the user can ask a question first, then continue filling the comments.

Strengths:
- <optional strength>

Weaknesses:
- <actionable weakness>

Latest Deliverables Satisfaction:
Current-version satisfaction only. Use 1-5, where 5 means very satisfied and 1 means very dissatisfied.
()/5

Latest Deliverables Aligns User Scores:
Score the current deliverables on a 1-10 scale where the user's own performance on this same task is the 5/10 anchor.
()/10

Notes:
```

If the user's language is not English, translate the visible labels and explanations while preserving the two score names if that helps parsing. The stored comments can still use the English headings when practical.

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

10. Use Review Governance to decide the current minimum weakness count, create/show the comments template, and ask the user for comments.

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

1. First apply the Scope And Hidden-Rule Gate, then the Weakness Quality Standard. If a weakness introduces facts, constraints, requirements, or hidden senior/domain rules beyond the original prompt and materials, ask the user for a brief reason before accepting it. If the explanation is coherent and compatible with the task package, accept it and record both the original feedback and the rationale verbatim. If the user cannot justify it, keep rejecting that weakness and do not pass it to the executor.
2. If the comments are too subjective, vague, duplicated, or unactionable, do not create the formal review record yet. Ask the user to revise and give one or two concrete rewrite suggestions.
3. Once the review passes the scope and quality gates, or the user strongly insists on continuing past a non-scope quality or quantity issue, save it verbatim:

```bash
python3 ~/.codex/skills/expert-boost-loop/scripts/boost_record.py record-review --run <task_package_dir> --round-under-review <latest_round_id> --raw-file <verbatim_review_file> --min-strengths <min_strengths> --min-weaknesses <min_weaknesses> --quality-decision <accepted|forced> --host-decision <request_more|continue|terminate>
```

4. Parse strengths, weaknesses, scores, and notes conservatively from the raw text.
5. If the user did not use the template headings, still save the raw text exactly, then pass host-parsed fields through `--strength`, `--weakness`, `--satisfaction`, `--aligns-user-score`, and `--notes` so `review.json` is structured without altering the raw text.
6. Update `review.json` with parsed `strengths`, `weaknesses`, `scores`, `notes`, validation, quality decision, and the host decision while keeping `raw_text` unchanged. Use `--quality-issue` for any admitted hidden-rule or scope concerns that were resolved by rationale.
7. If the review passes quality but does not meet the current quantity or score gate, preserve it first, then ask for the missing concrete weaknesses or scores. Do not launch the executor yet.
8. If weaknesses are ambiguous after formal recording, ask a concise clarification before launching the executor.
9. If the user strongly insists on continuing despite an unmet non-scope quality or quantity gate, record with `--forced-by-user --quality-decision forced --host-decision continue`, then proceed using only actionable parsed weaknesses. Do not use forced continuation to pass unsupported out-of-scope or hidden-rule claims.

Never summarize instead of saving the raw user review once it is accepted into the formal trace.

## Boosted Round

If the accepted review contains one or more actionable weaknesses and Main Codex judges another round can still improve the deliverable:

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
7. Write `final.md`, run `boost_record.py manifest`, update `task.json`, and use Review Governance to create/show the next comments template.

If the accepted review has no actionable weaknesses, or Main Codex judges from the scores, language, task difficulty, and review content that another round is unlikely to add value, terminate instead of launching a boosted round.

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

If the user provides no weaknesses, says the output is acceptable, scores are high with no actionable weaknesses, review signal is exhausted, or the user asks to finish:

1. Record the final review verbatim first.
2. Set `task.json.status` to `terminated`.
3. Write `export/run_summary.json` and `export/run_summary.md`.
4. Include original task path, round ids, review ids, final outputs path, and unresolved risks if any.
5. Tell the user that the next step is `rubric-crystallizer` if they want objective rubrics, and `starbench-hsw-builder` after curated rubrics exist if they want the final zip package.

## User-Facing Replies

Keep replies compact:

- After each executor output: report the task package path and output path, then show the comments template with the current minimum weakness count and two scores.
- After each review: say the review was recorded. If the gate is not met, ask for the missing weaknesses or scores. If accepted and continuing, create the next complete package.
- After termination: report the task package path, final output path, and export summary path. Do not claim the benchmark package or final zip exists.

Do not claim files were recorded unless they exist.
