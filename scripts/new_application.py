#!/usr/bin/env python3
"""Create one job-application folder in the private resume repository.

Formatting stays in generate_resume.py. This script only copies the customized
source, writes the posting and notes, and builds the Word and PDF files.
It does not commit.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from resume_diff import write_resume_diff

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_resume.py"
DOCX_NAME = "benjamin-roedell-resume.docx"
PDF_NAME = "benjamin-roedell-resume.pdf"


def slug(value, limit=48):
    text = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    text = text[:limit].strip("-")
    if not text:
        raise SystemExit(f"Could not make a folder name from {value!r}.")
    return text


def source_commit():
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def require_contact(contact_path):
    if contact_path:
        loaded = load_contact(contact_path)
        if loaded:
            return
    if os.environ.get("RESUME_EMAIL", "").strip() or os.environ.get("RESUME_PHONE", "").strip():
        return
    raise SystemExit(
        "Set RESUME_EMAIL and RESUME_PHONE, or pass --contact. "
        "Application resumes need the private contact line."
    )


def load_contact(path):
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        return False
    return bool(str(loaded.get("email") or "").strip() or str(loaded.get("phone") or "").strip())


def write_posting(folder, posting_path, url):
    body = posting_path.read_text(encoding="utf-8")
    if url and url not in body:
        body = f"URL: {url}\n\n{body}"
    if not body.endswith("\n"):
        body += "\n"
    (folder / "posting.md").write_text(body, encoding="utf-8")


def write_notes(folder, company, role, url, when, commit):
    text = (
        f"# {company} — {role}\n"
        f"- URL: {url}\n"
        "- Status: draft\n"
        "- Applied:\n"
        "- Contact:\n"
        f"- Source commit: {commit}\n"
        "- Changes: resume.diff\n"
        "\n"
        "## Log\n"
        f"- {when}: Resume customized.\n"
    )
    (folder / "notes.md").write_text(text, encoding="utf-8")


def upsert_index(path, row):
    header = [
        "# Applications",
        "",
        "Status for each application lives in that folder's notes.md.",
        "",
        "| Date | Company | Role | Status | Folder |",
        "| --- | --- | --- | --- | --- |",
    ]
    folder_name = row.rsplit("|", 2)[-2].strip()
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or line.startswith("| Date") or line.startswith("| ---"):
                continue
            if f"| {folder_name} |" in line:
                continue
            rows.append(line)
    rows.append(row)
    rows.sort()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(header + rows) + "\n", encoding="utf-8")


def build_files(folder, contact_path):
    docx = folder / DOCX_NAME
    command = [
        sys.executable,
        str(GENERATOR),
        "--resume",
        str(folder / "resume.yml"),
        "--docx",
        str(docx),
    ]
    if contact_path:
        command.extend(["--contact", str(contact_path)])
    subprocess.run(command, check=True, cwd=ROOT)
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(folder), str(docx)],
        check=True,
    )
    pdf = folder / PDF_NAME
    if not pdf.is_file():
        raise SystemExit(f"PDF was not written: {pdf}")
    try:
        info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pdfinfo is unavailable, so the page count was not checked.")
        return
    pages = ""
    for line in info.splitlines():
        if line.startswith("Pages:"):
            pages = line.split()[-1]
    print(f"PDF pages: {pages}")
    if pages != "2":
        print("WARNING: the application PDF is not 2 pages. Tighten the wording before commit.")


def main():
    parser = argparse.ArgumentParser(description="Create a job-application resume folder.")
    parser.add_argument("--dest", type=Path, required=True, help="Private repository root.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--posting", type=Path, required=True, help="Job posting text to copy unchanged.")
    parser.add_argument("--url", default="", help="Posting URL. Written at the top of posting.md when missing.")
    parser.add_argument("--resume", type=Path, help="Customized resume YAML. Defaults to _data/resume.yml.")
    parser.add_argument("--contact", type=Path, help="Untracked YAML with email and phone.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Folder date, YYYY-MM-DD.")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("--date must be YYYY-MM-DD.")
    dest = args.dest if args.dest.is_absolute() else Path.cwd() / args.dest
    dest = dest.resolve()
    root = ROOT.resolve()
    if dest == root or root in dest.parents:
        raise SystemExit("Refusing to write application folders into the public repository.")
    posting = args.posting if args.posting.is_absolute() else Path.cwd() / args.posting
    if not posting.is_file():
        raise SystemExit(f"Posting file not found: {posting}")
    resume_src = args.resume if args.resume else ROOT / "_data" / "resume.yml"
    if not resume_src.is_absolute():
        resume_src = Path.cwd() / resume_src
    if not resume_src.is_file():
        raise SystemExit(f"Resume file not found: {resume_src}")
    contact = None
    if args.contact:
        contact = args.contact if args.contact.is_absolute() else Path.cwd() / args.contact
        if not contact.is_file():
            raise SystemExit(f"Contact file not found: {contact}")
    require_contact(contact)

    folder_name = f"{args.date}-{slug(args.company)}-{slug(args.role)}"
    folder = dest / "applications" / folder_name
    if folder.exists():
        raise SystemExit(f"Application folder already exists: {folder}")

    folder.mkdir(parents=True)
    (folder / "resume.yml").write_text(resume_src.read_text(encoding="utf-8"), encoding="utf-8")
    commit = source_commit()
    write_posting(folder, posting, args.url.strip())
    write_notes(folder, args.company.strip(), args.role.strip(), args.url.strip(), args.date, commit)
    write_resume_diff(folder, commit)
    build_files(folder, contact)

    company = args.company.replace("|", "/")
    role = args.role.replace("|", "/")
    upsert_index(
        dest / "applications" / "index.md",
        f"| {args.date} | {company} | {role} | draft | {folder_name} |",
    )
    print(folder)


if __name__ == "__main__":
    main()
