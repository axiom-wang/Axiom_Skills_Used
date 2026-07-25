---
name: mptext-wechat-article-fetcher
description: Fetch and download WeChat official account articles using the MPText API. Use when the user provides an MPText API key and asks to search public accounts, resolve account fakeids, fetch article lists, download article text/markdown/html/json, or collect WeChat article bodies for later processing.
---

# MPText WeChat Article Fetcher

Use this skill when the user gives an MPText API key plus a WeChat official account/article fetching task. Prefer this over generic web search or Sogou-based skills when the user specifically wants article lists or article bodies.

## Core Rules

- Do not persist the user's API key in skill files, source code, final deliverables, or logs. Pass it by env var or command argument only.
- Treat `mp.weixin.qq.com` as the official article URL source. Do not substitute third-party repost pages when the task is to fetch official articles.
- State the account, date range, article count, output path, and extraction limits.
- MPText extracts page text but does not OCR text embedded in images. If many articles are image/poster-heavy, say that title/digest + extracted text were used and OCR was not performed unless requested.
- Save raw working data under the current workspace `work/` unless the user asks for a deliverable; put user-facing deliverables under the workspace `outputs/` directory.

## API Reference

Base URL: `https://down.mptext.top`

Authenticate every request with:

```text
X-Auth-Key: <user-provided-key>
```

Endpoints:

- Validate key: `GET /api/public/v1/authkey`
- Search account: `GET /api/public/v1/account?keyword=<keyword>`
- Article list: `GET /api/public/v1/article?fakeid=<fakeid>&begin=0&size=20&keyword=<optional-title-keyword>`
- Download article: `GET /api/public/v1/download?url=<article-url>&format=text`
- Account by article URL: `GET /api/public/v1/accountbyurl?url=<article-url>`

## Workflow

1. Validate the API key with `/authkey`.
2. Resolve the account:
   - If the user gives a `fakeid`, use it directly.
   - Otherwise search `/account?keyword=...` and choose the exact nickname/alias match when possible.
   - If multiple plausible official accounts exist, report the candidates and choose conservatively, or ask if ambiguity is material.
3. Fetch article list pages with `size=20` until the requested date range is covered.
4. Filter out deleted articles and keep only articles within the requested date range.
5. Download article bodies with the requested format. Default to `text` for downstream analysis and `json` when metadata plus raw HTML fields are useful.
6. Save a structured JSON file with account info, request parameters, article metadata, and downloaded content.
7. In the final answer, report what was fetched and where it was saved. Mention image/OCR limitations when relevant.

## Helper Script

Use `scripts/mptext_fetch.js` for repeatable fetching.

Example:

```powershell
$env:MPTEXT_AUTH_KEY = '<api-key>'
node C:\Users\24853\.codex\skills\mptext-wechat-article-fetcher\scripts\mptext_fetch.js `
  --account "公众号名称" `
  --from 2025-06-05 `
  --to 2026-06-05 `
  --out .\work\mptext_articles.json
```

Useful options:

- `--auth-key <key>` or env `MPTEXT_AUTH_KEY`
- `--account <keyword>` or `--fakeid <fakeid>`
- `--from YYYY-MM-DD`
- `--to YYYY-MM-DD`
- `--keyword <title keyword>`
- `--out <json path>`
- `--no-download` to fetch only metadata
- `--concurrency <n>` for article body downloads
- `--max-pages <n>` to cap article-list pagination

## Output Expectations

For fetch/download tasks, produce a short status summary:

- Account chosen: nickname, alias, fakeid if available.
- Date range and optional title keyword.
- Number of articles fetched and number of bodies downloaded.
- Count of very short extracted bodies (`text_length < 100`) as a signal that articles may be image-heavy.
- Path to the saved JSON file.

If the user asks for subsequent analysis, use the saved article bodies as source material and keep official article links attached to claims.
