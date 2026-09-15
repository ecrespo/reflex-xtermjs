#!/usr/bin/env python3
"""Preflight checks for a Reflex custom component before build/publish.

Validates that a custom component project is ready to be built and published to
PyPI: metadata is filled in (no scaffold placeholders), the package layout is
correct, the component source no longer contains the `Fill-Me` placeholders, and
(if a build exists) the built artifacts match the declared version.

Usage:
    python scripts/preflight_check.py [PROJECT_ROOT]

PROJECT_ROOT defaults to the current directory. Exits 0 if all required checks
pass, 1 otherwise. Warnings do not fail the run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - older interpreters
    tomllib = None


GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

errors: list[str] = []
warnings: list[str] = []


def ok(msg: str) -> None:
    print(f"{GREEN}[OK]{RESET} {msg}")


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"{RED}[X]{RESET} {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"{YELLOW}[!]{RESET} {msg}")


def load_pyproject(root: Path) -> dict:
    path = root / "pyproject.toml"
    if not path.exists():
        fail(f"pyproject.toml not found at {path}")
        return {}
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        try:
            return tomllib.loads(text)
        except Exception as exc:  # noqa: BLE001
            fail(f"pyproject.toml is not valid TOML: {exc}")
            return {}
    # Minimal fallback parser for the fields we care about when tomllib is absent.
    warn("tomllib unavailable; using a minimal regex parser for pyproject.toml.")
    data: dict = {"project": {}, "tool": {}}
    m = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"', text)
    if m:
        data["project"]["name"] = m.group(1)
    m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
    if m:
        data["project"]["version"] = m.group(1)
    m = re.search(r'(?m)^\s*description\s*=\s*"([^"]*)"', text)
    if m:
        data["project"]["description"] = m.group(1)
    data["_raw"] = text
    return data


def check_metadata(project: dict, raw_text: str) -> None:
    name = project.get("name", "")
    if not name:
        fail("pyproject.toml [project].name is empty.")
    else:
        ok(f"package name: {name}")
        if not name.startswith("reflex-"):
            warn(
                f"package name '{name}' does not start with 'reflex-'. The prefix "
                "is the Reflex convention for discoverability; keep it unless "
                "intentional."
            )

    version = project.get("version", "")
    if not version:
        fail("pyproject.toml [project].version is empty.")
    else:
        ok(f"version: {version}")
        if version == "0.0.1":
            warn(
                "version is still the scaffold default 0.0.1. Bump it before a "
                "real release (scripts/bump_version.py)."
            )

    description = project.get("description", "")
    if not description or description.strip().lower().startswith(
        "reflex custom component"
    ):
        warn(
            "description is empty or still the generic scaffold text. Set a real "
            "one-line description."
        )
    else:
        ok("description is set.")

    # Authors: tomllib gives structured data; fall back to raw text otherwise.
    authors = project.get("authors")
    author_blob = ""
    if isinstance(authors, list) and authors:
        author_blob = " ".join(
            f"{a.get('name', '')} {a.get('email', '')}" for a in authors
        )
    else:
        author_blob = raw_text
    if "YOUREMAIL@domain.com" in author_blob:
        fail("author email is still the placeholder YOUREMAIL@domain.com.")
    else:
        ok("author email is not the placeholder.")
    if isinstance(authors, list) and authors:
        if not any((a.get("name") or "").strip() for a in authors):
            warn("author name is empty in [project].authors.")

    # URLs
    urls = project.get("urls")
    if isinstance(urls, dict) and urls:
        ok(f"[project.urls] has {len(urls)} entry/entries.")
    elif "[project.urls]" in raw_text and re.search(
        r"(?ms)\[project\.urls\]\s*\n\s*\w", raw_text
    ):
        ok("[project.urls] appears to have entries.")
    else:
        warn("[project.urls] is empty. Add at least a Homepage/Source URL.")


def check_paths(root: Path, project: dict) -> None:
    if not (root / "README.md").exists():
        fail("README.md is missing.")
    else:
        readme = (root / "README.md").read_text(encoding="utf-8")
        if len(readme.strip().splitlines()) <= 6:
            warn(
                "README.md looks like the bare scaffold. Add real usage examples; "
                "PyPI renders it as the package page."
            )
        else:
            ok("README.md exists and has content.")

    cc = root / "custom_components"
    if not cc.is_dir():
        warn(
            "no custom_components/ directory. That's fine for a non-standard "
            "layout, but reflex component build/share expect it."
        )
        return
    ok("custom_components/ directory present.")

    pkg_dirs = [
        p
        for p in cc.iterdir()
        if p.is_dir() and p.name.startswith("reflex_") and not p.name.startswith(".")
    ]
    if not pkg_dirs:
        fail("no reflex_<module>/ package found under custom_components/.")
        return
    for pkg in pkg_dirs:
        if not (pkg / "__init__.py").exists():
            fail(f"{pkg.name}/__init__.py is missing.")
        else:
            ok(f"{pkg.name}/__init__.py present.")
        # Scan the module sources for leftover placeholders.
        for src in pkg.glob("*.py"):
            content = src.read_text(encoding="utf-8")
            if "Fill-Me" in content:
                fail(
                    f"{src.relative_to(root)} still contains 'Fill-Me' — set the "
                    "real library and tag."
                )


def check_dist(root: Path, project: dict) -> None:
    dist = root / "dist"
    version = project.get("version", "")
    if not dist.is_dir():
        warn("no dist/ yet. Run `uv run reflex component build` before publishing.")
        return
    artifacts = list(dist.glob("*.whl")) + list(dist.glob("*.tar.gz"))
    if not artifacts:
        warn("dist/ exists but has no .whl/.tar.gz. Rebuild before publishing.")
        return
    if version and not any(version in a.name for a in artifacts):
        warn(
            f"dist/ artifacts do not match version {version}. Rebuild so the "
            "upload matches pyproject.toml."
        )
    else:
        ok(f"dist/ has {len(artifacts)} artifact(s) matching version {version}.")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    print(f"Preflight for: {root}\n")

    data = load_pyproject(root)
    project = data.get("project", {}) if data else {}
    raw_text = data.get("_raw") or (
        (root / "pyproject.toml").read_text(encoding="utf-8")
        if (root / "pyproject.toml").exists()
        else ""
    )

    if project or raw_text:
        check_metadata(project, raw_text)
    check_paths(root, project)
    check_dist(root, project)

    print()
    if errors:
        print(f"{RED}Preflight failed: {len(errors)} error(s), "
              f"{len(warnings)} warning(s).{RESET}")
        return 1
    print(f"{GREEN}Preflight passed.{RESET} {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
