#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", "products",
    ".price_backups", ".integration_backups", ".import_backups",
    ".compliance_backups", "backups", "audit_reports",
}

IMPORTANT_FILES = (
    "coupons.json", "index.html", "sitemap.xml",
    "python/couponworld.py", "python/build_product_pages.py",
    "python/build_sitemap.py",
)

@dataclass
class ModuleInfo:
    path: str
    module: str
    lines: int
    syntax_ok: bool
    syntax_error: str | None
    imports: list[str]
    local_imports: list[str]
    classes: list[str]
    functions: list[str]
    cli_commands: list[str]
    has_main: bool
    category: str
    sha256: str


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit the complete Coupon World system in one read-only run")
    p.add_argument("--root", default=".")
    p.add_argument("--output-dir", default="audit_reports")
    return p.parse_args()


def module_name(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[0] == "python":
        parts = parts[1:]
    return ".".join(parts)


def category(path: Path) -> str:
    n = path.stem.lower()
    if n == "couponworld": return "Master Controller"
    if n.startswith("build_") or "sitemap" in n: return "Build System"
    if "audit" in n or "status" in n: return "Audit / Monitoring"
    if any(x in n for x in ("source", "provider", "adapter", "sync")): return "Source / Data Adapter"
    if any(x in n for x in ("import", "migrate", "queue")): return "Import / Intake"
    if any(x in n for x in ("price", "inventory")): return "Price / Inventory"
    if any(x in n for x in ("identity", "feature", "intelligence", "engine")): return "Product Intelligence"
    if any(x in n for x in ("brain", "recommendation", "scoring", "intent")): return "Shopping Intelligence"
    if "seo" in n or "link" in n: return "SEO / Discovery"
    if "image" in n: return "Image System"
    return "Utility / Other"


def py_files(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def cli_commands(tree: ast.AST) -> list[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr == "add_parser" and node.args:
            v = node.args[0]
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                found.add(v.value)
        for kw in node.keywords:
            if kw.arg == "choices" and isinstance(kw.value, (ast.List, ast.Tuple, ast.Set)):
                for item in kw.value.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        found.add(item.value)
    return sorted(found)


def parse_module(root: Path, path: Path, known: set[str]) -> ModuleInfo:
    text = path.read_text(encoding="utf-8", errors="replace")
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    name = module_name(root, path)
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return ModuleInfo(str(path.relative_to(root)), name, len(text.splitlines()), False,
                          f"Line {e.lineno}: {e.msg}", [], [], [], [], [], False,
                          category(path), digest)

    imports: set[str] = set()
    classes: list[str] = []
    functions: list[str] = []
    has_main = False
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            has_main = has_main or node.name == "main"

    local = sorted(i for i in imports if i.split(".")[0] in known or i in known)
    return ModuleInfo(str(path.relative_to(root)), name, len(text.splitlines()), True, None,
                      sorted(imports), local, sorted(classes), sorted(functions),
                      cli_commands(tree), has_main, category(path), digest)


def git(root: Path, *cmd: str) -> dict[str, Any]:
    try:
        r = subprocess.run(["git", *cmd], cwd=root, capture_output=True, text=True,
                           timeout=20, check=False)
        return {"ok": r.returncode == 0, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e)}


def coupons(root: Path) -> dict[str, Any]:
    p = root / "coupons.json"
    if not p.exists(): return {"exists": False}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"exists": True, "valid": False, "error": str(e)}
    if not isinstance(data, list):
        return {"exists": True, "valid": True, "is_list": False}
    tracked = ("id", "sl_no", "title", "category", "link", "image", "price", "mrp", "brand", "description", "active")
    missing = Counter()
    for product in data:
        if isinstance(product, dict):
            for field in tracked:
                if product.get(field) in (None, "", []):
                    missing[field] += 1
    return {"exists": True, "valid": True, "is_list": True,
            "products": len(data), "missing": dict(missing)}


def build(root: Path) -> dict[str, Any]:
    paths = py_files(root)
    known = {p.stem for p in paths}
    known.update(module_name(root, p).split(".")[0] for p in paths)
    modules = [parse_module(root, p, known) for p in paths]

    imported_by: dict[str, list[str]] = defaultdict(list)
    for m in modules:
        for imp in m.local_imports:
            imported_by[imp.split(".")[0]].append(m.module)

    duplicate_functions: dict[str, list[str]] = defaultdict(list)
    for m in modules:
        for fn in m.functions:
            if not fn.startswith("_"):
                duplicate_functions[fn].append(m.module)
    duplicate_functions = {k: sorted(v) for k, v in duplicate_functions.items() if len(v) > 1}

    hashes: dict[str, list[str]] = defaultdict(list)
    for m in modules:
        hashes[m.sha256].append(m.path)
    duplicate_files = [v for v in hashes.values() if len(v) > 1]

    orphan = [m.module for m in modules
              if m.module.split(".")[0] not in imported_by and m.module != "couponworld" and not m.has_main]

    cats: dict[str, list[str]] = defaultdict(list)
    for m in modules:
        cats[m.category].append(m.path)

    project_import = re.compile(r"^(amazon_|batch_|build_|couponworld$|google_|intent_|internal_|inventory_|migrate_|price_|product_|recommendation_|remove_|seo_|shopping_|site_|image_)")
    missing_imports = []
    for m in modules:
        for imp in m.imports:
            root_name = imp.split(".")[0]
            if project_import.match(root_name) and root_name not in known:
                missing_imports.append({"module": m.module, "import": imp})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "summary": {
            "python_files": len(modules),
            "syntax_errors": sum(not m.syntax_ok for m in modules),
            "classes": sum(len(m.classes) for m in modules),
            "functions": sum(len(m.functions) for m in modules),
            "entrypoints": sum(m.has_main for m in modules),
            "duplicate_function_names": len(duplicate_functions),
            "duplicate_files": len(duplicate_files),
            "possible_orphans": len(orphan),
        },
        "important_files": {x: (root / x).exists() for x in IMPORTANT_FILES},
        "categories": {k: sorted(v) for k, v in sorted(cats.items())},
        "modules": [asdict(m) for m in modules],
        "dependency_graph": {m.module: m.local_imports for m in modules},
        "imported_by": {k: sorted(v) for k, v in sorted(imported_by.items())},
        "syntax_errors": [{"path": m.path, "error": m.syntax_error} for m in modules if not m.syntax_ok],
        "missing_local_imports": missing_imports,
        "duplicate_function_names": duplicate_functions,
        "duplicate_files": duplicate_files,
        "possible_orphan_modules": sorted(orphan),
        "coupon_data": coupons(root),
        "git": {"branch": git(root, "branch", "--show-current"),
                "status": git(root, "status", "--short")},
    }


