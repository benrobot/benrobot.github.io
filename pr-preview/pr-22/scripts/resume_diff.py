#!/usr/bin/env python3
"""Write resume.diff for one application folder.

resume.yml stays a full copy so the Word file can be rebuilt. resume.diff
shows how that copy differs from the public _data/resume.yml at the source
commit recorded in notes.md.
"""

import argparse
import difflib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIFF_NAME = "resume.diff"


def source_commit_from_notes(folder):
    notes = folder / "notes.md"
    if not notes.is_file():
        return ""
    for line in notes.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Source commit:"):
            return line.split(":", 1)[1].strip()
    return ""


def public_resume_text(commit):
    if commit:
        try:
            return subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"{commit}:_data/resume.yml"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                f"Could not read _data/resume.yml at {commit}. Comparing with the working tree.",
                file=sys.stderr,
            )
    path = ROOT / "_data" / "resume.yml"
    if not path.is_file():
        raise SystemExit(f"Public resume not found: {path}")
    return path.read_text(encoding="utf-8")


def write_resume_diff(folder, commit=""):
    folder = Path(folder)
    resume = folder / "resume.yml"
    if not resume.is_file():
        raise SystemExit(f"Resume file not found: {resume}")
    if not commit:
        commit = source_commit_from_notes(folder)
    baseline = public_resume_text(commit)
    current = resume.read_text(encoding="utf-8")
    label = commit or "working tree"
    diff = "".join(
        difflib.unified_diff(
            baseline.splitlines(keepends=True),
            current.splitlines(keepends=True),
            fromfile=f"_data/resume.yml ({label})",
            tofile="resume.yml",
        )
    )
    text = (
        f"Differences from the public _data/resume.yml at {label}.\n"
        "resume.yml in this folder is the full customized source.\n"
        "\n"
    )
    text += diff if diff else "No differences.\n"
    if not text.endswith("\n"):
        text += "\n"
    path = folder / DIFF_NAME
    path.write_text(text, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description="Write resume.diff for an application folder.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--commit", default="", help="Public commit to compare. Defaults to notes.md.")
    args = parser.parse_args()
    folder = args.folder if args.folder.is_absolute() else Path.cwd() / args.folder
    print(write_resume_diff(folder.resolve(), args.commit.strip()))


if __name__ == "__main__":
    main()
