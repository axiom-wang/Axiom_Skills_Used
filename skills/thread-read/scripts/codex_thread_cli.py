from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.text_filters import is_meaningful_preview_candidate, normalize_text

try:
    import bm25s
except ImportError as exc:  # pragma: no cover - import-time dependency guard
    raise RuntimeError(
        "Missing dependency 'bm25s'. Install it with: python3 -m pip install bm25s"
    ) from exc

try:
    import rjieba
except ImportError as exc:  # pragma: no cover - import-time dependency guard
    raise RuntimeError(
        "Missing dependency 'rjieba'. Install it with: python3 -m pip install rjieba"
    ) from exc


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


def get_codex_home(explicit_codex_home: str | Path | None = None) -> Path:
    if explicit_codex_home is not None:
        return Path(explicit_codex_home).expanduser()
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def canonicalize_path(path_value: str | Path) -> Path:
    candidate = Path(path_value).expanduser()
    try:
        return candidate.resolve()
    except OSError:
        return Path(os.path.abspath(str(candidate)))


def resolve_workspace_root(start_cwd: str | Path) -> Path:
    current = canonicalize_path(start_cwd)
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return canonicalize_path(start_cwd)
        current = current.parent


def list_rollout_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        file_path
        for file_path in root.rglob("*.jsonl")
        if file_path.is_file()
    )


def load_session_names(codex_home: Path) -> dict[str, str]:
    index_path = codex_home / "session_index.jsonl"
    if not index_path.exists():
        return {}

    names: dict[str, str] = {}
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        session_id = entry.get("id")
        thread_name = entry.get("thread_name")
        if isinstance(session_id, str) and isinstance(thread_name, str) and thread_name.strip():
            names[session_id] = thread_name.strip()
    return names


def parse_date_input(value: str | None) -> Any:
    if not value:
        return None

    relative_match = re.fullmatch(r"(\d+)([dw])", value)
    if relative_match:
        count = int(relative_match.group(1))
        unit = relative_match.group(2)
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        if unit == "d":
            return now - timedelta(days=count)
        return now - timedelta(weeks=count)

    from datetime import datetime

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def collect_path_mentions(text: str) -> list[str]:
    value = str(text or "")
    matches: set[str] = set()
    for pattern in (
        re.compile(r"\b(?:[A-Za-z0-9_.-]+/)+[A-Za-z_][A-Za-z0-9_.-]*\b"),
        re.compile(r"\b[A-Za-z_][A-Za-z0-9_.-]*\.[A-Za-z][A-Za-z0-9]{1,7}\b"),
    ):
        for match in pattern.finditer(value):
            matches.add(match.group(0))
    return list(matches)


def try_rg_prefilter(
    query: str | None,
    roots: list[Path],
    *,
    fixed_strings: bool = False,
) -> set[Path] | None:
    if not query:
        return None
    existing_roots = [str(root) for root in roots if root.exists()]
    if not existing_roots:
        return None
    command = ["rg", "-l", "-i"]
    if fixed_strings:
        command.append("-F")
    command.extend([query, *existing_roots])
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode > 1:
        return None
    stdout = result.stdout.strip()
    if not stdout:
        return set()
    return {canonicalize_path(line) for line in stdout.splitlines() if line.strip()}


def intersect_prefilters(*prefilters: set[Path] | None) -> set[Path] | None:
    non_null = [prefilter for prefilter in prefilters if prefilter is not None]
    if not non_null:
        return None
    current = set(non_null[0])
    for prefilter in non_null[1:]:
        current &= prefilter
    return current


def parse_jsonl_lines(file_path: Path) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            lines.append(value)
    return lines


