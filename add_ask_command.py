from pathlib import Path
from datetime import datetime
import shutil

target = Path("python/couponworld.py")

if not target.exists():
    raise SystemExit("ERROR: python/couponworld.py not found")

text = target.read_text(encoding="utf-8-sig")

if 'def ask_command(' in text:
    print("ASK command already present. No change required.")
    raise SystemExit(0)

backup = target.with_name(
    f"couponworld_before_ask_{datetime.now():%Y%m%d_%H%M%S}.py"
)
shutil.copy2(target, backup)

# 1. Add ask_command before run_workflow
anchor_1 = "\ndef run_workflow(\n"

insert_1 = '''

def ask_command(
    query: str,
    json_output: bool = False,
) -> int:
    """Run the existing Shopping Brain through the control center."""
    command = [
        sys.executable,
        "python/shopping_brain.py",
    ]

    if json_output:
        command.append("--json")

    command.append(query)
    return run_command(command)


def run_workflow(
'''

if text.count(anchor_1) != 1:
    raise SystemExit(
        f"ERROR: run_workflow anchor count = {text.count(anchor_1)}"
    )

text = text.replace(anchor_1, insert_1, 1)

# 2. Add ask parser before run parser
anchor_2 = '''    run_parser = subparsers.add_parser(
        "run",
        help="Run the safe Coupon World master workflow",
    )
'''

insert_2 = '''    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask the Coupon World Shopping Brain",
    )

    ask_parser.add_argument(
        "query",
        nargs="+",
        help="Shopping query",
    )

    ask_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of formatted text",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run the safe Coupon World master workflow",
    )
'''

if text.count(anchor_2) != 1:
    raise SystemExit(
        f"ERROR: run parser anchor count = {text.count(anchor_2)}"
    )

text = text.replace(anchor_2, insert_2, 1)

# 3. Add ask dispatch before run dispatch
anchor_3 = '''    if args.command == "run":
        return run_workflow(
'''

insert_3 = '''    if args.command == "ask":
        return ask_command(
            " ".join(args.query).strip(),
            args.json,
        )

    if args.command == "run":
        return run_workflow(
'''

if text.count(anchor_3) != 1:
    raise SystemExit(
        f"ERROR: run dispatch anchor count = {text.count(anchor_3)}"
    )

text = text.replace(anchor_3, insert_3, 1)

target.write_text(text, encoding="utf-8", newline="\n")

print("PASS: ASK command added")
print("Backup:", backup)
print("Updated:", target)
