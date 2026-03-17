from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = ROOT / "docs"
SPHINX_SOURCE = DOCS_ROOT / "sphinx"
SPHINX_TMP_SOURCE = DOCS_ROOT / ".tmp" / "api-sphinx-source"
SPHINX_BUILD = DOCS_ROOT / ".tmp" / "api-sphinx-build"
API_OUTPUT = DOCS_ROOT / "src" / "content" / "docs" / "api"

BASE_PATH = "/algorand-python-testing/"


@dataclass(frozen=True)
class ModuleDoc:
    module_name: str
    source_file: Path


def discover_modules(package_path: Path) -> list[ModuleDoc]:
    modules: list[ModuleDoc] = []
    package_name = package_path.name

    for file_path in sorted(package_path.rglob("*.py")):
        relative = file_path.relative_to(package_path)
        parts = list(relative.parts)

        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]

        if not parts:
            module_name = package_name
        else:
            module_name = ".".join([package_name, *parts])

        modules.append(ModuleDoc(module_name=module_name, source_file=file_path))

    return modules


def render_module_page(module_name: str) -> str:
    return f"""# `{module_name}`

```{{autodoc2-object}} {module_name}
```
"""


def write_sphinx_source(modules: list[ModuleDoc]) -> None:
    if SPHINX_TMP_SOURCE.exists():
        shutil.rmtree(SPHINX_TMP_SOURCE)

    shutil.copytree(SPHINX_SOURCE, SPHINX_TMP_SOURCE)

    generated_dir = SPHINX_TMP_SOURCE / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    toctree_entries: list[str] = []
    for module in modules:
        relative = Path(*module.module_name.split("."))
        module_file = generated_dir / f"{relative}.md"
        module_file.parent.mkdir(parents=True, exist_ok=True)
        module_file.write_text(render_module_page(module.module_name), encoding="utf-8")
        toctree_entries.append(f"generated/{relative.as_posix()}")

    index_content = "\n".join(
        [
            "# API Reference",
            "",
            "```{toctree}",
            ":maxdepth: 2",
            ":caption: Modules",
            "",
            *toctree_entries,
            "```",
            "",
        ]
    )
    (SPHINX_TMP_SOURCE / "index.md").write_text(index_content, encoding="utf-8")


def rewrite_links(content: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        label = match.group(1)
        href = match.group(2)

        if href.startswith("http://") or href.startswith("https://") or href.startswith("#"):
            return match.group(0)

        anchor = ""
        path_part = href
        if "#" in href:
            path_part, anchor = href.split("#", 1)
            anchor = f"#{anchor}"

        if not path_part.endswith(".md"):
            return match.group(0)

        normalized = path_part
        normalized = normalized.replace("../", "")
        normalized = normalized.removeprefix("generated/")
        normalized = normalized.removesuffix(".md")

        if normalized in {"index", ""}:
            new_href = f"{BASE_PATH}api/{anchor}"
        else:
            new_href = f"{BASE_PATH}api/{normalized}/{anchor}"

        return f"[{label}]({new_href})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace, content)


def add_frontmatter(content: str, title: str) -> str:
    body = content
    title_heading = f"# {title}"
    if body.startswith(title_heading):
        body = body[len(title_heading) :].lstrip("\n")

    return "\n".join(
        [
            "---",
            f"title: {title}",
            f"description: API reference for {title}.",
            "---",
            "",
            body,
        ]
    )


def build_sphinx_markdown() -> None:
    if SPHINX_BUILD.exists():
        shutil.rmtree(SPHINX_BUILD)

    cmd = [
        "sphinx-build",
        "-b",
        "markdown",
        "-c",
        str(SPHINX_TMP_SOURCE),
        str(SPHINX_TMP_SOURCE),
        str(SPHINX_BUILD),
        "-W",
        "--keep-going",
    ]
    subprocess.run(cmd, check=True)


def write_starlight_api(modules: list[ModuleDoc]) -> None:
    if API_OUTPUT.exists():
        shutil.rmtree(API_OUTPUT)
    API_OUTPUT.mkdir(parents=True, exist_ok=True)

    index_md = SPHINX_BUILD / "index.md"
    index_content = index_md.read_text(encoding="utf-8") if index_md.exists() else "# API Reference\n"
    index_content = rewrite_links(index_content)
    (API_OUTPUT / "index.md").write_text(add_frontmatter(index_content, "API Reference"), encoding="utf-8")

    for module in modules:
        module_path = Path(*module.module_name.split("."))
        source_md = SPHINX_BUILD / "generated" / f"{module_path}.md"
        if not source_md.exists():
            continue

        destination = API_OUTPUT / module_path / "index.md"
        destination.parent.mkdir(parents=True, exist_ok=True)

        page_content = source_md.read_text(encoding="utf-8")
        page_content = rewrite_links(page_content)
        page_title = module.module_name
        destination.write_text(add_frontmatter(page_content, page_title), encoding="utf-8")


def main() -> None:
    package_roots = [ROOT / "src" / "algopy_testing", ROOT / "src" / "_algopy_testing"]
    modules: list[ModuleDoc] = []
    for package_root in package_roots:
        modules.extend(discover_modules(package_root))

    modules.sort(key=lambda item: item.module_name)

    write_sphinx_source(modules)
    build_sphinx_markdown()
    write_starlight_api(modules)

    print(f"Generated API docs for {len(modules)} modules into {API_OUTPUT}")


if __name__ == "__main__":
    main()