def parse_session_summary(file_path: Path, names_by_session_id: dict[str, str]) -> dict[str, Any] | None:
    lines = parse_jsonl_lines(file_path)
    session_id = None
    created_at = None
    updated_at = None
    cwd = None
    preview = None
    searchable_parts: list[str] = []
    path_mentions: set[str] = set()

    for line in lines:
        timestamp = line.get("timestamp")
        if isinstance(timestamp, str):
            updated_at = timestamp

        if line.get("type") == "session_meta" and isinstance(line.get("payload"), dict):
            payload = line["payload"]
            if isinstance(payload.get("id"), str):
                session_id = payload["id"]
            if isinstance(payload.get("timestamp"), str):
                created_at = payload["timestamp"]
            if isinstance(payload.get("cwd"), str):
                cwd = payload["cwd"]
            continue

        if line.get("type") == "event_msg" and isinstance(line.get("payload"), dict):
            payload = line["payload"]
            if payload.get("type") == "user_message":
                event_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
                message = normalize_text(event_payload.get("message"))
                if message:
                    if preview is None and is_meaningful_preview_candidate(message):
                        preview = message
                    searchable_parts.append(message)
                    path_mentions.update(collect_path_mentions(message))
                continue
            if payload.get("type") == "exec_command_end":
                event_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
                aggregated_output = normalize_text(event_payload.get("aggregated_output"))
                if aggregated_output:
                    searchable_parts.append(aggregated_output)
                    path_mentions.update(collect_path_mentions(aggregated_output))
                continue

        if line.get("type") == "response_item" and isinstance(line.get("payload"), dict):
            payload = line["payload"]
            if payload.get("type") == "message":
                message_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
                text = extract_message_text(message_payload.get("content"))
                if text:
                    searchable_parts.append(text)
                    path_mentions.update(collect_path_mentions(text))
                continue

        if line.get("type") == "compacted":
            payload = line.get("payload")
            compacted_payload = payload.get("payload") if isinstance(payload, dict) and isinstance(payload.get("payload"), dict) else payload
            if isinstance(compacted_payload, dict):
                message = normalize_text(compacted_payload.get("message"))
                if message:
                    searchable_parts.append(message)

    if not session_id:
        return None

    stat = file_path.stat()
    if updated_at is None:
        updated_at = _isoformat_timestamp(stat.st_mtime)
    if created_at is None:
        created_at = updated_at

    return {
        "sessionId": session_id,
        "title": names_by_session_id.get(session_id),
        "cwd": cwd,
        "createdAt": created_at,
        "updatedAt": updated_at,
        "archived": "archived_sessions" in file_path.parts,
        "preview": preview or "",
        "searchableText": "\n".join(searchable_parts),
        "pathMentions": sorted(path_mentions),
        "rolloutPath": str(file_path),
    }


