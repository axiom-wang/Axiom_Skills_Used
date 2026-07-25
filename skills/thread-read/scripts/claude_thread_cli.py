from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.text_filters import is_meaningful_preview_candidate, normalize_text


UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
ISO_Z_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
PATH_RE = re.compile(
    r"(?<![:\w])(?:/(?:[A-Za-z0-9._~\-]+/?)+|(?:[A-Za-z0-9._\-]+/)+(?:[A-Za-z0-9._\-]+))"
)
CJK_RE = re.compile(r"[\u3400-\u9fff]+")
DEFAULT_FIND_LIMIT = 20
DEFAULT_TOP_K = 5
DEFAULT_MAX_CHARS = 8000
CHUNK_EXCERPT_CHARS = 700

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "include",
    "including",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "this",
    "to",
    "we",
    "what",
    "when",
    "which",
    "with",
    "的",
    "了",
    "并",
    "和",
    "是",
    "在",
    "把",
    "对",
    "请",
    "继续",
    "当前",
    "我们",
}

_ASCII_TOKEN_RE = re.compile(r"[a-z0-9_./-]+")
_CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclass
class SessionSummary:
    session_id: str
    title: str | None
    cwd: str | None
    created_at: str | None
    updated_at: str | None
    archived: bool
    preview: str
    searchable_text: str
    matched_by: list[str]
    matched_text: list[str]
    matched_paths: list[str]
    rollout_path: str


@dataclass
class Chunk:
    turn_index: int
    chunk_type: str
    text: str
    paths_mentioned: list[str]
    timestamp: str | None
    rollout_start_index: int
    rollout_end_index: int


@dataclass
class RankedChunk:
    rank: int
    chunk: Chunk
    score: float
    why_matched: list[str]


