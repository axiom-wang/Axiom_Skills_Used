#!/usr/bin/env python3
"""Kami local Windows PDF runner.

Usage:
  python render_pdf.py <HTML_PATH> <PDF_PATH>

Writes:
  - render_result.json next to this script
  - render_pdf.log next to this script
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


LOCAL_DIR = Path(__file__).resolve().parent
RESULT_JSON = LOCAL_DIR / "render_result.json"
LOG_PATH = LOCAL_DIR / "render_pdf.log"


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_result(payload: dict) -> None:
    RESULT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fail(html: str, pdf: str, error: str, code: int = 1) -> int:
    write_result(
        {
            "success": False,
            "html": html,
            "pdf": pdf,
            "size": 0,
            "error": error,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    log(f"FAIL: {error}")
    return code


def main(argv: list[str]) -> int:
    # Fresh log for this run
    LOG_PATH.write_text("", encoding="utf-8")

    if len(argv) != 3:
        return fail(
            "",
            "",
            "Usage: render_pdf.py <HTML_PATH> <PDF_PATH>",
            code=2,
        )

    # Keep caller-provided path strings in JSON (junction/symlink hosts may
    # resolve C:\Users\...\ .claude -> D:\claude-data; kami-pdf verifies
    # exact path equality against the requested Windows path).
    html_arg = os.path.expanduser(argv[1])
    pdf_arg = os.path.expanduser(argv[2])
    html_real = str(Path(html_arg).resolve())
    pdf_real = str(Path(pdf_arg).resolve())

    log(f"HTML={html_arg}")
    log(f"HTML_REAL={html_real}")
    log(f"PDF={pdf_arg}")
    log(f"PDF_REAL={pdf_real}")

    if not Path(html_real).is_file():
        return fail(html_arg, pdf_arg, f"HTML not found: {html_arg}")

    try:
        from weasyprint import HTML
    except Exception as exc:  # noqa: BLE001
        return fail(
            html_arg,
            pdf_arg,
            f"WeasyPrint import failed: {exc}",
        )

    try:
        Path(pdf_real).parent.mkdir(parents=True, exist_ok=True)
        # Remove stale PDF so success cannot be inferred from an old file
        if Path(pdf_real).exists():
            Path(pdf_real).unlink()

        base_url = Path(html_real).parent.as_uri() + "/"
        log(f"base_url={base_url}")
        HTML(filename=html_real, base_url=base_url).write_pdf(pdf_real)

        size = Path(pdf_real).stat().st_size if Path(pdf_real).is_file() else 0
        if size <= 0:
            return fail(html_arg, pdf_arg, "PDF was created but size is 0")

        write_result(
            {
                "success": True,
                "html": html_arg,
                "pdf": pdf_arg,
                "size": size,
                "error": None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "html_resolved": html_real,
                "pdf_resolved": pdf_real,
            }
        )
        log(f"OK size={size}")
        return 0
    except Exception as exc:  # noqa: BLE001
        log(traceback.format_exc())
        return fail(html_arg, pdf_arg, f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
