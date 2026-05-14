#!/usr/bin/env python3
"""Generate API reference markdown from Python source using Sphinx + autoapi,
then post-process the output for Starlight consumption.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_DIR.parent
API_OUT = DOCS_DIR / "src" / "content" / "docs" / "api"

SOURCE_PACKAGE = "_algopy_testing"
PUBLIC_PACKAGE = "algopy_testing"
PACKAGES = (PUBLIC_PACKAGE,)
_PACKAGES_ALT = "|".join(re.escape(p) for p in PACKAGES)

_HEADING_RE = re.compile(r"^#{3,4}\s")
_LINKED_QUALIFIED_RE = re.compile(
    rf"\[\\?(?:{_PACKAGES_ALT}|typing_extensions|collections\.abc)" r"(?:\.\w+)*\.(\w+)\]"
)
_PLAIN_QUALIFIED_RE = re.compile(
    rf"(?<!\[)(?<!#)(?<!/)(?<!\.md)\\?(?:{_PACKAGES_ALT}|typing_extensions|collections\.abc)"
    r"(?:\.\w+)*\.(\w+)"
)
_INDEX_MD_RE = re.compile(r"/index\.md")

_CLASS_ARGS_RE = re.compile(
    r"^(#{3,4} \*class\* \w+)\(.*\)\s*$",
    re.MULTILINE,
)
_CLASS_HEADING_RE = re.compile(r"^#{3,4} \*class\* ")
_H3_TEXT_RE = re.compile(r"^### (.+)$", re.MULTILINE)
_QUALIFIED_ANCHOR_RE = re.compile(
    rf"\(([^()\s\"']*?)#(?:{_PACKAGES_ALT}|typing_extensions|collections\.abc)"
    r"(?:\.\w+)*\.(\w+)\)"
)


def _clean_api_output() -> None:
    print("==> Cleaning previous API output...")
    if API_OUT.exists():
        shutil.rmtree(API_OUT)
    API_OUT.mkdir(parents=True, exist_ok=True)


def _run_sphinx_build() -> None:
    print("==> Running Sphinx markdown build...")
    result = subprocess.run(
        ["sphinx-build", "-b", "markdown", "docs/sphinx", str(API_OUT), "-q"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"ERROR: Sphinx build failed (exit code {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        sys.exit(1)


def _remove_sphinx_artifacts() -> None:
    print("==> Removing Sphinx artifacts...")
    buildinfo = API_OUT / ".buildinfo"
    if buildinfo.exists():
        buildinfo.unlink()

    doctrees = API_OUT / ".doctrees"
    if doctrees.exists():
        shutil.rmtree(doctrees)

    index_md = API_OUT / "index.md"
    if index_md.exists():
        index_md.unlink()


def _flatten_autoapi() -> None:
    """Move autoapi/_algopy_testing/ → algopy_testing/ — rename private impl
    package to its public name so docs never expose the leading-underscore."""
    print("==> Flattening autoapi directory structure...")
    autoapi_dir = API_OUT / "autoapi"

    source = autoapi_dir / SOURCE_PACKAGE
    target = API_OUT / PUBLIC_PACKAGE

    if not source.is_dir():
        print(
            f"ERROR: Expected autoapi output directory not found: {source}\n"
            "This likely means the Sphinx autoapi configuration or"
            " package structure has changed.\n"
            "Check that 'autoapi_dirs' in docs/sphinx/conf.py points to"
            " the correct source directories.",
            file=sys.stderr,
        )
        sys.exit(1)

    if target.exists():
        shutil.rmtree(target)
    shutil.move(str(source), str(target))

    if autoapi_dir.exists():
        shutil.rmtree(autoapi_dir)


def _rename_source_package_in_content() -> None:
    """Rewrite `_algopy_testing` → `algopy_testing` inside generated markdown.
    Drops markdown's `\\_` escape (no longer needed for a non-underscore prefix)."""
    print(f"==> Rewriting {SOURCE_PACKAGE} → {PUBLIC_PACKAGE} in content...")
    escaped = "\\" + SOURCE_PACKAGE
    for md_file in API_OUT.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        updated = content.replace(escaped, PUBLIC_PACKAGE).replace(SOURCE_PACKAGE, PUBLIC_PACKAGE)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def _extract_title(file_path: Path) -> str:
    with file_path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return re.sub(r"\\(?=\w)", "", line[2:].strip())
    return file_path.stem