class ToolError(RuntimeError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "thread_find":
            return run_thread_find(args)
        if args.command == "thread_retrieval":
            return run_thread_retrieval(args)
        parser.error("missing command")
    except ToolError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claude-thread")
    subparsers = parser.add_subparsers(dest="command")

    find_parser = subparsers.add_parser("thread_find")
    find_parser.add_argument("--query")
    find_parser.add_argument("--file")
    find_parser.add_argument("--after")
    find_parser.add_argument("--before")
    find_parser.add_argument("--limit", type=int, default=DEFAULT_FIND_LIMIT)
    find_parser.add_argument("--global", dest="global_scope", action="store_true")
    find_parser.add_argument("--json", action="store_true")

    retrieval_parser = subparsers.add_parser("thread_retrieval")
    retrieval_parser.add_argument("--session-id", required=True)
    retrieval_parser.add_argument("--goal", required=True)
    retrieval_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    retrieval_parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    retrieval_parser.add_argument("--include-neighbors", type=int, default=0)
    retrieval_parser.add_argument("--json", action="store_true")
    return parser


def run_thread_find(args: argparse.Namespace) -> int:
    cwd = Path.cwd()
    workspace_root = resolve_workspace_root(cwd)
    after = parse_date_filter(args.after, "--after")
    before = parse_date_filter(args.before, "--before")

    transcripts = list_candidate_transcripts(workspace_root, args.global_scope)
    if not transcripts:
        raise ToolError(f"No Claude sessions directory found under {projects_root()}.")

    filtered_paths = transcripts
    if args.query:
        filtered_paths = prefilter_with_rg(filtered_paths, args.query, fixed_strings=False)
    if args.file:
        filtered_paths = prefilter_with_rg(filtered_paths, args.file, fixed_strings=True)

    results: list[SessionSummary] = []
    for path in filtered_paths:
        summary = summarize_session(path)
        if not summary:
            continue
        if not args.global_scope and summary.cwd and not is_same_workspace(
            summary.cwd, workspace_root
        ):
            continue
        matched_by, matched_text, matched_paths = evaluate_session_match(
            summary, args.query, args.file, after, before
        )
        if any([args.query, args.file, after, before]) and not matched_by:
            continue
        results.append(
            SessionSummary(
                session_id=summary.session_id,
                title=summary.title,
                cwd=summary.cwd,
                created_at=summary.created_at,
                updated_at=summary.updated_at,
                archived=summary.archived,
                preview=summary.preview,
                searchable_text=summary.searchable_text,
                matched_by=matched_by,
                matched_text=matched_text,
                matched_paths=matched_paths,
                rollout_path=summary.rollout_path,
            )
        )

    results.sort(key=lambda item: item.updated_at or "", reverse=True)
    limited = results[: max(1, args.limit)]

    if args.json:
        payload = {
            "scope": {
                "workspaceRoot": None if args.global_scope else str(workspace_root),
                "global": bool(args.global_scope),
            },
            "filters": {
                "query": args.query,
                "file": args.file,
                "after": args.after,
                "before": args.before,
                "limit": args.limit,
            },
            "results": [session_summary_to_json(result) for result in limited],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_find_text(limited, workspace_root, bool(args.global_scope), args.limit))
    return 0


def run_thread_retrieval(args: argparse.Namespace) -> int:
    if not args.goal.strip():
        raise ToolError("--goal is required")
    workspace_root = resolve_workspace_root(Path.cwd())
    transcript_path = find_transcript_path(args.session_id, workspace_root)
    if not transcript_path:
        raise ToolError(f"Session not found: {args.session_id}")

    session = load_session(transcript_path)
    chunks = build_chunks(session["chain"])
    if not chunks:
        payload = {
            "sessionId": args.session_id,
            "goal": args.goal,
            "topK": args.top_k,
            "maxChars": args.max_chars,
            "truncated": False,
            "results": [],
            "rolloutPath": str(transcript_path),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Session {args.session_id}\nGoal: {args.goal}\n\nNo retrievable chunks found.")
        return 0

    ranked = rank_chunks(
        chunks,
        args.goal,
        top_k=max(1, args.top_k),
        include_neighbors=max(0, args.include_neighbors),
        max_chars=max(1, args.max_chars),
    )
    payload = {
        "sessionId": args.session_id,
        "goal": args.goal,
        "topK": args.top_k,
        "maxChars": args.max_chars,
        "truncated": ranked["truncated"],
        "results": [
            {
                "rank": item.rank,
                "turnIndex": item.chunk.turn_index,
                "chunkType": item.chunk.chunk_type,
                "score": round(item.score, 2),
                "whyMatched": item.why_matched,
                "pathsMentioned": item.chunk.paths_mentioned,
                "timestamp": item.chunk.timestamp,
                "rolloutStartIndex": item.chunk.rollout_start_index,
                "rolloutEndIndex": item.chunk.rollout_end_index,
                "excerpt": item.chunk.text,
            }
            for item in ranked["results"]
        ],
        "rolloutPath": str(transcript_path),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_retrieval_text(payload))
    return 0


def claude_config_home() -> Path:
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude"


def projects_root() -> Path:
    return claude_config_home() / "projects"


def resolve_workspace_root(cwd: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return cwd
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return cwd


def sanitize_path(name: str) -> str:
    sanitized = "".join(ch if ch.isalnum() else "-" for ch in name)
    if len(sanitized) <= 200:
        return sanitized
    suffix = format(stable_hash(name), "x")
    return f"{sanitized[:200]}-{suffix}"


def stable_hash(text: str) -> int:
    value = 5381
    for char in text:
        value = ((value << 5) + value) + ord(char)
        value &= 0xFFFFFFFF
    return value


def candidate_project_dir(workspace_root: Path) -> Path:
    return projects_root() / sanitize_path(str(workspace_root))


def list_candidate_transcripts(workspace_root: Path, global_scope: bool) -> list[Path]:
    root = projects_root()
    if not root.exists():
        return []
    if not global_scope:
        project_dir = candidate_project_dir(workspace_root)
        if not project_dir.exists():
            return []
        return sorted(project_dir.glob("*.jsonl"))
    candidates: list[Path] = []
    for project_dir in root.iterdir():
        if not project_dir.is_dir():
            continue
        candidates.extend(sorted(project_dir.glob("*.jsonl")))
    return candidates


def find_transcript_path(session_id: str, workspace_root: Path) -> Path | None:
    if not UUID_RE.match(session_id):
        return None
    workspace_candidate = candidate_project_dir(workspace_root) / f"{session_id}.jsonl"
    if workspace_candidate.exists():
        return workspace_candidate
    for candidate in projects_root().rglob(f"{session_id}.jsonl"):
        if candidate.name == f"{session_id}.jsonl":
            return candidate
    return None


def prefilter_with_rg(paths: list[Path], needle: str, *, fixed_strings: bool) -> list[Path]:
    rg = shutil.which("rg")
    if not rg or not needle or not paths:
        return paths
    matched: set[Path] = set()
    batch_size = 128
    base_args = [rg, "-l", "-i"]
    if fixed_strings:
        base_args.append("-F")
    base_args.append(needle)
    for index in range(0, len(paths), batch_size):
        batch = paths[index : index + batch_size]
        proc = subprocess.run(
            base_args + [str(path) for path in batch],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode not in (0, 1):
            return paths
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line:
                matched.add(Path(line))
    return [path for path in paths if path in matched]


def summarize_session(path: Path) -> SessionSummary | None:
    session_id = path.stem
    if not UUID_RE.match(session_id):
        return None

    title: str | None = None
    preview: str = ""
    cwd: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    extracted_paths: set[str] = set()
    searchable_fragments: list[str] = []

    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    entry = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                etype = entry.get("type")
                if etype == "custom-title":
                    title = as_string(entry.get("customTitle")) or title
                elif etype == "ai-title" and not title:
                    title = as_string(entry.get("aiTitle")) or title
                elif etype == "last-prompt":
                    candidate = as_string(entry.get("lastPrompt"))
                    if candidate and is_meaningful_preview_candidate(candidate):
                        preview = candidate

                timestamp = as_string(entry.get("timestamp"))
                if timestamp:
                    if created_at is None or timestamp < created_at:
                        created_at = timestamp
                    if updated_at is None or timestamp > updated_at:
                        updated_at = timestamp

                if cwd is None and isinstance(entry.get("cwd"), str):
                    cwd = entry["cwd"]

                for text in extract_text_fragments(entry):
                    searchable_fragments.append(text)
                    extracted_paths.update(extract_paths(text))
                    if (
                        not preview
                        and etype == "user"
                        and not entry.get("isMeta")
                        and not is_tool_result_message(entry)
                        and is_meaningful_preview_candidate(text)
                    ):
                        preview = summarize_text(text, 180)
    except OSError:
        return None

    if not updated_at:
        stat = path.stat()
        updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime(ISO_Z_FORMAT)
        created_at = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).strftime(ISO_Z_FORMAT)

    return SessionSummary(
        session_id=session_id,
        title=title,
        cwd=cwd,
        created_at=created_at,
        updated_at=updated_at,
        archived=False,
        preview=preview or "(untitled)",
        searchable_text="\n".join(searchable_fragments),
        matched_by=[],
        matched_text=[],
        matched_paths=sorted(extracted_paths),
        rollout_path=str(path),
    )


def evaluate_session_match(
    summary: SessionSummary,
    query: str | None,
    file_filter: str | None,
    after: datetime | None,
    before: datetime | None,
) -> tuple[list[str], list[str], list[str]]:
    matched_by: list[str] = []
    matched_text: list[str] = []
    matched_paths: list[str] = []

    haystack = "\n".join(
        filter(
            None,
            [
                summary.title or "",
                summary.preview,
                summary.searchable_text,
                " ".join(summary.matched_paths),
            ],
        )
    ).lower()

    if query:
        q = query.lower()
        if q not in haystack:
            return [], [], []
        matched_by.append("query")
        matched_text.append(query)

    if file_filter:
        f = file_filter.lower()
        matched_paths = [path for path in summary.matched_paths if f in path.lower()]
        if not matched_paths:
            return [], [], []
        matched_by.append("file")

    if after or before:
        updated = parse_iso_timestamp(summary.updated_at)
        if updated is None:
            return [], [], []
        if after and updated < after:
            return [], [], []
        if before and updated > before:
            return [], [], []
        matched_by.append("date")

    return matched_by, matched_text, matched_paths or summary.matched_paths[:10]


def session_summary_to_json(summary: SessionSummary) -> dict[str, Any]:
    return {
        "sessionId": summary.session_id,
        "title": summary.title,
        "cwd": summary.cwd,
        "createdAt": summary.created_at,
        "updatedAt": summary.updated_at,
        "archived": summary.archived,
        "preview": summary.preview,
        "matchedBy": summary.matched_by,
        "matchedText": summary.matched_text,
        "matchedPaths": summary.matched_paths,
        "rolloutPath": summary.rollout_path,
    }


def render_find_text(
    results: list[SessionSummary], workspace_root: Path, global_scope: bool, limit: int
) -> str:
    lines = [
        f"Scope: {'global' if global_scope else str(workspace_root)}",
        f"Results: {len(results)} (limit {limit})",
    ]
    if not results:
        lines.append("No matching sessions.")
        return "\n".join(lines)
    for index, result in enumerate(results, start=1):
        lines.extend(
            [
                "",
                f"{index}. {result.title or '(untitled)'}",
                f"   sessionId: {result.session_id}",
                f"   updatedAt: {result.updated_at or '(unknown)'}",
                f"   cwd: {result.cwd or '(unknown)'}",
                f"   preview: {summarize_text(result.preview, 160)}",
            ]
        )
        if result.matched_by:
            lines.append(f"   matchedBy: {', '.join(result.matched_by)}")
        if result.matched_paths:
            lines.append(f"   matchedPaths: {', '.join(result.matched_paths[:3])}")
    return "\n".join(lines)


def load_session(path: Path) -> dict[str, Any]:
    messages: dict[str, dict[str, Any]] = {}
    entries: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for index, raw_line in enumerate(handle):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    entry = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                entry["_rollout_index"] = index
                entries.append(entry)
                if is_transcript_message(entry) and not entry.get("isSidechain"):
                    uuid = as_string(entry.get("uuid"))
                    if uuid:
                        messages[uuid] = entry
    except OSError as exc:
        raise ToolError(f"Failed to load transcript: {exc}") from exc

    leaf = latest_leaf(messages)
    chain = build_chain(messages, leaf) if leaf else []
    return {"entries": entries, "messages": messages, "chain": chain}


def latest_leaf(messages: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not messages:
        return None
    parents = {
        entry.get("parentUuid")
        for entry in messages.values()
        if isinstance(entry.get("parentUuid"), str)
    }
    candidates = [
        entry
        for entry in messages.values()
        if entry.get("uuid") not in parents and entry.get("type") in {"user", "assistant"}
    ]
    if not candidates:
        candidates = list(messages.values())
    candidates.sort(key=lambda item: as_string(item.get("timestamp")) or "")
    return candidates[-1] if candidates else None


def build_chain(messages: dict[str, dict[str, Any]], leaf: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not leaf:
        return []
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    current = leaf
    while current:
        uuid = as_string(current.get("uuid"))
        if not uuid or uuid in seen:
            break
        seen.add(uuid)
        chain.append(current)
        parent_uuid = as_string(current.get("parentUuid"))
        if not parent_uuid:
            break
        current = messages.get(parent_uuid)
    chain.reverse()
    return chain


def build_chunks(chain: list[dict[str, Any]]) -> list[Chunk]:
    chunks: list[Chunk] = []
    turn_index = -1
    for entry in chain:
        etype = entry.get("type")
        if etype == "user" and not entry.get("isMeta") and not is_tool_result_message(entry):
            turn_index += 1
            text = extract_primary_text(entry)
            if text:
                chunks.append(
                    Chunk(
                        turn_index=max(turn_index, 0),
                        chunk_type="user_request",
                        text=summarize_text(text, CHUNK_EXCERPT_CHARS),
                        paths_mentioned=sorted(extract_paths(text)),
                        timestamp=as_string(entry.get("timestamp")),
                        rollout_start_index=entry["_rollout_index"],
                        rollout_end_index=entry["_rollout_index"],
                    )
                )
        elif etype == "assistant":
            text = extract_primary_text(entry)
            if text:
                chunks.append(
                    Chunk(
                        turn_index=max(turn_index, 0),
                        chunk_type="assistant_response",
                        text=summarize_text(text, CHUNK_EXCERPT_CHARS),
                        paths_mentioned=sorted(extract_paths(text)),
                        timestamp=as_string(entry.get("timestamp")),
                        rollout_start_index=entry["_rollout_index"],
                        rollout_end_index=entry["_rollout_index"],
                    )
                )
        elif etype == "user" and is_tool_result_message(entry):
            turn_index = max(turn_index, 0)
            text = extract_tool_result_text(entry)
            if text:
                chunks.append(
                    Chunk(
                        turn_index=turn_index,
                        chunk_type="tool_result",
                        text=summarize_text(text, CHUNK_EXCERPT_CHARS),
                        paths_mentioned=sorted(extract_paths(text)),
                        timestamp=as_string(entry.get("timestamp")),
                        rollout_start_index=entry["_rollout_index"],
                        rollout_end_index=entry["_rollout_index"],
                    )
                )
        elif is_compaction_summary(entry):
            text = extract_primary_text(entry)
            if text:
                chunks.append(
                    Chunk(
                        turn_index=max(turn_index, 0),
                        chunk_type="compaction_summary",
                        text=summarize_text(text, CHUNK_EXCERPT_CHARS),
                        paths_mentioned=sorted(extract_paths(text)),
                        timestamp=as_string(entry.get("timestamp")),
                        rollout_start_index=entry["_rollout_index"],
                        rollout_end_index=entry["_rollout_index"],
                    )
                )
    return chunks


def chunk_type_base_score(chunk_type: str) -> float:
    if chunk_type == "assistant_response":
        return 4.0
    if chunk_type == "user_request":
        return 3.5
    if chunk_type == "compaction_summary":
        return 2.5
    if chunk_type == "tool_result":
        return 0.5
    return 1.0


def build_excerpt(
    chunks: list[Chunk], index: int, include_neighbors: int,
) -> tuple[str, int, int]:
    start = max(0, index - include_neighbors)
    end = min(len(chunks) - 1, index + include_neighbors)
    excerpt = "\n\n".join(
        f"[turn {chunk.turn_index} | {chunk.chunk_type}] {chunk.text}"
        for chunk in chunks[start : end + 1]
    )
    if len(excerpt) > CHUNK_EXCERPT_CHARS:
        excerpt = f"{excerpt[:CHUNK_EXCERPT_CHARS]}..."
    return excerpt, chunks[start].rollout_start_index, chunks[end].rollout_end_index


def rank_chunks(
    chunks: list[Chunk],
    goal: str,
    *,
    top_k: int,
    include_neighbors: int,
    max_chars: int,
) -> dict[str, Any]:
    query_tokens = tokenize_text(goal)
    if not query_tokens:
        query_tokens = [goal.strip().lower()]
    doc_tokens = [
        tokenize_text(f"{chunk.text} {' '.join(chunk.paths_mentioned)}".strip())
        for chunk in chunks
    ]
    bm25_scores = compute_bm25_scores(query_tokens, doc_tokens)

    scored: list[tuple[float, int, list[str]]] = []
    for index, chunk in enumerate(chunks):
        chunk_token_set = set(doc_tokens[index])
        base = chunk_type_base_score(chunk.chunk_type)
        score = float(bm25_scores[index]) + base
        why_matched: list[str] = []

        for token in query_tokens:
            if token in chunk_token_set:
                why_matched.append(token)

        path_tokens = [p.lower() for p in chunk.paths_mentioned]
        for token in query_tokens:
            if any(token in pv for pv in path_tokens):
                score += 3.0
                if token not in why_matched:
                    why_matched.append(token)

        if len(chunks) > 0:
            score += ((index + 1) / len(chunks)) * 0.5

        if chunk.chunk_type == "tool_result" and chunk.text.lstrip().startswith(("{", "[")):
            score -= 4.0

        if score <= base:
            continue

        seen: set[str] = set()
        deduped_why: list[str] = []
        for token in why_matched:
            if token in seen:
                continue
            seen.add(token)
            deduped_why.append(token)
            if len(deduped_why) >= 5:
                break

        scored.append((score, index, deduped_why))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = scored[:top_k]

    total_chars = 0
    results: list[RankedChunk] = []
    for score, index, why_matched in selected:
        excerpt, rollout_start, rollout_end = build_excerpt(
            chunks, index, include_neighbors,
        )
        if results and total_chars + len(excerpt) > max_chars:
            break
        total_chars += len(excerpt)
        chunk = chunks[index]
        results.append(
            RankedChunk(
                rank=len(results) + 1,
                chunk=Chunk(
                    turn_index=chunk.turn_index,
                    chunk_type=chunk.chunk_type,
                    text=excerpt,
                    paths_mentioned=chunk.paths_mentioned,
                    timestamp=chunk.timestamp,
                    rollout_start_index=rollout_start,
                    rollout_end_index=rollout_end,
                ),
                score=score,
                why_matched=why_matched,
            )
        )
    return {"results": results, "truncated": len(results) < len(selected)}


def render_retrieval_text(payload: dict[str, Any]) -> str:
    lines = [f"Session: {payload['sessionId']}", f"Goal: {payload['goal']}"]
    if payload["truncated"]:
        lines.append("Output truncated to fit maxChars.")
    if not payload["results"]:
        lines.extend(["", "No retrievable chunks found."])
        return "\n".join(lines)
    for item in payload["results"]:
        lines.extend(
            [
                "",
                f"{item['rank']}. {item['chunkType']} (turn {item['turnIndex']}, score {item['score']})",
                f"   why: {', '.join(item['whyMatched'])}",
                f"   paths: {', '.join(item['pathsMentioned']) if item['pathsMentioned'] else '(none)'}",
                f"   excerpt: {item['excerpt']}",
            ]
        )
    return "\n".join(lines)


def is_same_workspace(session_cwd: str, workspace_root: Path) -> bool:
    try:
        return resolve_workspace_root(Path(session_cwd)) == workspace_root
    except OSError:
        return False


def parse_date_filter(value: str | None, flag_name: str) -> datetime | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    now = datetime.now(timezone.utc)
    if re.match(r"^\d+d$", value):
        return now - timedelta(days=int(value[:-1]))
    if re.match(r"^\d+w$", value):
        return now - timedelta(weeks=int(value[:-1]))
    try:
        if len(value) == 10:
            return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return parse_iso_timestamp(value)
    except ValueError as exc:
        raise ToolError(f"Invalid value for {flag_name}: {value}. Expected YYYY-MM-DD, 7d, or 2w.") from exc


def parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.strptime(value, ISO_Z_FORMAT).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def extract_text_fragments(entry: dict[str, Any]) -> list[str]:
    fragments: list[str] = []
    etype = entry.get("type")
    if etype in {"custom-title", "ai-title"}:
        for key in ("customTitle", "aiTitle"):
            value = as_string(entry.get(key))
            if value:
                fragments.append(value)
        return fragments
    if etype == "last-prompt":
        value = as_string(entry.get("lastPrompt"))
        if value:
            fragments.append(value)
        return fragments
    fragments.extend(extract_message_content(entry.get("message")))
    if etype == "system":
        content = as_string(entry.get("content"))
        if content:
            fragments.append(content)
    return [item for item in fragments if item]


def extract_message_content(message: Any) -> list[str]:
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        fragments: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                text = as_string(block.get("text"))
                if text:
                    fragments.append(text)
            elif btype == "tool_result":
                result_content = block.get("content")
                if isinstance(result_content, str):
                    fragments.append(result_content)
                elif isinstance(result_content, list):
                    fragments.extend(
                        fragment
                        for fragment in (
                            as_string(part.get("text"))
                            for part in result_content
                            if isinstance(part, dict) and part.get("type") == "text"
                        )
                        if fragment
                    )
            elif btype == "tool_use":
                name = as_string(block.get("name"))
                if name:
                    fragments.append(name)
        return fragments
    return []


def extract_primary_text(entry: dict[str, Any]) -> str:
    fragments = extract_text_fragments(entry)
    filtered = [
        fragment
        for fragment in fragments
        if "<local-command-caveat>" not in fragment
        and not fragment.strip().startswith("<command-name>")
    ]
    return "\n\n".join(filtered).strip()


def is_transcript_message(entry: dict[str, Any]) -> bool:
    return entry.get("type") in {"user", "assistant", "attachment", "system"}


def is_tool_result_message(entry: dict[str, Any]) -> bool:
    if entry.get("type") != "user":
        return False
    message = entry.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    return bool(
        isinstance(content, list)
        and any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content)
    )


def extract_tool_result_text(entry: dict[str, Any]) -> str:
    message = entry.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "tool_result":
            continue
        tool_id = as_string(block.get("tool_use_id"))
        result_content = block.get("content")
        if isinstance(result_content, str):
            text = result_content
        elif isinstance(result_content, list):
            text = "\n".join(
                as_string(part.get("text")) or ""
                for part in result_content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        else:
            text = ""
        if tool_id and text:
            parts.append(f"[{tool_id}] {text}")
        elif text:
            parts.append(text)
    return "\n\n".join(parts).strip()


def is_compaction_summary(entry: dict[str, Any]) -> bool:
    return bool(entry.get("isCompactSummary")) or entry.get("subtype") == "compact_boundary"


def extract_paths(text: str) -> list[str]:
    matches: list[str] = []
    for match in PATH_RE.findall(text):
        candidate = match.rstrip(".,:;)")
        if "://" in candidate:
            continue
        if re.fullmatch(r"/[A-Za-z0-9_-]+", candidate):
            continue
        if candidate not in matches:
            matches.append(candidate)
    return matches


def tokenize_text(text: str) -> list[str]:
    lowered = text.lower()
    tokens: list[str] = []
    tokens.extend(path.lower() for path in extract_paths(text))

    for match in _ASCII_TOKEN_RE.finditer(lowered):
        token = match.group(0).strip()
        if len(token) < 2 or token in STOP_WORDS or token.isdigit():
            continue
        tokens.append(token)

    try:
        import rjieba  # type: ignore

        for segment in rjieba.cut(lowered):
            cleaned = segment.strip().lower()
            if not cleaned or cleaned in STOP_WORDS:
                continue
            if not _CJK_CHAR_RE.search(cleaned):
                continue
            tokens.append(cleaned)
    except Exception:
        for seq in CJK_RE.findall(text):
            if len(seq) == 1:
                tokens.append(seq)
            else:
                tokens.extend(seq[index : index + 2] for index in range(len(seq) - 1))

    seen: set[str] = set()
    ordered: list[str] = []
    for token in tokens:
        if token and token not in seen:
            seen.add(token)
            ordered.append(token)
    return ordered


def compute_bm25_scores(query_tokens: list[str], docs: list[list[str]]) -> list[float]:
    if not docs:
        return []
    doc_freq: Counter[str] = Counter()
    doc_lengths = [len(doc) or 1 for doc in docs]
    avgdl = sum(doc_lengths) / max(1, len(doc_lengths))
    doc_counters = [Counter(doc) for doc in docs]
    for doc in docs:
        for token in set(doc):
            doc_freq[token] += 1

    scores: list[float] = []
    k1 = 1.5
    b = 0.75
    N = len(docs)
    for doc_len, counter in zip(doc_lengths, doc_counters):
        score = 0.0
        for token in query_tokens:
            tf = counter.get(token, 0)
            if tf == 0:
                continue
            df = doc_freq.get(token, 0)
            idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
            denom = tf + k1 * (1 - b + b * (doc_len / avgdl))
            score += idf * ((tf * (k1 + 1)) / denom)
        scores.append(score)
    return scores


def summarize_text(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def as_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


if __name__ == "__main__":
    raise SystemExit(main())
