"""Generic markdown "section" format shared by pipeline stages.

Each stage (filter -> summarize -> write) reads markdown sections written by
the previous stage and writes its own. A section looks like:

    ## Title

    **Key:** value
    **Another Key:** value

    Free-form body text.

This module is the single place that knows that shape, so every agent reads
and writes it the same way instead of each hand-rolling its own regex.
"""

from __future__ import annotations

import re
from pathlib import Path

_FIELD_RE = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")
_SECTION_SPLIT_RE = re.compile(r"(?m)^## (.+)$")
_TRAILING_RULE_RE = re.compile(r"\n-{3,}\s*$")


def write_sections(path: str | Path, sections: list[dict], header: str = "") -> Path:
    """Write ``sections`` to ``path``. Each section needs a ``title`` and a ``body``;
    every other key becomes a bold ``**Key:** value`` field line.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        if header:
            f.write(header.rstrip() + "\n\n")

        for section in sections:
            f.write(f"## {section['title']}\n\n")
            for key, value in section.items():
                if key in ("title", "body"):
                    continue
                f.write(f"**{key.replace('_', ' ').title()}:** {value}\n")
            f.write(f"\n{section.get('body', '')}\n\n---\n\n")

    return path


def load_sections(path: str | Path) -> list[dict]:
    """Parse ``## Title`` sections (as written by ``write_sections``) back into dicts.

    Anything before the first ``## `` heading (e.g. a document header) is ignored.
    """
    text = Path(path).read_text(encoding="utf-8")
    pieces = _SECTION_SPLIT_RE.split(text)[1:]  # drop any pre-first-heading text

    records = []
    for title, body in zip(pieces[0::2], pieces[1::2]):
        body = _TRAILING_RULE_RE.sub("", body).strip()

        record: dict = {"title": title.strip()}
        body_lines = []
        for line in body.splitlines():
            match = _FIELD_RE.match(line.strip())
            if match:
                key = match.group(1).strip().lower().replace(" ", "_")
                record[key] = match.group(2).strip()
            elif line.strip():
                body_lines.append(line.strip())

        record["body"] = "\n".join(body_lines).strip()
        records.append(record)

    return records
