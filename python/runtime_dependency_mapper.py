#!/usr/bin/env python3

from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parent
files = sorted(ROOT.glob("*.py"))


def main() -> int:
    print("=" * 70)
    print("COUPON WORLD RUNTIME DEPENDENCY MAP")
    print("=" * 70)

    for file in files:
        print(f"\n{file.name}")

        try:
            source = file.read_text(encoding="utf-8-sig")
            tree = ast.parse(source)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            continue

        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        for imported_module in sorted(set(imports)):
            print(f"   -> {imported_module}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())