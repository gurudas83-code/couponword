#!/usr/bin/env python3
"""Build the approved public GitHub Pages artifact."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    "index.html", "style.css", "app.js", "coupons.json", "CNAME",
    "robots.txt", "sitemap.xml", "buying-guides.html", "buying-guides.js",
)
PUBLIC_DATA_FILES = ("data/seo-pages.json",)
PUBLIC_DIRECTORIES = ("assets", "products", "seo")
FORBIDDEN_NAMES = {
    "admin.html", "validator.html", "python", "reports", "outputs",
    "backups", ".git", "phase_e_current.zip",
}


def _copy_file(relative: str, destination: Path) -> None:
    source = ROOT / relative
    if not source.is_file():
        raise FileNotFoundError(f"required public file is missing: {relative}")
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build(output: Path) -> Path:
    output = output.resolve()
    if output == ROOT or output in ROOT.parents:
        raise ValueError("public artifact output cannot replace the repository")
    source_paths = [ROOT / item for item in PUBLIC_FILES + PUBLIC_DIRECTORIES]
    if any(output == source or source in output.parents for source in source_paths):
        raise ValueError("public artifact output cannot overlap a source path")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for relative in PUBLIC_FILES + PUBLIC_DATA_FILES:
        _copy_file(relative, output)
    for relative in PUBLIC_DIRECTORIES:
        source = ROOT / relative
        if not source.is_dir():
            raise FileNotFoundError(f"required public directory is missing: {relative}")
        shutil.copytree(source, output / relative)

    leaked = []
    for path in output.rglob("*"):
        parts = path.relative_to(output).parts
        if path.name in FORBIDDEN_NAMES or any(part in FORBIDDEN_NAMES for part in parts):
            leaked.append(str(path.relative_to(output)))
    if leaked:
        raise RuntimeError("forbidden files entered public artifact: " + ", ".join(leaked))
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"public artifact ready: {build(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
