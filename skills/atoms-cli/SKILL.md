---
name: atoms-cli
description: Use the `atoms` CLI to operate Atoms apps as remote lifecycle-managed objects. Use when Codex needs to log in, bind a repository to an Atoms app, inspect app state, send or reply to the AI team, manage versions, configure secrets or LLM settings, inspect balance and usage, publish share links, or deploy an Atoms app. Treat this skill as the operating model for using Atoms CLI against remote app state, not as a local build tool.
---

# Atoms CLI

Treat `atoms` as the control plane for a remote Atoms application. The central object is an app identified by `chat_id`; most commands inspect or mutate remote state, while local state is limited to auth material, `atoms.yaml`, and files explicitly uploaded as attachments.

## Start From State

Before choosing a command, identify four things:

1. Who is the operator: authenticated user, token health, API reachability.
2. What is the target: specific `chat_id`, current repo binding, or account-level scope.
3. Which plane is being touched: conversation, configuration, versioning, sharing, deployment, or billing.
4. Whether the action is read-only or a state transition.

Prefer `atoms ping`, `atoms auth whoami`, `atoms app get`, `atoms app history`, `atoms version list`, or `atoms deploy status` before mutating anything.

## Core Model

- Identity plane: `auth` and `ping` establish whether the terminal can act on behalf of a user.
- Routing plane: `chat_id` is the routing key for nearly every app-scoped action; `atoms.yaml` binds a working directory to a default app and agent mode.
- Conversation plane: `app send` starts or continues AI work; `app reply` resumes blocked work when the AI has asked a question or proposed a plan.
- Lifecycle plane: apps move through creation, iterative conversation, versioning, sharing, and deployment.
- Configuration plane: `config keys` and `config llm` shape runtime behavior for a user or a specific app.
- Economics plane: `balance` exposes cost, quota, and order history.

Read [references/mental-model.md](references/mental-model.md) when you need the architectural framing behind these planes.

## Operate By Intent

Map user intent to one of these operating modes:

- Inspect: establish current state without changing it.
- Steer: send instructions to the AI team or answer a pending question.
- Shape runtime: modify secrets, environment scope, or LLM selection.
- Promote: turn current work into a version, share link, or deployment target.
- Recover: inspect history, versions, deployment status, or pending tasks before deciding the next move.

Read [references/workflow-guide.md](references/workflow-guide.md) when the intent is clear but the next command is not.

## Standard Operating Loop

1. Resolve scope first.
   Determine whether the task is account-wide or app-scoped. If app-scoped, resolve `chat_id` from explicit input first, then `atoms.yaml`, then any stored default.

2. Inspect before mutating.
   Query the current remote state before issuing destructive or promotive commands. Do not assume that the latest version, share mode, or deploy domain is already known.

3. Advance one state transition at a time.
   Separate conversational work from versioning, sharing, and deployment. Avoid chaining multiple irreversible transitions without checking intermediate state.

4. Verify with the surface that owns the state.
   Verify conversation changes via `app history`, version changes via `version list/get`, share changes via `share link/list`, deploy changes via `deploy status`, and billing changes via `balance`.

## Critical Heuristics

- Treat this CLI as remote-first. It does not build local source trees; it orchestrates a remote Atoms app.
- Treat `app send` as opening or advancing a work turn. Treat `app reply` as satisfying an AI checkpoint. If the AI is blocked on a task, reply instead of sending a fresh message.
- Treat `atoms.yaml` as routing metadata, not source of truth for the app itself.
- Treat file attachments as explicit uploads into the remote chat context. Local files are not synchronized unless attached.
- Prefer `--json` when the result will be consumed programmatically or fed into follow-up automation.
- Treat `delete`, `restore`, `publish`, `unpublish`, and `deploy publish` as side-effecting operations that require explicit intent.

## Failure Posture

- If auth fails or the token is expired, restore operator identity before debugging anything else.
- If Socket.IO streaming fails, expect send-only fallback behavior; verify progress through `app history`.
- If a command targets a `chat_id`, validate that app state explicitly instead of assuming the working directory still points at the right app.
- If the user asks for “what changed” or “where are we”, inspect history, versions, and deployment status before proposing action.

## Resource Loading

- Read [references/mental-model.md](references/mental-model.md) for the high-level architecture and local-vs-remote boundary.
- Read [references/workflow-guide.md](references/workflow-guide.md) for practical decision rules by operator intent.