def markdown(a: dict[str, Any]) -> str:
    s = a["summary"]
    out = [
        "# Coupon World System Audit", "",
        f"Generated: `{a['generated_at']}`", "",
        "## Summary", "",
        f"- Python files: **{s['python_files']}**",
        f"- Syntax errors: **{s['syntax_errors']}**",
        f"- Classes: **{s['classes']}**",
        f"- Functions: **{s['functions']}**",
        f"- Entrypoints: **{s['entrypoints']}**",
        f"- Exact duplicate files: **{s['duplicate_files']}**",
        f"- Repeated function names: **{s['duplicate_function_names']}**",
        f"- Possible orphan modules: **{s['possible_orphans']}**", "",
        "## Important Files", ""
    ]
    for p, ok in a["important_files"].items():
        out.append(f"- {'PASS' if ok else 'MISSING'} — `{p}`")
    out += ["", "## System Areas", ""]
    for cat, paths in a["categories"].items():
        out.append(f"### {cat}")
        out.extend(f"- `{p}`" for p in paths)
        out.append("")
    out += ["## Module Details", ""]
    for m in a["modules"]:
        out.append(f"### `{m['path']}`")
        out.append(f"- Status: **{'PASS' if m['syntax_ok'] else 'FAIL'}**")
        out.append(f"- Lines: {m['lines']} | Category: {m['category']}")
        if m["local_imports"]: out.append("- Uses: " + ", ".join(f"`{x}`" for x in m["local_imports"]))
        if m["classes"]: out.append("- Classes: " + ", ".join(f"`{x}`" for x in m["classes"]))
        if m["functions"]:
            shown = m["functions"][:20]
            out.append("- Functions: " + ", ".join(f"`{x}`" for x in shown) + (" ..." if len(m["functions"]) > 20 else ""))
        if m["cli_commands"]: out.append("- CLI commands: " + ", ".join(f"`{x}`" for x in m["cli_commands"]))
        if m["syntax_error"]: out.append(f"- Error: `{m['syntax_error']}`")
        out.append("")

    out += ["## Review Warnings", ""]
    if a["syntax_errors"]:
        out.append("### Syntax Errors")
        out.extend(f"- `{x['path']}` — {x['error']}" for x in a["syntax_errors"])
        out.append("")
    if a["missing_local_imports"]:
        out.append("### Missing Local Imports")
        out.extend(f"- `{x['module']}` imports `{x['import']}`" for x in a["missing_local_imports"])
        out.append("")
    if a["possible_orphan_modules"]:
        out.append("### Possible Orphan Modules")
        out.extend(f"- `{x}`" for x in a["possible_orphan_modules"])
        out.append("")
    if a["duplicate_files"]:
        out.append("### Exact Duplicate Files")
        out.extend("- " + ", ".join(f"`{x}`" for x in group) for group in a["duplicate_files"])
        out.append("")
    if a["duplicate_function_names"]:
        out.append("### Repeated Public Function Names")
        out.append("Repeated names are review indicators, not automatic bugs.")
        for fn, mods in sorted(a["duplicate_function_names"].items()):
            out.append(f"- `{fn}`: " + ", ".join(f"`{x}`" for x in mods))
        out.append("")

    c = a["coupon_data"]
    out += ["## Product Database", ""]
    if not c.get("exists"): out.append("- `coupons.json` missing")
    elif not c.get("valid"): out.append(f"- Invalid JSON: `{c.get('error')}`")
    elif not c.get("is_list"): out.append("- Root is not a list")
    else:
        out.append(f"- Products: **{c['products']}**")
        out.extend(f"- Missing `{k}`: **{v}**" for k, v in c["missing"].items())

    out += ["", "## Decision Rule", "",
            "Before making a new engine: check existing responsibility, extend the matching module, and create a new module only for a genuinely separate responsibility.", ""]
    return "\n".join(out)


def main() -> int:
    ns = args()
    root = Path(ns.root).resolve()
    if not root.exists():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2
    report = build(root)
    outdir = root / ns.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "system_audit.json"
    md_path = outdir / "system_audit.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")

    s = report["summary"]
    print("=" * 68)
    print("COUPON WORLD — SYSTEM AUDIT AGENT")
    print("=" * 68)
    print(f"Python files            : {s['python_files']}")
    print(f"Syntax errors           : {s['syntax_errors']}")
    print(f"Classes                 : {s['classes']}")
    print(f"Functions               : {s['functions']}")
    print(f"Entrypoints             : {s['entrypoints']}")
    print(f"Possible orphan modules : {s['possible_orphans']}")
    print(f"Duplicate files         : {s['duplicate_files']}")
    print(f"Report                  : {md_path}")
    print(f"JSON                    : {json_path}")
    print("AUDIT STATUS            : " + ("REVIEW REQUIRED" if s['syntax_errors'] or report['missing_local_imports'] else "PASS WITH REVIEW NOTES"))
    print("=" * 68)
    return 1 if s["syntax_errors"] or report["missing_local_imports"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
