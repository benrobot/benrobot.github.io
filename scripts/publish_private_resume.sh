#!/bin/bash
# Build the private resume and commit it in the private repository.
# The private workflow checks out this script from the public repository.
set -euo pipefail

if [ "${GITHUB_ACTIONS:-}" != "true" ]; then
  echo "This script runs from the private resume workflow." >&2
  exit 1
fi

public_dir="${PUBLIC_SITE_DIR:-public-site}"
if [ ! -f "${public_dir}/scripts/generate_resume.py" ]; then
  echo "The public resume checkout is missing at ${public_dir}." >&2
  exit 1
fi

if [ -z "${RESUME_EMAIL:-}" ] || [ -z "${RESUME_PHONE:-}" ]; then
  echo "RESUME_EMAIL or RESUME_PHONE is empty. The private file will omit a missing value." >&2
fi

sudo apt-get update
sudo apt-get install -y libreoffice-writer fonts-crosextra-carlito
mkdir -p "${HOME}/.config/fontconfig"
cat > "${HOME}/.config/fontconfig/fonts.conf" <<'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias>
    <family>Calibri</family>
    <prefer><family>Carlito</family></prefer>
  </alias>
</fontconfig>
EOF
fc-cache -f

python3 -m pip install --user python-docx pyyaml
python3 "${public_dir}/scripts/generate_resume.py" \
  --docx benjamin-roedell-resume-private.docx
soffice --headless --convert-to pdf --outdir . benjamin-roedell-resume-private.docx
rm -rf "${public_dir}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add benjamin-roedell-resume-private.docx benjamin-roedell-resume-private.pdf
if git diff --cached --quiet; then
  echo "Private resume files are unchanged."
  exit 0
fi
git commit -m "Update the private resume"

branch="$(git branch --show-current)"
for attempt in 1 2 3 4 5; do
  if git push origin "HEAD:${branch}"; then
    exit 0
  fi
  echo "Push was rejected. Rebasing onto the latest ${branch}."
  git fetch --depth=50 origin "${branch}"
  if ! git rebase "origin/${branch}"; then
    git rebase --abort
    echo "Could not rebase the private resume commit."
    exit 1
  fi
done
echo "Could not push the private resume commit."
exit 1
