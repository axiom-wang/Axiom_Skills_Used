# Workflow Guide

## Overview

Choose commands by operator intent, not by memorizing the command tree.

## If The User Wants To Understand Current State

Use read-first commands:

- `atoms ping`
- `atoms auth whoami`
- `atoms app get <chat_id>`
- `atoms app history <chat_id>`
- `atoms version list <chat_id>`
- `atoms deploy status <chat_id>`
- `atoms share link <chat_id>`
- `atoms balance usage [chat_id]`

Default stance:

- Verify app identity first.
- Verify lifecycle stage second.
- Only then suggest mutation.

## If The User Wants To Start Or Continue Building

Use the conversation plane:

1. Create or identify the target app.
2. Send the next instruction with `atoms app send`.
3. Watch for AI output, work-step traces, or a blocking task.
4. If the AI asks a question or proposes a plan, continue with `atoms app reply`.

Decision rule:

- No pending checkpoint: use `send`.
- Pending checkpoint exists: use `reply`.
- Use focused single-agent mode when the request is narrow and execution-heavy; use team mode when the request benefits from explicit multi-role coordination.

## If The User Wants To Bind Work To A Repo

Use project binding intentionally:

1. Create or choose the app.
2. Write `atoms.yaml` when the repository should consistently target that app.
3. Treat the file as routing metadata for future commands.

Do not describe `atoms.yaml` as deployment config or source sync.

## If The User Wants To Change Runtime Behavior

Split the request into one of two categories:

- Secret and environment scope changes: `config keys`
- Model selection changes: `config llm`

Always determine whether the change belongs at global scope or app scope before writing it.

## If The User Wants To Share Or Deploy

Treat promotion surfaces as sequential:

1. Inspect versions first.
2. Choose the target version intentionally.
3. Decide whether the goal is preview, share, or deployment.

Use:

- `app preview` for inspectable preview URLs
- `share publish` and `share link` for public or secret distribution
- `deploy publish` and `deploy status` for production deployment

Do not collapse preview, sharing, and deployment into the same step unless the user explicitly wants that.

### Deploying a local ZIP project

To deploy an existing local project archive (for example a GitHub repo downloaded as a ZIP):

1. `atoms app create --name "<name>"` — create the hosting app.
2. `atoms app send <chat_id> -f <project.zip> -m "This zip contains a complete, working project. Extract it and deploy it as-is: keep the code and design unchanged, but install any missing dependencies and fix build or configuration errors so it builds and runs. Verify the deployed app loads without errors before finishing. Do not redesign or add features, and do not ask me for confirmation - just deploy it."`
3. Wait for the send command to finish, then publish with `atoms deploy publish <chat_id> --always-latest` (this is what the web "Publish" button does). Optionally also run `atoms share publish <chat_id> --mode public --name "<name>" --wait` to make the app page public.

Key facts:

- The version becomes queryable a few seconds AFTER the AI reports completion. Always pass `--wait` to `atoms app preview` / `atoms share publish` in scripted flows.
- An explicit "deploy as-is, do not ask for confirmation" instruction prevents the AI from pausing to ask questions. If it does pause, answer with `atoms app reply <chat_id>` (see `atoms app reply --help` for non-interactive options).
- "As-is" must not mean "change nothing at all": explicitly tell the AI to install missing dependencies and verify the deployed app runs, or projects with uninstalled imports (e.g. `three`) ship broken.
- Web "Publish" = `deploy publish` (production deployment, shows the Published badge), NOT `share publish` (access mode only). Do not report an app as published after `share publish` alone.
- `deploy publish` fails with "The build for this version does not exist" when the version has no build artifact; the build-trigger API is not CLI-accessible yet — the user must click Publish in the web App Viewer once in that case.

## If The User Wants To Recover Or Roll Back

Use the recovery surfaces in this order:

1. `app history` to see what the AI and user have already done
2. `version list` and `version get` to identify stable checkpoints
3. `version restore --preview` to inspect the target historical version before deciding whether to restore
4. `deploy status` if the issue is about production exposure rather than app content

When recovering, explain whether the rollback target is conversational, versioned, or deployed state. These are related but not identical surfaces.

## If The User Wants Automation

Prefer `--json` when:

- Another tool or script will consume the output
- The result will be transformed immediately
- The user asked for machine-readable output

Prefer human-readable mode when:

- The goal is diagnosis
- The user is inspecting history or AI work traces
- Rich formatting clarifies a state transition

## Safety Rules

- Confirm intent before destructive operations such as delete or restore.
- Treat share-mode changes as visibility changes, not cosmetic metadata edits.
- Treat deploy operations as production-facing, especially when backend sync or data migration flags are involved.
- When in doubt, inspect before mutate.
