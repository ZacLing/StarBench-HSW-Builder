---
name: jsg-task-miner
description: Guide domain experts through a structured interview to surface real Senior-Junior Gap AI-agent task opportunities from their actual work, materials, data, review habits, judgment calls, hidden constraints, and ambiguous real-world scenarios. Use when the user does not yet have a concrete task and needs help remembering, selecting, and packaging an authentic task candidate that tests taste, judgment, tradeoffs, risk anticipation, ambiguity handling, or expert-level decision-making rather than routine junior execution.
---

# JSG Task Miner

## Purpose

Help the user surface and choose an authentic Senior-Junior Gap (JSG) task from their own work. The goal is not for Codex to invent benchmark tasks for the user. The goal is to ask the right questions so the user remembers and provides a real task, scenario, dataset, document bundle, codebase, ticket, review thread, customer request, incident, analysis, or other work artifact where a junior worker or current AI agent can satisfy the surface request, but a senior expert would avoid hidden traps, make sharper tradeoffs, ask better questions, or preserve long-term quality.

Prefer real data, real information, real scenarios, and real materials. If the material is sensitive, encourage the user to sanitize, anonymize, redact, aggregate, or create a safe excerpt that preserves the judgment challenge.

## Core Principle

Mine for authentic divergence, not synthetic task design:

- **Junior behavior**: literal execution, happy-path thinking, overuse of fashionable tools, shallow optimization, missing edge cases, or failure to clarify.
- **Senior behavior**: taste, judgment, sequencing, risk control, domain-specific constraints, stakeholder awareness, and explicit tradeoffs.

Reject tasks that only test speed, tool fluency, long-context processing, or routine operational complexity unless they contain a real expert judgment fork.

Do not behave as the main task designer. Codex may frame hypotheses, name patterns, and propose ways to package a real example, but the user should remain the source of the actual task, facts, constraints, materials, and domain truth.

## Intake

Start by collecting enough context to personalize the mining session. Ask concise questions, preferably in rounds rather than one large questionnaire.

Required context:

- Role, domain, seniority, and years of experience.
- Main workflows, artifacts, tools, and decision surfaces.
- Recent examples of review comments, escalations, production incidents, rework, failed handoffs, or "technically correct but wrong" junior outputs.
- Common hidden constraints in the user's field.
- Real source material types the user can provide or safely sanitize, such as documents, spreadsheets, code, tickets, emails, transcripts, logs, screenshots, SOWs, reports, customer requests, datasets, or review threads.
- Whether the eventual task may use internet search, subagents, code execution, proprietary materials, or external documents.

If the user gives partial context, proceed with reasonable assumptions and mark assumptions explicitly.

## Real Task First

Avoid overwhelming the user with a large synthetic task list. Unless the user explicitly asks for broad brainstorming:

- Ask for concrete memories and materials before generating candidates.
- Produce a small set of **3-6 task opportunity leads** grounded in what the user said.
- For each lead, ask what real artifact, data, or scenario can anchor it.
- Do not finalize a task candidate until the user confirms the real scenario and available materials.
- If the user cannot provide real materials, help them create a sanitized or minimal representative version rather than inventing domain facts.

Use broad ideation only as a last resort to help the user remember real work, and label it clearly as "memory prompts" rather than finished task design.

## Mining Lenses

Use these four lenses to elicit memories and materials. Translate the user's memories into task opportunities only after the user provides real context.

### 1. Review and Friction

Ask what the user repeatedly corrects in code review, document review, design critique, data analysis review, customer handling, strategy review, or operational postmortems.

Look for:

- "Meets the requirement but feels wrong."
- Review comments that took unusually long to write.
- Outputs that were hard to maintain, hard to trust, misleading, legally risky, off-brand, or brittle.
- Places where juniors optimize the visible metric while damaging the real objective.
- Real artifacts the user can share or sanitize: PRs, review comments, decks, docs, analyses, support threads, SOWs, specs, experiment results, or decision memos.

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

Find real asks where the first senior move may be to clarify, scope, or de-risk instead of immediately producing a long answer.

Look for:

- Boss-style one-line asks.
- Missing product, audience, budget, authority, timeframe, or success metric.
- Requests that are dangerous if executed literally.

For these tasks, preserve the authentic ambiguity. Do not over-design the prompt to reveal the intended senior move.

## Workflow

### Step 1: Build the Expert Map

Summarize the user's profile as:

- Domain and seniority.
- Repeated work products.
- High-stakes decisions.
- Common junior failure modes.
- Sources of hidden constraints.

