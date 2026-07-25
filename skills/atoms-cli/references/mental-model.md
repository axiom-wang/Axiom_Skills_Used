# Mental Model

## Overview

This CLI is best understood as a terminal-native control plane for an Atoms-hosted app. It is not a local build runner. Most commands call remote HTTP APIs; conversational turns also attach to a WebSocket stream to render AI output and work-step events.

The primary domain object is the app identified by `chat_id`.

## State Boundaries

### Local state

- Stored auth token, preferably in keyring, with config fallback.
- Stored API base URL.
- Optional project binding in `atoms.yaml`.
- Files chosen for upload.
- CLI output format choice, including `--json`.

### Remote state

- User identity and quota.
- App metadata and app status.
- Chat messages, pending tasks, and AI work traces.
- Uploaded file references.
- Versions, restore/remix lineage, and preview URLs.
- Share mode and pinned version.
- Deployment state and cloud function rollout.
- Secrets and LLM configuration.
- Balance, usage, and order history.

The skill should reason from the assumption that the authoritative state lives remotely.

## The Six Planes

### 1. Identity plane

`auth login`, `auth logout`, `auth whoami`, and `ping` establish whether the CLI can operate.

Signals:

- Missing or expired token blocks most useful work.
- `ping` is the fastest operator health check because it combines auth and API reachability.

### 2. Routing plane

`chat_id` is the routing key for app-scoped actions.

Resolution model:

1. Explicit CLI argument wins.
2. `atoms.yaml` project binding comes next.
3. Global stored fallback may exist.

Important implication: before acting on “the current app,” verify which routing source is in effect.

### 3. Conversation plane

`app send` and `app reply` form a conversational state machine rather than a simple message log.

Key distinctions:

- `send` starts or advances AI work.
- `reply` answers a pending AI checkpoint.
- `agent_mode` selects the orchestration style: focused single-agent work or broader multi-agent coordination.
- The AI may emit normal messages, work-step traces, or task objects that require human approval or selection.

If the AI is waiting on a plan approval or question, replying is the correct continuation primitive.

### 4. Lifecycle plane

The app moves through these broad states:

1. Created
2. Iterated through conversation
3. Materialized as versions
4. Exposed through share links
5. Promoted to deployment

Versioning, sharing, and deployment are not separate products; they are successive surfaces over the same app object.

### 5. Configuration plane

Configuration is split by scope:

- Global user-level configuration
- App-level configuration

Secrets and general LLM config shape how the remote app behaves. They are not merely local CLI preferences.

### 6. Economics plane

Balance and usage are control-plane visibility for cost and quota. They should be read before proposing large-scale AI work, repeated retries, or operational debugging that may incur cost.

## Streaming Model

The CLI uses WebSocket streaming to show live AI text and work-step events.

Operational consequences:

- A send or reply can succeed even if streaming setup fails.
- Streaming failure does not necessarily mean the remote action failed.
- `app history` is the authoritative recovery surface after an interrupted or degraded live session.

## What This CLI Is Not

- Not a local code generator that edits repository files directly.
- Not a package manager or build system.
- Not a source-sync client.
- Not a deploy system for arbitrary local artifacts.

It is a remote operator for Atoms-managed app state.
