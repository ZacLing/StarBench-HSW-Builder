---
name: jsg-task-miner
description: Guide domain experts through a structured interview to mine many Senior-Junior Gap AI-agent task candidates from their role, years of experience, daily work, review habits, judgment calls, hidden constraints, and ambiguous real-world scenarios. Use when the user wants to design, brainstorm, or refine task prompts that test taste, judgment, tradeoffs, risk anticipation, ambiguity handling, or expert-level decision-making rather than routine junior execution.
---

# JSG Task Miner

## Purpose

Turn a user's professional experience into a sizable batch of Senior-Junior Gap (JSG) task candidates: tasks where a junior worker or current AI agent can satisfy the surface request, but a senior expert would avoid hidden traps, make sharper tradeoffs, ask better questions, or preserve long-term quality.

## Core Principle

Mine for divergence:

- **Junior behavior**: literal execution, happy-path thinking, overuse of fashionable tools, shallow optimization, missing edge cases, or failure to clarify.
- **Senior behavior**: taste, judgment, sequencing, risk control, domain-specific constraints, stakeholder awareness, and explicit tradeoffs.

Reject tasks that only test speed, tool fluency, long-context processing, or routine operational complexity unless they contain a real expert judgment fork.

## Intake

Start by collecting enough context to personalize the mining session. Ask concise questions, preferably in rounds rather than one large questionnaire.

Required context:

- Role, domain, seniority, and years of experience.
- Main workflows, artifacts, tools, and decision surfaces.
- Recent examples of review comments, escalations, production incidents, rework, failed handoffs, or "technically correct but wrong" junior outputs.
- Common hidden constraints in the user's field.
- Whether task candidates may assume internet search, subagents, code execution, proprietary materials, or external documents.

If the user gives partial context, proceed with reasonable assumptions and mark assumptions explicitly.

## Quantity Target

Do not produce a tiny list. Unless the user specifies otherwise:

- Generate **20-30 raw task seeds** during exploration.
- Refine at least **12 strong task candidates**.
- Cover all four mining lenses when possible.
- If the domain is narrow, produce fewer only after explaining the limiting factor and asking for more real examples.

## Mining Lenses

Use these four lenses in every session. Translate the user's memories into task candidates, not generic advice.

### 1. Review and Friction

Ask what the user repeatedly corrects in code review, document review, design critique, data analysis review, customer handling, strategy review, or operational postmortems.

Look for:

- "Meets the requirement but feels wrong."
- Review comments that took unusually long to write.
- Outputs that were hard to maintain, hard to trust, misleading, legally risky, off-brand, or brittle.
- Places where juniors optimize the visible metric while damaging the real objective.

### 2. It Depends Forks

Find decisions where the right answer depends on context.

Look for:

- Speed vs reliability.
- Conversion vs trust.
- Automation vs human control.
- Simplicity vs extensibility.
- Standardization vs local adaptation.
- Short-term metrics vs long-term ecosystem health.

Extract the implicit signals a senior uses to choose a path.

### 3. Hidden Constraints and Edge Cases

Find domain rules that experts assume but requirements rarely state.

Look for:

- Dirty data, fraud, bots, duplicate records, timezone or locale traps.
- Legal, compliance, security, privacy, accessibility, safety, or audit constraints.
- Operational failure modes, rollback needs, rate limits, vendor lock-in, maintenance burden.
- Stakeholder constraints such as sales promises, support load, policy interpretation, or brand risk.

### 4. Ambiguous Opening

Design tasks where the first senior move may be to clarify, scope, or de-risk instead of immediately producing a long answer.

Look for:

- Boss-style one-line asks.
- Missing product, audience, budget, authority, timeframe, or success metric.
- Requests that are dangerous if executed literally.

For these tasks, make the task prompt naturally expose whether the agent clarifies first or prematurely executes.

## Workflow

### Step 1: Build the Expert Map

Summarize the user's profile as:

- Domain and seniority.
- Repeated work products.
- High-stakes decisions.
- Common junior failure modes.
- Sources of hidden constraints.

Ask the user to correct the map before deep task generation if the profile is thin or high-stakes.

### Step 2: Generate Raw Seeds

Produce a broad list of raw seeds before polishing. Each seed should include:

- Scenario memory or plausible work situation.
- Junior trap.
- Senior move.
- Which mining lens it came from.

Aim for variety across artifact types: code, analysis, planning, review, writing, design, operations, investigation, and stakeholder communication when relevant.

### Step 3: Select and Deepen

Choose the strongest seeds using these filters:

- The task creates a plausible junior/senior divergence.
- The senior behavior is observable in the output or interaction.
- The task has observable senior behavior in the produced artifact or first response.
- The prompt does not reveal the hidden senior answer too directly.
- The setup is feasible using mock data, public materials, or safely anonymized examples.
- The task may reasonably allow internet search, code execution, or subagents if that matches real work.

### Step 4: Produce Task Cards

For each refined candidate, use this structure:

```text
Task ID:
Title:
Domain / role:
JSG lens:
Scenario:
User-facing task prompt:
Provided materials:
Allowed tools:
Junior trap:
Senior signals:
Hidden constraints:
Failure modes:
Setup notes:
Difficulty:
```

Keep "Junior trap", "Senior signals", and "Hidden constraints" as task-design notes, not inside the user-facing task prompt unless the task is meant to test implementation of stated constraints.

### Step 5: Rank and Iterate

Return a ranked shortlist plus the broader candidate pool. Ask the user to label each strong candidate:

- Keep.
- Merge.
- Make harder.
- Make more realistic.
- Drop.

Then revise the batch. Preserve quantity unless the user explicitly narrows the scope.

## Tooling Guidance

When the user asks for current-market, legal, regulatory, software, product, or platform-specific task realism, use internet search and cite sources in the task design notes.

When the user explicitly allows subagents or parallel agent work, use them for independent ideation, edge-case discovery, or prompt leakage checks. Give subagents bounded prompts such as:

- "Generate hidden-constraint JSG task seeds for this role profile."
- "Stress-test these task prompts for whether they leak the senior answer."
- "Find junior failure modes in this workflow."

Do not rely on subagents for the final judgment; synthesize and prune the results.

## Output Formats

Default deliverables:

- Expert map.
- 20-30 raw seeds.
- 12+ refined task cards.
- Ranked top 5 highest-signal tasks.
- Follow-up questions for making the next iteration more realistic.

For spreadsheet-friendly output, provide a table with columns:

```text
id, title, domain, lens, scenario, user_prompt, materials, allowed_tools, junior_trap, senior_signals, hidden_constraints, difficulty, setup_notes
```

For benchmark-building output, group tasks by:

- Interaction style: direct execution, clarification-first, review, debugging, strategy, investigation.
- Required assets: no materials, mock data, codebase, document bundle, browser/search, multi-agent.
- Output type: code, plan, review comment, investigation report, design proposal, data analysis, operational playbook.

## Quality Bar

Before presenting the final set, check:

- At least 12 candidates are present unless constrained by the user.
- Each candidate has a specific junior trap and senior signal.
- At least one candidate tests ambiguity handling.
- At least one candidate tests hidden constraints.
- At least one candidate tests tradeoff judgment.
- The user-facing prompt is not over-explaining the trap.
- The task-design notes are concrete enough for another task writer to recreate the setup.
