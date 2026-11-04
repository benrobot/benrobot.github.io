#!/bin/sh
# Build the private Word and PDF resumes from private/contact.yml.
# That file stays untracked. This does not change the public resume files.
set -eu
cd "$(dirname "$0")/.."
if [ ! -f private/contact.yml ]; then
  echo "Create private/contact.yml with email and phone first." >&2
  exit 1
fi
python3 scripts/generate_resume.py --contact private/contact.yml
soffice --headless --convert-to pdf --outdir private private/benjamin-roedell-resume.docx
