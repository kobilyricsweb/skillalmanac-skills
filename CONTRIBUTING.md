# Contributing

Issues and pull requests are welcome.

- **Fix or improve a skill:** change files under `skills/<slug>/` and open a pull request describing what was wrong and what changed. Keep `SKILL.md` frontmatter to open-spec fields (`name`, `description`, `license`, `compatibility`, `metadata`).
- **Propose a new skill:** open an issue first with the task it covers and the requests that should trigger it.
- **Every change goes through the site's evaluation.** A merged change is re-scored at skillalmanac.com under the published [method](https://skillalmanac.com/methodology); scores can go down as well as up. Add or update cases in `evals/` with your change.
- **No secrets.** Fixtures with fake secrets belong only in `evals/` and must be obviously fake. Run `node tools/secrets_scan.cjs` before you push; it fails on any hit outside `evals/`.
- **Licence:** contributions are Apache-2.0, as the rest of the repository.
- After changing skills, regenerate the index: `node tools/build_catalog.cjs`.
