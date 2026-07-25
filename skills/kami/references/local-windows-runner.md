# Local Windows Runner

Fixed Windows path for Kami PDF rendering. Used by the `/kami-pdf` command.

## Paths

| Item | Path |
|---|---|
| Skill root | `C:\Users\24853\.claude\skills\kami` |
| Work HTML | `C:\Users\24853\.claude\skills\kami\work\` |
| Runner | `C:\Users\24853\.claude\skills\kami\local\render_pdf.cmd` |
| Result JSON | `C:\Users\24853\.claude\skills\kami\local\render_result.json` |
| Log | `C:\Users\24853\.claude\skills\kami\local\render_pdf.log` |

## Render command

```bat
cmd.exe /c ""C:\Users\24853\.claude\skills\kami\local\render_pdf.cmd" "<HTML_PATH>" "<PDF_PATH>""
```

## Result contract

`render_result.json` fields:

- `success` (bool)
- `html` (absolute Windows path)
- `pdf` (absolute Windows path)
- `size` (bytes, > 0 on success)
- `error` (string or null)
- `generated_at` (ISO-8601 UTC)

## Notes

- Prefer `C:\Program Files\Python312\python.exe` (WeasyPrint installed there).
- Always delete stale `render_result.json` / `render_pdf.log` before a new render.
- Do not call WeasyPrint directly from the agent; go through `render_pdf.cmd`.
- On this machine `C:\Users\24853\.claude` is a symlink to `D:\claude-data`. The runner keeps the caller-provided `C:\...` paths in `render_result.json` so `/kami-pdf` path equality checks still pass.
