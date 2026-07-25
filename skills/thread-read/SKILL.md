---
name: thread-read
description: >
  Use when the user needs to find a past session, recover context from a
  known session, or search prior conversations for earlier decisions,
  attempts, constraints, or context that matter to the current work.
  Trigger for requests about old sessions, threads, conversation history,
  "what we tried before", "what I discussed last week", or "recover session
  <id>". Do not use for the current live session, git history, or remote
  thread services.
version: 1.0.0
metadata:
  skill_os:
    standardized: true
---

# Thread Read

Local search and retrieval for past sessions. There are two CLIs, one per agent type:

| Agent type | CLI | Data root | Session storage |
|---|---|---|---|
| Claude Code | `bin/claude-thread` | `$CLAUDE_CONFIG_DIR` (default `~/.claude`) | `projects/<encoded-workspace>/<uuid>.jsonl` |
| Codex | `bin/codex-thread` | `$CODEX_HOME` (default `~/.codex`) | `sessions/<id>/rollout.jsonl` |

Both CLIs expose the same two top-level commands (`thread_find`, `thread_retrieval`). Use the CLI that matches the agent type of the session you want to inspect.

## Picking the right CLI

Choose based on which agent created the session you're looking for:

- If the user has been working in **Claude Code** (this CLI, `claude` commands, `~/.claude/` directory), use `bin/claude-thread`.
- If the user has been working in **Codex** (`codex` commands, `~/.codex/` directory), use `bin/codex-thread`.
- If unclear, check both: run `thread_find` against each CLI, then keep the one whose sessions, timestamps, and workspace match the agent history you need.

The common workflow is **find → retrieve**: narrow down to the right session with `thread_find`, then pull the relevant slices with `thread_retrieval`.

## CLI path resolution

The CLI paths in this skill are relative to this skill directory, not the caller's cwd. Resolve a prefix first:

```bash
THREAD_READ_DIR="/abs/path/to/skills/thread-read"
# If you are already at repo root, you can also use:
# THREAD_READ_DIR="skills/thread-read"
```

## Commands

Both CLIs use the same find → retrieve workflow. Examples below use `claude-thread`; substitute `codex-thread` for Codex sessions.

### `thread_find` — locate past sessions

Finds sessions matching filters, newest first. Workspace-scoped by default.

Flags:

- `--query <text>` — case-insensitive match across title, messages, and path mentions
- `--file <path-fragment>` — match against file/path mentions
- `--after <date>` — ISO 8601 (`2026-04-12T00:00:00Z`) or relative (`7d`, `2w`)
- `--before <date>` — same formats as `--after`
- `--limit <n>` — max results, default 20
- `--global` — search all workspaces, not just the current one
- `--json` — machine-readable JSON output

```bash
# Claude Code sessions mentioning "auth refresh" in this workspace
"$THREAD_READ_DIR/bin/claude-thread" thread_find --query "auth refresh"

# Codex sessions that touched a file in the last week
"$THREAD_READ_DIR/bin/codex-thread" thread_find --file src/auth/callback.ts --after 7d

# Five most recent Claude Code sessions, as JSON
"$THREAD_READ_DIR/bin/claude-thread" thread_find --limit 5 --json
```

### `thread_retrieval` — extract relevant chunks from a known session

Given a session ID and a goal, ranks chunks with BM25 + heuristic boosts and returns top matches within a character budget.

Flags:

- `--session-id <id>` (required)
- `--goal <text>` (required) — what to recover; this is the retrieval query
- `--top-k <n>` — number of matches, default 5
- `--max-chars <n>` — total character budget, default 8000
- `--include-neighbors <n>` — expand each chunk with adjacent context, default 0
- `--json` — machine-readable JSON output

```bash
# Recover auth constraints from a Claude Code session
"$THREAD_READ_DIR/bin/claude-thread" thread_retrieval \
  --session-id 019d7e80-... \
  --goal "OAuth callback constraints for mobile clients"

# Same from a Codex session, with neighbors
"$THREAD_READ_DIR/bin/codex-thread" thread_retrieval \
  --session-id 019d7e80-... \
  --goal "retry logic for network flaps" \
  --include-neighbors 2 --json
```

Retrieval tips:

- Mentioning a file path in the goal produces more targeted results (exact path matches get a significant boost).
- Chinese goals work — the tokenizer uses `rjieba` for CJK segmentation. Mixed-language goals like `"恢复 OAuth callback 的兼容逻辑"` are fine.
- The ranking prefers `assistant_response` and `user_request` chunks over `tool_result` because raw tool output is noisier.

## Output format

Use `--json` when piping to other tools or chaining find → retrieve; omit it when showing results directly to the user.

## Dependencies

Codex CLI requires `bm25s` and `rjieba`; Claude Code CLI has no hard dependencies but benefits from `rjieba` for Chinese tokenization. Install both:

```bash
python3 -m pip install -r requirements/thread-read.txt
```

## Workspace scoping

By default `thread_find` returns only sessions whose working directory belongs to the current workspace (resolved as the git root, or cwd if no git root exists). Pass `--global` for cross-workspace search.

`thread_retrieval` does not scope by workspace — once you have a session ID, retrieval works regardless of origin.

## Common failure modes

- **"No sessions directory found"** — the config home is wrong, or the agent hasn't run on this machine
- **"Session not found: <id>"** — double-check via `thread_find --query <something>`
- **Zero results** — the workspace filter may be eliminating matches; try `--global` or broaden `--query`
- **Retrieval returns noise** — the goal is too generic; include a file path or distinctive identifier

## Design rationale

For the full design discussion, see:

- `design-docs/2026-04-12-thread-tools-proposal.md` — goals, scope, core decisions
- `design-docs/2026-04-12-thread-tools-spec.md` — full spec for both commands
- `design-docs/2026-04-12-claude-thread-cli-implementation-plan.md` — Claude Code CLI implementation plan

Key decisions:

- **Filesystem-first** — rollout/transcript JSONL is the source of truth; no database dependency
- **Session-level search, turn-level retrieval** — users remember conversations, not turns
- **Retrieval-first** — local ranking returns raw excerpts; synthesis is the agent's job
- **Unified interface** — both CLIs share identical commands, flags, ranking algorithm, and output schema so the agent only needs to learn one interface

## Usage

TODO: Document the primary workflow for this skill.

## Examples

- TODO: Add one concrete trigger or use case for this skill.
