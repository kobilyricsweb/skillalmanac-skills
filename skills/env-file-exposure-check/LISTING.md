# env-file-exposure-check

## One line

Scans one local project folder for environment files, key files and secret-shaped text, and reports each hit with its line number and a masked value.

## What it does

The skill runs a standard-library Python scanner on a folder you name. The scanner lists up to 5000 files, flags names such as `.env*`, `*.pem`, `id_rsa` and `credentials*`, and checks each file's text against four patterns: AWS access key IDs, PEM private key headers, GitHub personal tokens and key=value lines with a long value. Every flagged file is checked against the root `.gitignore` with simple glob rules, so a secret file that is already ignored is reported as a note while one that is not ignored is reported as an exposure. The output is one JSON object. The agent turns it into a status, a findings table and a remediation list. Full secret values are never printed; token-shaped matches show the first four characters and `***`, and key=value matches show only the value's length.

## When to use

Use it before pushing a repository, before a release, or after someone asks whether a `.env` file has been tracked. It also helps when a folder was copied from another machine and its `.gitignore` may be incomplete.

## When not to use

It does not read git history, so a secret that was committed and later deleted will not appear. It does not query cloud accounts to see whether a key is still live. It does not check dependencies for known vulnerabilities, and it does not look at code logic.

## Requirements

Python 3.9 or newer, standard library only. No network access and no packages to install. It reads the folder and never writes to it.

## Example

Smoke run on a three-file folder: a `.env` with a fake AWS-shaped key that is not listed in `.gitignore`, a `.gitignore` for other entries, and one clean text file. Output copied verbatim from the run; the temp path differs on each run.

```json
{
  "tool": "env_exposure",
  "root": "<local-path>",
  "gitignore_present": true,
  "files_visited": 3,
  "files_content_scanned": 3,
  "files_skipped": 0,
  "truncated": false,
  "exposure_count": 1,
  "findings": [
    {
      "file": ".env",
      "ignored_by_gitignore": false,
      "reasons": [
        "sensitive_filename",
        "aws_access_key_id"
      ],
      "matches": [
        {
          "line": 2,
          "pattern": "aws_access_key_id",
          "masked": "AKIA***"
        }
      ]
    }
  ]
}
```

The process exits with code 1 because one exposure was found.

## Limits

Only the root `.gitignore` is read, and its glob rules are simplified: a parent directory excluded by a rule cannot be re-included by a later negation in this scanner, which git does enforce. The key=value pattern uses a 16-character working threshold and will report some placeholders, so those hits need a human check. Files over 2 MB, binary files and files that are not valid UTF-8 are not content-scanned. The walk stops at 5000 files and at depth 12. Symbolic links are not followed.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
