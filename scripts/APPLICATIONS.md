---
published: false
---

# Job application resumes

This file is not published on the site. Read it before customizing a resume for a job posting. Use `scripts/new_application.py` from the branch that added it until that change is on `main`. The public repository owns the generator and this workflow. The private repository `benrobot/benrobot.github.io.private` only stores the finished application folders.

## Decisions already made

- Each application is a folder on `main` in the private repository, not a branch.
- Folder name: `applications/YYYY-MM-DD-company-role/`. The date is the day the resume is customized. Use lowercase hyphens. Do not rename a folder after it is created.
- The folder contains `posting.md`, `resume.yml`, `notes.md`, `benjamin-roedell-resume.docx`, and `benjamin-roedell-resume.pdf`.
- `applications/index.md` is a table of those folders. Status stays in each `notes.md` (`draft`, `applied`, `screen`, `interview`, `offer`, `closed`).
- `resume.yml` in the folder is a full copy of the customized source. It must not contain an email address or a phone number.
- The Word and PDF files get the contact line at build time from `RESUME_EMAIL` and `RESUME_PHONE`, or from `--contact`. That line is `Tampa, FL · email · phone` on the existing location line.
- The root files `benjamin-roedell-resume-private.docx` and `.pdf` stay the canonical private resume. `.github/workflows` in the private repo, via `scripts/publish_private_resume.sh`, commits only those two files and leaves `applications/` alone.
- Do not commit application folders, contact files, or private resumes to `benrobot/benrobot.github.io`.

## What an agent changes

Start from the current public `_data/resume.yml`. Do not start from a previous application's `resume.yml`.

These fields may change to match the posting:

- `download.headline`
- `intro_blurb`
- the order of `skills`
- the order of bullets, and which bullets are listed in `download_description`

Move a skill forward, or from `parked` into `skills`, only when the experience text already supports it. Dates, employers, and job titles stay as they are. The Mad Mobile title stays Solution Architect. Do not invent metrics, tools, or employers.

Use `download.headline` for the role family in the posting. Software Architect and Engineer is the default. Use Solution Architect only when that is the posting's title.

After generation, the PDF must be 2 pages. If `new_application.py` prints a page-count warning, shorten the summary or the bullet selection and run it again before committing. Delete the rejected folder first, because the script will not overwrite an existing folder.

## Commands

From a checkout of the public repository, with the private repository checked out separately:

```sh
python3 scripts/new_application.py \
  --dest /path/to/benrobot.github.io.private \
  --company "Acme" \
  --role "Software Architect" \
  --url "https://example.com/job" \
  --posting /tmp/acme-posting.md \
  --resume /tmp/acme-resume.yml \
  --contact private/contact.yml
```

`--resume` defaults to `_data/resume.yml`. `--contact` may be omitted when `RESUME_EMAIL` and `RESUME_PHONE` are set. Never print those values. Never commit `private/contact.yml`.

`posting.md` is the job text the user pasted, unchanged, with the URL at the top when they supplied one. `notes.md` records the public commit in `Source commit`. The user fills in the communication log.

Show the headline, summary, and skill-order changes in the session, then commit and push only the `applications/` folder on `main` of the private repository. The public site does not need a commit for an application.

## Regenerating one folder

`scripts/generate_resume.py --resume <folder>/resume.yml --docx <folder>/benjamin-roedell-resume.docx` rebuilds the Word file from the saved source. Convert with LibreOffice the same way `new_application.py` does. The public commit in `notes.md` is the generator version that first built the folder.
