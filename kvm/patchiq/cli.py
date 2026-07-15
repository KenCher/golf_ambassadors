#!/usr/bin/env python3
"""
PatchIQ — Command-line interface.

Usage:
  # Review a patch file
  python -m patchiq.cli patch my_fix.patch

  # Review a git commit
  python -m patchiq.cli commit HEAD

  # Review a git range
  python -m patchiq.cli range origin/main..HEAD

  # Pipe a diff directly
  git diff HEAD~1 | python -m patchiq.cli pipe
"""

import argparse
import subprocess
import sys
import os

from patchiq.analyzer import review_patch
from patchiq.report import generate_html


def _run_git(*args) -> str:
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, check=True
    )
    return result.stdout


def print_terminal_report(result):
    """Print a readable summary to stdout."""
    SEV_ICON = {"error": "🔴", "warning": "🟡", "info": "🔵"}
    bar = "─" * 70

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                     🔎 PatchIQ Review                          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"\n  Patch : {result.patch_subject}")
    print(f"  Files : {len(result.files)}")
    print(f"  Score : {result.score}/100")
    print()

    if result.findings:
        print(f"  {bar}")
        print(f"  FINDINGS ({len(result.findings)})")
        print(f"  {bar}")
        for f in result.findings:
            icon = SEV_ICON.get(f.severity, "⚪")
            print(f"  {icon} [{f.rule_id}] ({f.layer}) {f.message}")
            if f.line:
                print(f"       ↳ {f.line[:90].strip()}")
        print()
    else:
        print("  ✅ No style issues found\n")

    print(f"  {bar}")
    print("  AI SUMMARY")
    print(f"  {bar}")
    print(f"  {result.ai_summary}")
    print()

    if result.ai_suggestions:
        print("  SUGGESTIONS")
        for i, s in enumerate(result.ai_suggestions, 1):
            print(f"  {i}. {s}")
        print()


def cmd_patch(args):
    raw = open(args.file).read()
    result = review_patch(raw)
    print_terminal_report(result)
    if args.html:
        path = args.html
        generate_html(result, path)
        print(f"  📄 HTML report saved to: {path}\n")


def cmd_commit(args):
    raw = _run_git("show", "--format=Subject: %s%n", args.ref)
    result = review_patch(raw)
    print_terminal_report(result)
    if args.html:
        generate_html(result, args.html)
        print(f"  📄 HTML report saved to: {args.html}\n")


def cmd_range(args):
    raw = _run_git("diff", args.range)
    result = review_patch(raw)
    print_terminal_report(result)
    if args.html:
        generate_html(result, args.html)
        print(f"  📄 HTML report saved to: {args.html}\n")


def cmd_pipe(args):
    raw = sys.stdin.read()
    if not raw.strip():
        print("❌ No diff received on stdin", file=sys.stderr)
        sys.exit(1)
    result = review_patch(raw)
    print_terminal_report(result)
    if args.html:
        generate_html(result, args.html)
        print(f"  📄 HTML report saved to: {args.html}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="patchiq",
        description="PatchIQ — AI-powered patch review for KVM/Linux/QEMU/libvirt"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # patch subcommand
    p_patch = sub.add_parser("patch", help="Review a .patch file")
    p_patch.add_argument("file", help="Path to the patch file")
    p_patch.add_argument("--html", metavar="OUT", help="Save HTML report to file")
    p_patch.set_defaults(func=cmd_patch)

    # commit subcommand
    p_commit = sub.add_parser("commit", help="Review a git commit")
    p_commit.add_argument("ref", nargs="?", default="HEAD", help="Git ref (default: HEAD)")
    p_commit.add_argument("--html", metavar="OUT", help="Save HTML report to file")
    p_commit.set_defaults(func=cmd_commit)

    # range subcommand
    p_range = sub.add_parser("range", help="Review a git commit range")
    p_range.add_argument("range", help="Git range e.g. origin/main..HEAD")
    p_range.add_argument("--html", metavar="OUT", help="Save HTML report to file")
    p_range.set_defaults(func=cmd_range)

    # pipe subcommand
    p_pipe = sub.add_parser("pipe", help="Review a diff from stdin")
    p_pipe.add_argument("--html", metavar="OUT", help="Save HTML report to file")
    p_pipe.set_defaults(func=cmd_pipe)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