def _isoformat_timestamp(stat_mtime: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(stat_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def is_within_workspace(session_cwd: str | None, workspace_root: Path | None) -> bool:
    if not session_cwd or workspace_root is None:
        return False
    resolved_cwd = canonicalize_path(session_cwd)
    resolved_workspace = canonicalize_path(workspace_root)
    return resolved_cwd == resolved_workspace or str(resolved_cwd).startswith(f"{resolved_workspace}{os.sep}")


def build_matched_fields(summary: dict[str, Any], query: str | None, file_query: str | None) -> tuple[list[str], list[str], list[str]]:
    matched_by: list[str] = []
    matched_text: list[str] = []
    matched_paths: list[str] = []

    if query:
        query_lower = query.lower()
        if query_lower in (summary.get("title") or "").lower():
            matched_by.append("query")
            matched_text.append(query)
        elif query_lower in summary.get("searchableText", "").lower():
            matched_by.append("query")
            matched_text.append(query)

    if file_query:
        file_lower = file_query.lower()
        paths = [value for value in summary.get("pathMentions", []) if file_lower in value.lower()]
        if paths:
            matched_by.append("file")
            matched_paths.extend(paths)

    return matched_by, matched_text, matched_paths


def find_sessions(
    *,
    codex_home: Path | None = None,
    cwd: Path | str,
    query: str | None,
    file: str | None,
    after: str | None,
    before: str | None,
    limit: int = 20,
    global_search: bool = False,
) -> dict[str, Any]:
    codex_home = get_codex_home(codex_home)
    workspace_root = None if global_search else resolve_workspace_root(cwd)
    names_by_session_id = load_session_names(codex_home)
    search_roots = [codex_home / "sessions", codex_home / "archived_sessions"]
    rg_query_matches = try_rg_prefilter(query, search_roots, fixed_strings=False)
    rg_file_matches = try_rg_prefilter(file, search_roots, fixed_strings=True)
    rg_matches = intersect_prefilters(rg_query_matches, rg_file_matches)
    after_date = parse_date_input(after)
    before_date = parse_date_input(before)

    results: list[dict[str, Any]] = []
    for root in search_roots:
        for file_path in list_rollout_files(root):
            if rg_matches is not None and canonicalize_path(file_path) not in rg_matches:
                continue
            summary = parse_session_summary(file_path, names_by_session_id)
            if summary is None:
                continue
            if workspace_root and not is_within_workspace(summary.get("cwd"), workspace_root):
                continue
            if query:
                lowered = query.lower()
                if not (
                    lowered in (summary.get("title") or "").lower()
                    or lowered in summary.get("preview", "").lower()
                    or lowered in summary.get("searchableText", "").lower()
                ):
                    continue
            if file:
                lowered = file.lower()
                if not any(lowered in value.lower() for value in summary.get("pathMentions", [])):
                    continue

            updated_at = parse_date_input(summary.get("updatedAt"))
            if after_date and updated_at and updated_at < after_date:
                continue
            if before_date and updated_at and updated_at > before_date:
                continue

            matched_by, matched_text, matched_paths = build_matched_fields(summary, query, file)
            results.append(
                {
                    "sessionId": summary["sessionId"],
                    "title": summary["title"],
                    "cwd": summary["cwd"],
                    "createdAt": summary["createdAt"],
                    "updatedAt": summary["updatedAt"],
                    "archived": summary["archived"],
                    "preview": summary["preview"],
                    "matchedBy": matched_by,
                    "matchedText": matched_text,
                    "matchedPaths": matched_paths,
                    "rolloutPath": summary["rolloutPath"],
                }
            )

    results.sort(key=lambda item: item.get("updatedAt") or "", reverse=True)
    return {
        "scope": {
            "workspaceRoot": str(workspace_root) if workspace_root else None,
            "global": global_search,
        },
        "filters": {
            "query": query,
            "file": file,
            "after": after,
            "before": before,
            "limit": limit,
        },
        "results": results[:limit],
    }


def extract_message_text(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("text"), str):
            parts.append(item["text"])
        elif isinstance(item.get("thinking"), str):
            parts.append(item["thinking"])
    return normalize_text("\n".join(parts))


def normalize_chunk_text(text: Any) -> str:
    return normalize_text(text)


def is_useful_assistant_response(text: str) -> bool:
    lowered = text.lower()
    blocked = [
        "<permissions instructions>",
        "<collaboration_mode>",
        "<apps_instructions>",
        "<skills_instructions>",
        "<environment_context>",
    ]
    return not any(needle in lowered for needle in blocked)


def is_useful_tool_result(text: str) -> bool:
    lowered = text.lower().strip()
    if not lowered:
        return False
    blocked = [
        "chunk id:",
        "wall time:",
        "original token count:",
        "\"sessionid\":",
        "\"rolloutpath\":",
        "tests 5",
        "suites 0",
        "duration_ms",
    ]
    return not any(needle in lowered for needle in blocked)


def parse_session_chunks(file_path: Path) -> tuple[str | None, list[dict[str, Any]]]:
    lines = parse_jsonl_lines(file_path)
    session_id = None
    turn_index = 0
    current_turn_id = None
    chunks: list[dict[str, Any]] = []

    for line_index, line in enumerate(lines):
        timestamp = line.get("timestamp")
        if line.get("type") == "session_meta" and isinstance(line.get("payload"), dict):
            payload = line["payload"]
            if isinstance(payload.get("id"), str):
                session_id = payload["id"]
            continue

        if line.get("type") == "event_msg" and isinstance(line.get("payload"), dict):
            payload = line["payload"]
            if payload.get("type") == "turn_started":
                event_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
                current_turn_id = event_payload.get("turn_id") or current_turn_id
                turn_index += 1
                continue
            if payload.get("type") == "turn_complete":
                current_turn_id = None
                continue

        if line.get("type") == "turn_context" and isinstance(line.get("payload"), dict) and not current_turn_id:
            current_turn_id = line["payload"].get("turn_id")
            turn_index += 1
            continue

        effective_turn_index = turn_index or 1

        if line.get("type") == "event_msg" and isinstance(line.get("payload"), dict):
            payload = line["payload"]
            if payload.get("type") == "user_message":
                event_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
                text = normalize_chunk_text(event_payload.get("message"))
                if text:
                    chunks.append(
                        {
                            "turnIndex": effective_turn_index,
                            "chunkType": "user_request",
                            "text": text,
                            "pathsMentioned": collect_path_mentions(text),
                            "timestamp": timestamp,
                            "rolloutStartIndex": line_index,
                            "rolloutEndIndex": line_index,
                        }
                    )
                continue
            if payload.get("type") == "exec_command_end":
                event_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
                text = normalize_chunk_text(event_payload.get("aggregated_output"))
                if text and is_useful_tool_result(text):
                    chunks.append(
                        {
                            "turnIndex": effective_turn_index,
                            "chunkType": "tool_result",
                            "text": text,
                            "pathsMentioned": collect_path_mentions(text),
                            "timestamp": timestamp,
                            "rolloutStartIndex": line_index,
                            "rolloutEndIndex": line_index,
                        }
                    )
                continue

        if line.get("type") == "response_item" and isinstance(line.get("payload"), dict):
            payload = line["payload"]
            if payload.get("type") == "message":
                message_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
                role = message_payload.get("role")
                text = extract_message_text(message_payload.get("content"))
                if not text:
                    continue
                chunk_type = "user_request" if role == "user" else "assistant_response"
                if chunk_type == "assistant_response" and not is_useful_assistant_response(text):
                    continue
                chunks.append(
                    {
                        "turnIndex": effective_turn_index,
                        "chunkType": chunk_type,
                        "text": text,
                        "pathsMentioned": collect_path_mentions(text),
                        "timestamp": timestamp,
                        "rolloutStartIndex": line_index,
                        "rolloutEndIndex": line_index,
                    }
                )
                continue

        if line.get("type") == "compacted":
            payload = line.get("payload")
            compacted_payload = payload.get("payload") if isinstance(payload, dict) and isinstance(payload.get("payload"), dict) else payload
            if isinstance(compacted_payload, dict):
                text = normalize_chunk_text(compacted_payload.get("message"))
                if text:
                    chunks.append(
                        {
                            "turnIndex": effective_turn_index,
                            "chunkType": "compaction_summary",
                            "text": text,
                            "pathsMentioned": collect_path_mentions(text),
                            "timestamp": timestamp,
                            "rolloutStartIndex": line_index,
                            "rolloutEndIndex": line_index,
                        }
                    )
    return session_id, chunks


_ASCII_TOKEN_RE = re.compile(r"[a-z0-9_./-]+")
_CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


def tokenize_for_retrieval(value: str) -> list[str]:
    text = str(value or "").lower()
    tokens: list[str] = []
    tokens.extend(token.lower() for token in collect_path_mentions(text))

    for match in _ASCII_TOKEN_RE.finditer(text):
        token = match.group(0).strip()
        if len(token) < 2 or token in STOP_WORDS or token.isdigit():
            continue
        tokens.append(token)

    for token in rjieba.cut(text):
        cleaned = token.strip().lower()
        if not cleaned:
            continue
        if cleaned in STOP_WORDS:
            continue
        if not _CJK_CHAR_RE.search(cleaned):
            continue
        tokens.append(cleaned)

    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        deduped.append(token)
    return deduped


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


def score_chunk_bm25(
    chunk: dict[str, Any],
    bm25_score: float,
    query_tokens: list[str],
    chunk_index: int,
    total_chunks: int,
) -> tuple[float, list[str]]:
    chunk_tokens = set(tokenize_for_retrieval(chunk["text"]))
    score = float(bm25_score) + chunk_type_base_score(chunk["chunkType"])
    why_matched: list[str] = []

    for token in query_tokens:
        if token in chunk_tokens:
            why_matched.append(token)

    path_tokens = [value.lower() for value in chunk.get("pathsMentioned", [])]
    for token in query_tokens:
        if any(token in path_value for path_value in path_tokens):
            score += 3.0
            why_matched.append(token)

    if total_chunks > 0:
        score += ((chunk_index + 1) / total_chunks) * 0.5

    if chunk["chunkType"] == "tool_result" and chunk["text"].lstrip().startswith(("{", "[")):
        score -= 4.0

    deduped_why: list[str] = []
    seen: set[str] = set()
    for token in why_matched:
        if token in seen:
            continue
        seen.add(token)
        deduped_why.append(token)
        if len(deduped_why) >= 5:
            break
    return score, deduped_why


def build_excerpt(chunks: list[dict[str, Any]], index: int, include_neighbors: int) -> tuple[str, int, int]:
    start = max(0, index - include_neighbors)
    end = min(len(chunks) - 1, index + include_neighbors)
    excerpt = "\n\n".join(
        f"[turn {chunk['turnIndex']} | {chunk['chunkType']}] {chunk['text']}"
        for chunk in chunks[start : end + 1]
    )
    if len(excerpt) > 700:
        excerpt = f"{excerpt[:700]}..."
    return excerpt, chunks[start]["rolloutStartIndex"], chunks[end]["rolloutEndIndex"]


def read_session_file_by_id(session_id: str, codex_home: Path) -> Path | None:
    roots = [codex_home / "sessions", codex_home / "archived_sessions"]
    for root in roots:
        for file_path in list_rollout_files(root):
            if session_id in file_path.name:
                return file_path
    for root in roots:
        for file_path in list_rollout_files(root):
            first_line = file_path.read_text(encoding="utf-8").splitlines()[:1]
            if not first_line:
                continue
            try:
                value = json.loads(first_line[0])
            except json.JSONDecodeError:
                continue
            if value.get("type") == "session_meta" and value.get("payload", {}).get("id") == session_id:
                return file_path
    return None


def retrieve_thread_context(
    *,
    codex_home: Path | None = None,
    session_id: str,
    goal: str,
    top_k: int = 5,
    max_chars: int = 8000,
    include_neighbors: int = 0,
) -> dict[str, Any]:
    if not goal or not goal.strip():
        raise ValueError("--goal is required")

    codex_home = get_codex_home(codex_home)
    file_path = read_session_file_by_id(session_id, codex_home)
    if file_path is None:
        raise FileNotFoundError(f"Session not found: {session_id}")

    parsed_session_id, chunks = parse_session_chunks(file_path)
    if not parsed_session_id:
        raise RuntimeError(f"Session metadata missing: {session_id}")

    query_tokens = tokenize_for_retrieval(goal)
    if not query_tokens:
        query_tokens = [goal.strip().lower()]

    tokenized_chunks = []
    for chunk in chunks:
        combined_text = f"{chunk['text']} {' '.join(chunk.get('pathsMentioned', []))}".strip()
        tokenized_chunks.append(tokenize_for_retrieval(combined_text))

    bm25 = bm25s.BM25()
    bm25.index(tokenized_chunks, show_progress=False)
    candidate_count = min(len(chunks), max(top_k * 4, top_k))
    retrieval = bm25.retrieve(
        [query_tokens],
        corpus=list(range(len(chunks))),
        k=max(candidate_count, 1),
        show_progress=False,
    )
    document_indices = retrieval.documents[0].tolist()
    bm25_scores = retrieval.scores[0].tolist()

    scored_chunks: list[tuple[float, int, dict[str, Any], list[str]]] = []
    for index, bm25_score in zip(document_indices, bm25_scores, strict=False):
        chunk = chunks[index]
        score, why_matched = score_chunk_bm25(
            chunk,
            bm25_score,
            query_tokens,
            index,
            len(chunks),
        )
        if score > chunk_type_base_score(chunk["chunkType"]):
            scored_chunks.append((score, index, chunk, why_matched))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    selected = scored_chunks[:top_k]

    total_chars = 0
    results: list[dict[str, Any]] = []
    for score, index, chunk, why_matched in selected:
        excerpt, rollout_start_index, rollout_end_index = build_excerpt(
            chunks, index, include_neighbors
        )
        if results and total_chars + len(excerpt) > max_chars:
            break
        total_chars += len(excerpt)
        results.append(
            {
                "rank": len(results) + 1,
                "turnIndex": chunk["turnIndex"],
                "chunkType": chunk["chunkType"],
                "score": round(score, 2),
                "whyMatched": why_matched,
                "pathsMentioned": chunk["pathsMentioned"],
                "timestamp": chunk["timestamp"],
                "rolloutStartIndex": rollout_start_index,
                "rolloutEndIndex": rollout_end_index,
                "excerpt": excerpt,
            }
        )

    return {
        "sessionId": parsed_session_id,
        "goal": goal,
        "topK": top_k,
        "maxChars": max_chars,
        "truncated": len(results) < len(selected),
        "results": results,
        "rolloutPath": str(file_path),
    }


def format_find_text(result: dict[str, Any]) -> str:
    entries = result["results"]
    if not entries:
        return "(no matching sessions found)"
    lines = [f"Found {len(entries)} matching session{'s' if len(entries) != 1 else ''}:", ""]
    for index, entry in enumerate(entries, start=1):
        lines.append(f"{index}. {entry['title'] or '(untitled)'}")
        lines.append(f"   session: {entry['sessionId']}")
        if entry.get("cwd"):
            lines.append(f"   cwd: {entry['cwd']}")
        lines.append(f"   updated: {entry['updatedAt']}")
        if entry.get("preview"):
            lines.append(f"   preview: {entry['preview']}")
        if entry.get("matchedPaths"):
            lines.append(f"   paths: {', '.join(entry['matchedPaths'])}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_retrieval_text(result: dict[str, Any]) -> str:
    if not result["results"]:
        return f"Session: {result['sessionId']}\nGoal: {result['goal']}\n\n(no relevant context found)"
    lines = [f"Session: {result['sessionId']}", f"Goal: {result['goal']}", "", "Top matches:", ""]
    for item in result["results"]:
        lines.append(
            f"{item['rank']}. Turn {item['turnIndex']} · {item['chunkType']} · score {item['score']}"
        )
        if item["whyMatched"]:
            lines.append(f"   Why matched: {', '.join(item['whyMatched'])}")
        if item["pathsMentioned"]:
            lines.append(f"   Paths: {', '.join(item['pathsMentioned'])}")
        lines.append(f"   Excerpt: {item['excerpt']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-thread",
        description="Local Codex session search and retrieval tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    find_parser = subparsers.add_parser(
        "thread_find",
        help="Find local sessions by query, file path, or date range.",
    )
    find_parser.add_argument("--query")
    find_parser.add_argument("--file")
    find_parser.add_argument("--after")
    find_parser.add_argument("--before")
    find_parser.add_argument("--limit", type=int, default=20)
    find_parser.add_argument("--global", dest="global_search", action="store_true")
    find_parser.add_argument("--json", action="store_true")

    retrieval_parser = subparsers.add_parser(
        "thread_retrieval",
        help="Retrieve relevant local context from a known session.",
    )
    retrieval_parser.add_argument("--session-id", required=True)
    retrieval_parser.add_argument("--goal", required=True)
    retrieval_parser.add_argument("--top-k", type=int, default=5)
    retrieval_parser.add_argument("--max-chars", type=int, default=8000)
    retrieval_parser.add_argument("--include-neighbors", type=int, default=0)
    retrieval_parser.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "thread_find":
            if args.limit < 1:
                raise ValueError("--limit must be a positive integer")
            result = find_sessions(
                codex_home=None,
                cwd=Path.cwd(),
                query=args.query,
                file=args.file,
                after=args.after,
                before=args.before,
                limit=args.limit,
                global_search=args.global_search,
            )
            output = json.dumps(result, indent=2, ensure_ascii=False) if args.json else format_find_text(result)
            sys.stdout.write(f"{output}\n")
            return 0

        if args.command == "thread_retrieval":
            if args.top_k < 1:
                raise ValueError("--top-k must be a positive integer")
            if args.max_chars < 1:
                raise ValueError("--max-chars must be a positive integer")
            if args.include_neighbors < 0:
                raise ValueError("--include-neighbors must be a non-negative integer")
            result = retrieve_thread_context(
                codex_home=None,
                session_id=args.session_id,
                goal=args.goal,
                top_k=args.top_k,
                max_chars=args.max_chars,
                include_neighbors=args.include_neighbors,
            )
            output = (
                json.dumps(result, indent=2, ensure_ascii=False)
                if args.json
                else format_retrieval_text(result)
            )
            sys.stdout.write(f"{output}\n")
            return 0

        raise ValueError(f"Unknown command: {args.command}")
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        sys.stderr.write(f"{error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