Ask the user to correct the map before deep task generation if the profile is thin or high-stakes.

### Step 2: Surface Real Task Leads

Produce a small set of task leads grounded in the user's actual memories. Each lead should include:

- Scenario memory or real work situation.
- Junior trap.
- Senior move.
- Which mining lens it came from.
- Needed real materials or data.
- Sensitivity/sanitization notes.

Use these leads to ask the user which one is real, available, and worth turning into a task. Do not present them as final benchmark tasks yet.

### Step 3: Material Check

For each promising lead, ask what concrete material can anchor it:

- original request or prompt;
- source document, code, data, ticket, email, screenshot, report, log, transcript, or customer artifact;
- expected output type;
- known junior failure;
- senior hidden rule or judgment fork;
- what must be sanitized before use.

Tell the user plainly that real materials make the HSW task stronger. If materials are sensitive, suggest anonymization, redaction, aggregation, synthetic-but-structure-preserving examples, or smaller excerpts.

### Step 4: Select and Deepen

Choose the strongest user-confirmed leads using these filters:

- The task creates a plausible junior/senior divergence.
- The senior behavior is observable in the output or interaction.
- The task has observable senior behavior in the produced artifact or first response.
- The prompt does not reveal the hidden senior answer too directly.
- The setup is feasible using real, public, or safely anonymized materials.
- The task may reasonably allow internet search, code execution, or subagents if that matches real work.

### Step 5: Produce Task Opportunity Cards

For each user-confirmed lead, produce a task opportunity card. It is a draft packaging aid, not a substitute for user-provided task content:

```text
Task ID:
Title:
Domain / role:
JSG lens:
Real scenario:
User-provided or needed materials:
Sensitivity / sanitization plan:
Candidate user-facing task prompt:
Allowed tools:
Junior trap:
Senior signals:
Hidden constraints:
Failure modes:
User decisions still needed:
Setup notes:
Difficulty:
```

Keep "Junior trap", "Senior signals", and "Hidden constraints" as task-design notes, not inside the user-facing task prompt unless the task is meant to test implementation of stated constraints.

### Step 6: Hand Back Ownership

Ask the user to choose which real task to proceed with and to provide or sanitize the materials. Use labels like:

- This is real and I can provide materials.
- This is real but needs sanitization.
- This is close, but adjust the scenario.
- Drop this.

Then revise the selected task opportunity around the user's corrections. The next handoff should be to `expert-boost-loop` only after the user has chosen a concrete task and the material situation is clear.

## Tooling Guidance

When the user asks for current-market, legal, regulatory, software, product, or platform-specific task realism, use internet search and cite sources in the notes. Do not let public sources replace the user's real task context unless the user explicitly wants a public-material task.

When the user explicitly allows subagents or parallel agent work, use them for independent ideation, edge-case discovery, or prompt leakage checks. Give subagents bounded prompts such as:

- "Given this user-provided real scenario, list hidden constraints the user should confirm."
- "Stress-test this candidate task prompt for whether it leaks the senior answer."
- "Find likely junior failure modes in this user-described workflow without inventing new facts."

Do not rely on subagents for the final judgment; synthesize and prune the results.

## Output Formats

Default deliverables:

- Expert map.
- 3-6 real task opportunity leads.
- Materials and sanitization checklist for each promising lead.
- 1-3 user-confirmed task opportunity cards, only if the user has confirmed the scenario is real.
- Follow-up questions that help the user provide the actual task and materials.

For spreadsheet-friendly output, provide a table with columns:

```text
id, title, domain, lens, real_scenario, materials_needed, sensitivity_plan, candidate_user_prompt, allowed_tools, junior_trap, senior_signals, hidden_constraints, user_decisions_needed, difficulty, setup_notes
```

For benchmark-building output, group tasks by:

- Interaction style: direct execution, clarification-first, review, debugging, strategy, investigation.
- Required assets: no materials, mock data, codebase, document bundle, browser/search, multi-agent.
- Output type: code, plan, review comment, investigation report, design proposal, data analysis, operational playbook.

## Quality Bar

Before presenting the final set, check:

- The output is grounded in user-provided real work memory, not Codex invention.
- Each lead names the real material or data needed to make it benchmarkable.
- Sensitive materials have a sanitization path.
- Each user-confirmed candidate has a specific junior trap and senior signal.
- At least one candidate tests ambiguity handling.
- At least one candidate tests hidden constraints.
- At least one candidate tests tradeoff judgment.
- The user-facing prompt is not over-explaining the trap.
- The task-design notes are concrete enough for the user to decide whether to proceed into `expert-boost-loop`.