def _inject_frontmatter() -> None:
    print("==> Injecting Starlight frontmatter into API docs...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        title = _extract_title(md_file)
        escaped_title = title.replace('"', '\\"')

        content = md_file.read_text(encoding="utf-8")
        content = re.sub(r"^# [^\n]*\n+", "", content)
        md_file.write_text(
            f'---\ntitle: "{escaped_title}"\n---\n\n'
            f'<div class="api-ref">\n\n{content}\n\n</div>\n',
            encoding="utf-8",
        )


def _fix_internal_links() -> None:
    print("==> Fixing internal links for Starlight...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _INDEX_MD_RE.sub("/", content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def _compute_starlight_anchor(heading_text: str) -> str:
    """Reproduce Sphinx-markdown-builder's slug for a heading, used to recognise
    the legacy autoapi-style anchors that summary tables emit before rewriting."""
    text = re.sub(r"\*([^*]+)\*", r"\1", heading_text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\\.", "", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9-]+", " ", text)
    return "-".join(text.split())


def _github_slug(heading_text: str) -> str:
    """Reproduce github-slugger's slug (the algorithm rehype-slug uses inside
    Starlight) so we can rewrite anchors to match the heading IDs Starlight
    actually emits.

    Differs from `_compute_starlight_anchor` by preserving underscores and not
    collapsing runs of removed punctuation — `\\* | \\*` becomes `--` here but
    `-` under the Sphinx algorithm.
    """
    text = re.sub(r"\*([^*]+)\*", r"\1", heading_text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\\(.)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9 _-]", "", text)
    text = text.replace(" ", "-")
    return text.strip("-")


def _simplify_class_headings() -> None:
    print("==> Simplifying class heading signatures...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _CLASS_ARGS_RE.sub(r"\1", content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


_H2_HEADING_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
_SUMMARY_RENAME = {"Attributes": "Data", "Classes": "Classes", "Functions": "Functions"}
_SUMMARY_ORDER = ("Classes", "Functions", "Attributes")  # puya order: Classes, Functions, Data

_SIG_DOUBLE_COMMA_RE = re.compile(r",\s*(?:,\s*)+")
_SIG_TRAILING_COMMA_RE = re.compile(r",\s*\)")
_SIG_LEADING_COMMA_RE = re.compile(r"\(\s*,\s*")
_SIGNATURE_HEADING_RE = re.compile(r"^(#{3,4} [^\n]*\([^\n)]*\)[^\n]*)$", re.MULTILINE)


def _clean_signature_separators(line: str) -> str:
    """Collapse stray separator artifacts left when autoapi drops `/` and `*`
    parameter markers but leaves the surrounding commas (e.g. ``a, , b`` or
    ``a, , , b``)."""
    cleaned = _SIG_DOUBLE_COMMA_RE.sub(", ", line)
    cleaned = _SIG_TRAILING_COMMA_RE.sub(")", cleaned)
    cleaned = _SIG_LEADING_COMMA_RE.sub("(", cleaned)
    return cleaned


def _clean_signature_artifacts() -> None:
    """Repair signature artifacts in heading lines only (avoid touching prose)."""
    print("==> Cleaning signature comma artifacts...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _SIGNATURE_HEADING_RE.sub(
            lambda m: _clean_signature_separators(m.group(1)), content
        )
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def _restructure_top_sections() -> None:
    """Nest `Attributes/Classes/Functions` summary tables under the existing
    `## Module Contents` H2 (and demote them to H3, renaming Attributes → Data)
    so the page reads as a single grouped section rather than four sibling H2s."""
    print("==> Restructuring module summaries under Module Contents...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        h2_matches = list(_H2_HEADING_RE.finditer(content))
        if not h2_matches:
            continue

        sections: dict[str, tuple[int, int]] = {}
        for i, m in enumerate(h2_matches):
            name = m.group(1).strip()
            end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(content)
            sections[name] = (m.start(), end)

        if "Module Contents" not in sections or not (set(_SUMMARY_RENAME) & set(sections)):
            continue

        summary_blocks: dict[str, str] = {}
        for name in _SUMMARY_RENAME:
            if name not in sections:
                continue
            start, end = sections[name]
            block = content[start:end].rstrip() + "\n\n"
            new_name = _SUMMARY_RENAME[name]
            summary_blocks[name] = re.sub(r"^## .+", f"### {new_name}", block, count=1)

        ranges = sorted((sections[n] for n in summary_blocks), key=lambda r: r[0], reverse=True)
        new_content = content
        for start, end in ranges:
            new_content = new_content[:start] + new_content[end:]

        mc_match = re.search(r"^## Module Contents[ \t]*$", new_content, re.MULTILINE)
        if not mc_match:
            continue
        injection = "\n\n" + "".join(
            summary_blocks[n] for n in _SUMMARY_ORDER if n in summary_blocks
        )
        insert_at = mc_match.end()
        tail = new_content[insert_at:].lstrip("\n")
        new_content = new_content[:insert_at] + injection + tail
        new_content = re.sub(r"\n{3,}", "\n\n", new_content)

        if new_content != content:
            md_file.write_text(new_content, encoding="utf-8")


def _dedupe_class_headings() -> None:
    """Drop adjacent duplicate class headings produced when @typing.overload
    spawns multiple signatures that collapse after argument stripping."""
    print("==> Deduplicating adjacent class headings...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        lines = md_file.read_text(encoding="utf-8").splitlines(keepends=True)
        out: list[str] = []
        prev_class: str | None = None
        changed = False
        for line in lines:
            s = line.rstrip()
            if _CLASS_HEADING_RE.match(s):
                if s == prev_class:
                    changed = True
                    continue
                prev_class = s
            elif s:
                prev_class = None
            out.append(line)
        if changed:
            md_file.write_text("".join(out), encoding="utf-8")


def _fix_qualified_anchors() -> None:
    print("==> Fixing qualified name anchors...")
    file_maps: dict[str, dict[str, str]] = {}
    for md_file in sorted(API_OUT.rglob("*.md")):
        anchor_map: dict[str, str] = {}
        content = md_file.read_text(encoding="utf-8")
        for m in _H3_TEXT_RE.finditer(content):
            heading_text = m.group(1)
            key_m = re.match(r"(?:\*\w+\*\s+)?(\w+)", heading_text)
            if key_m:
                symbol = key_m.group(1)
                anchor_map[symbol] = _github_slug(heading_text)
        file_maps[str(md_file)] = anchor_map

    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")

        def fix_anchor(m: re.Match, _file: Path = md_file) -> str:
            path_part, symbol = m.group(1), m.group(2)
            if path_part:
                target_md = (_file.parent / path_part).resolve() / "index.md"
            else:
                target_md = _file
            anchor = file_maps.get(str(target_md), {}).get(symbol, symbol.lower())
            return f"({path_part}#{anchor})"

        updated = _QUALIFIED_ANCHOR_RE.sub(fix_anchor, content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


_SAME_PAGE_ANCHOR_RE = re.compile(r"\(#([^)]+)\)")


def _fix_member_index_anchors() -> None:
    """Rewrite same-page anchors that Sphinx pre-slugified to the slug Starlight
    actually generates.

    Sphinx-markdown-builder writes summary-table links such as
    ``[arc4_signature](#arc4-signature-signature-str-callable-p-r-algopy-bytes)``
    using its own slug algorithm, but Starlight assigns heading IDs via
    github-slugger, which produces a different slug for the same heading text
    (preserves underscores, doesn't collapse removed punctuation). For each H3
    heading we map the Sphinx slug onto the github-slugger slug and rewrite
    every ``(#anchor)`` reference on the same page.
    """
    print("==> Fixing member-index anchor slugs (sphinx → github-slugger)...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        slug_map: dict[str, str] = {}
        for m in _H3_TEXT_RE.finditer(content):
            heading_text = m.group(1)
            old_slug = _compute_starlight_anchor(heading_text)
            new_slug = _github_slug(heading_text)
            if old_slug and old_slug != new_slug:
                slug_map[old_slug] = new_slug

        if not slug_map:
            continue

        def fix_anchor(m: re.Match, _slug_map: dict[str, str] = slug_map) -> str:
            anchor = m.group(1)
            return f"(#{_slug_map.get(anchor, anchor)})"

        updated = _SAME_PAGE_ANCHOR_RE.sub(fix_anchor, content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


_HEADING_ESCAPE_RE = re.compile(r"\\(?=\w)")


_ADMONITION_HEADING_RE = re.compile(
    r"^#### (NOTE|WARNING|TIP|IMPORTANT|CAUTION|DANGER|HINT|ATTENTION|SEEALSO)\s*$"
)
_STARLIGHT_ADMONITION = {
    "note": "note",
    "hint": "tip",
    "tip": "tip",
    "warning": "caution",
    "caution": "caution",
    "attention": "caution",
    "important": "danger",
    "danger": "danger",
    "seealso": "note",
}


def _convert_admonitions() -> None:
    """Rewrite sphinx admonition headings as Starlight aside directives.

    sphinx-markdown-builder renders ``.. note::`` (and friends) as ``#### NOTE``
    followed by the body until the next heading. Starlight uses container
    directives (``:::note ... :::``), so collect each admonition block and
    re-emit it.
    """
    print("==> Converting rST admonitions to Starlight asides...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        out: list[str] = []
        i = 0
        n = len(lines)
        changed = False
        while i < n:
            m = _ADMONITION_HEADING_RE.match(lines[i])
            if not m:
                out.append(lines[i])
                i += 1
                continue
            changed = True
            kind = _STARLIGHT_ADMONITION.get(m.group(1).lower(), "note")
            i += 1
            body: list[str] = []
            while i < n and not lines[i].lstrip().startswith("#"):
                body.append(lines[i])
                i += 1
            while body and body[-1].strip() == "":
                body.pop()
            while body and body[0].strip() == "":
                body.pop(0)
            out.append(f":::{kind}")
            out.extend(body)
            out.append(":::")
            out.append("")
        if changed:
            new_content = "\n".join(out) + ("\n" if content.endswith("\n") else "")
            md_file.write_text(new_content, encoding="utf-8")


_PARAM_BULLET_RE = re.compile(r"^(\s{4,})\\\*(\s)", re.MULTILINE)


def _fix_param_bullet_escapes() -> None:
    """Unescape ``\\*`` sub-bullets that appear inside Parameter blocks.

    Sphinx already renders ``:param:`` field lists into a Parameters bullet
    structure, but ``*`` characters used by docstring authors as nested bullets
    are emitted as ``\\*`` and stay as literal text. They sit at 4-space indent
    inside the parameter item, which is exactly the depth a real nested bullet
    needs — so dropping the backslash turns them into proper nested bullets.
    """
    print("==> Fixing escaped sub-bullets in Parameter blocks...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _PARAM_BULLET_RE.sub(r"\1*\2", content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


_DEFAULT_FENCE_RE = re.compile(r"^```default\s*$", re.MULTILINE)


def _strip_default_language() -> None:
    """Remove the ``default`` language tag from fenced code blocks.

    sphinx-markdown-builder writes ``.. code-block::`` (no argument) as
    ``` ```default ```; Starlight's expressive-code highlighter doesn't know
    that language and falls back to plain text. Drop the tag so the block
    renders as plain text without the synthetic language annotation.
    """
    print("==> Stripping `default` language tag from code fences...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        updated = _DEFAULT_FENCE_RE.sub("```", content)
        if updated != content:
            md_file.write_text(updated, encoding="utf-8")


def _shorten_qualified_names() -> None:
    print("==> Shortening qualified names in headings...")
    for md_file in sorted(API_OUT.rglob("*.md")):
        lines = md_file.read_text(encoding="utf-8").splitlines(keepends=True)
        changed = False
        for i, line in enumerate(lines):
            if not _HEADING_RE.match(line):
                continue
            new_line = _LINKED_QUALIFIED_RE.sub(r"[\1]", line)
            new_line = _PLAIN_QUALIFIED_RE.sub(r"\1", new_line)
            new_line = _HEADING_ESCAPE_RE.sub("", new_line)
            if new_line != line:
                lines[i] = new_line
                changed = True
        if changed:
            md_file.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    _clean_api_output()
    _run_sphinx_build()
    _remove_sphinx_artifacts()
    _flatten_autoapi()
    _rename_source_package_in_content()
    _inject_frontmatter()
    _convert_admonitions()
    _fix_param_bullet_escapes()
    _strip_default_language()
    _restructure_top_sections()
    _fix_internal_links()
    _shorten_qualified_names()
    _simplify_class_headings()
    _clean_signature_artifacts()
    _dedupe_class_headings()
    _fix_qualified_anchors()
    _fix_member_index_anchors()

    file_count = sum(1 for _ in API_OUT.rglob("*.md"))
    print(f"==> API docs generated at: {API_OUT}")
    print(f"    {file_count} markdown files")


if __name__ == "__main__":
    main()
