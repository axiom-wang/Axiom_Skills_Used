---
name: goal
description: Goal mode for turning broad, ambiguous, or multi-step requests into a concrete objective with success criteria, constraints, an execution checklist, and verification. Use when the user invokes goal mode, goal模式, /goal, $goal, or asks Codex to clarify objectives, define success criteria, stay goal-driven, or keep a task aligned until completion.
---

# Goal Mode

Use this skill to keep work anchored to the user's desired outcome.

## Core Behavior

Start by forming a concise goal contract:

- Goal: the outcome the user wants.
- Success criteria: observable conditions that make the task done.
- Constraints: explicit user constraints plus important repo, time, safety, or tool constraints.
- Current next action: the first concrete action to move toward the goal.

If the goal is clear enough, proceed without asking. Ask a brief clarifying question only when a wrong assumption would materially change the result or create avoidable risk.

## Workflow

1. Restate the goal contract in a short user update before substantial work.
2. Inspect relevant context before deciding implementation details.
3. Use a checklist or `update_plan` when the task has multiple steps, uncertainty, or meaningful validation work.
4. Execute toward the success criteria, keeping edits and actions scoped to the stated goal.
5. Reconcile interruptions or new user messages by updating the goal contract before continuing.
6. Verify the result with the narrowest reliable checks available.
7. Finish with what changed, what was verified, and any remaining blocker or risk.

## Operating Rules

- Do not stop at a proposal when execution is feasible and the user asked for an outcome.
- Do not expand scope into adjacent cleanup unless it is required for the stated goal.
- Prefer concrete artifacts: edited files, commands run, validated outputs, saved plans, or clear decisions.
- If blocked, identify the blocker, explain the next viable path, and preserve partial work.
- Match the user's language for updates and final response.

## Goal Drift

When the user changes direction, treat the latest message as authoritative. Briefly restate the new goal, retire obsolete checklist items, and continue from the current state without reverting unrelated user work.
