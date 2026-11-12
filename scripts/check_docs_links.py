"""Check relative links and the documentation index of this repository.

The repository has no Markdown linter or link checker of its own, so this is the
`docs` arm of `./run.sh`: every tracked Markdown file is scanned for relative
links, and each link must resolve to an existing path (and, for a Markdown
target with a fragment, an existing heading). External URLs are not fetched;
network reachability is not a documentation property this gate can prove.

It also keeps `docs/documentation-index.md` honest: that file must link every
long-lived page under `docs/`, and `docs/README.md` must link the index.

Usage:
    python3 scripts/check_docs_links.py [--root PATH] [--quiet]

Exit codes: 0 all links and index entries resolve, 1 at least one failure.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_DEF = re.compile(r"(?m)^[ \t]{0,3}\[[^\]]+\]:[ \t]*(\S+)")
HEADING = re.compile(r"(?m)^[ \t]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE = re.compile(r"(?m)^[ \t]{0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

INDEX = Path("docs/documentation-index.md")
HUB = Path("docs/README.md")


def tracked_markdown(root: Path) -> list[Path]:
    """Return the tracked Markdown files, ordered."""

    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "*.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return sorted(path for path in root.rglob("*.md") if ".git" not in path.parts)
    return sorted(root / name for name in completed.stdout.split("\0") if name)


def strip_fences(text: str) -> str:
    """Blank out fenced code blocks so examples are not scanned as links."""

    lines = []
    fence = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if fence is None and marker:
            fence = marker.group(1)
            lines.append("")
            continue
        if fence is not None:
            if marker and marker.group(1).startswith(fence[0]) and len(marker.group(1)) >= len(fence):
                fence = None
            lines.append("")
            continue
        lines.append(INLINE_CODE.sub("", line))
    return "\n".join(lines)


def slugify(heading: str) -> str:
    """Approximate GitHub's heading anchor."""

    text = re.sub(r"`([^`]*)`", r"\1", heading)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text)


def anchors(path: Path) -> set[str]:
    """Return every heading anchor of a Markdown file, including `-N` suffixes."""

    text = strip_fences(path.read_text(encoding="utf-8", errors="replace"))
    seen: dict[str, int] = {}
    result: set[str] = set()
    for match in HEADING.finditer(text):
        slug = slugify(match.group(2))
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def link_targets(text: str) -> list[tuple[int, str]]:
    """Return `(line number, target)` for every link in a Markdown document."""

    found: list[tuple[int, str]] = []
    stripped = strip_fences(text)
    for pattern in (INLINE_LINK, REFERENCE_DEF):
        for match in pattern.finditer(stripped):
            raw = match.group(1).strip()
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            elif " " in raw:
                raw = raw.split(" ", 1)[0]
            line = stripped.count("\n", 0, match.start(1)) + 1
            found.append((line, raw))
    return found


def check(root: Path) -> list[str]:
    """Return every documentation failure."""

    failures: list[str] = []
    markdown = tracked_markdown(root)
    known = set(markdown)
    anchor_cache: dict[Path, set[str]] = {}

    for source in markdown:
        if source not in known:
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        relative_source = source.relative_to(root)
        for line, target in link_targets(text):
            if not target or SCHEME.match(target) or target.startswith("//"):
                continue
            parts = urlsplit(target)
            path_part = unquote(parts.path)
            if path_part:
                destination = (source.parent / path_part).resolve()
            else:
                destination = source
            if not destination.exists():
                failures.append(f"{relative_source}:{line}: missing link target {target!r}")
                continue
            if parts.fragment and destination.suffix == ".md":
                if destination not in known:
                    continue
                if destination not in anchor_cache:
                    anchor_cache[destination] = anchors(destination)
                fragment = unquote(parts.fragment)
                if fragment not in anchor_cache[destination]:
                    failures.append(
                        f"{relative_source}:{line}: missing heading #{fragment} in "
                        f"{destination.relative_to(root)}"
                    )

    index = root / INDEX
    hub = root / HUB
    if not index.is_file():
        failures.append(f"{INDEX}: documentation index is missing")
    else:
        index_text = index.read_text(encoding="utf-8")
        for page in sorted((root / "docs").glob("*.md")):
            if page.name in ("README.md", INDEX.name):
                continue
            link = f"({page.name})"
            if link not in index_text:
                failures.append(f"{INDEX}: does not list docs/{page.name}")
        if hub.is_file():
            hub_text = strip_fences(hub.read_text(encoding="utf-8"))
            if INDEX.name not in hub_text:
                failures.append(f"{HUB}: does not link {INDEX.name}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    failures = check(args.root.resolve())
    if failures:
        print("documentation failures:", file=sys.stderr)
        for message in failures:
            print(f"  {message}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"documentation links and index: ok ({len(tracked_markdown(args.root.resolve()))} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
