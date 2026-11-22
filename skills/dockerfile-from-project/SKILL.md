---
name: dockerfile-from-project
description: Drafts a Dockerfile and .dockerignore from project files the user supplies, with every assumption listed in a table. Use when the user asks for a Dockerfile for a small Node.js, Python or Go project and has pasted the manifest and the entry file. Do not use for Kubernetes manifests, Compose files, CI pipelines, image security scanning or production deployment. The draft never invents ports, secrets or commands that the supplied files do not contain.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Dockerfile from project files

Drafts one Dockerfile and one .dockerignore from text the user pastes into the conversation. Every value in the draft is one of three kinds: IN-FILE (read from a supplied file), RULE (set by a fixed rule in this skill) or TO-CONFIRM (missing or uncertain). The skill has no shell, no network and no file access. It works only on the supplied text.

## Required intake

1. A manifest: package.json (Node.js), requirements.txt (Python), or go.mod (Go). A pyproject.toml alone is not enough; see the Stop rules.
2. An entry point: the "start" script in package.json, a Python file with an `if __name__ == "__main__":` guard, or a Go main package in the root directory.
3. The full text of every file that the entry point or the start script names.

If any intake item is missing, follow the Stop rules.

## Workflow

1. Inventory the supplied files. Record each file with its role (manifest, entry, config, other) and what it is used for. A file that was not supplied is never assumed to exist. Output: the Inventory table.
2. Detect the runtime from the manifest. Use the table below. Any other manifest (pom.xml, Gemfile, Cargo.toml, composer.json) triggers the Stop rules. Output: one runtime value, with its A-row.

   | Manifest supplied | Runtime | Base image rule | Run user |
   |---|---|---|---|
   | package.json | Node.js | node:<major>-alpine, where major is the smallest major number in engines.node; if engines.node is missing, node:TO-CONFIRM-alpine | node (RULE) |
   | requirements.txt | Python | python:TO-CONFIRM-slim, because requirements.txt names no Python version | app, uid 10001 (RULE) |
   | go.mod | Go | build stage golang:<go directive>-alpine; run stage alpine:TO-CONFIRM | app, uid 10001 (RULE) |

3. Set the entry command. Node.js: copy the scripts.start command exactly and write it in exec form, for example "node server.js" becomes CMD ["node", "server.js"]. If there is no start script, use the main field only when that file is supplied, and mark the row TO-CONFIRM. Python: CMD ["python", "<file>"] only when that file contains the `__main__` guard. Go: build with `go build -o /out/app .` and run CMD ["/out/app"]. If no rule applies, stop.
4. Set the port. Search the supplied text, in this order, for the first literal: `process.env.PORT || N`, `listen(N`, `EXPOSE N`, `PORT=N`. Write EXPOSE N. If no literal exists, write no EXPOSE line and mark the port row TO-CONFIRM. Never write 80, 3000 or 8080 as a default.
5. Set the build stage. Node.js with a scripts.build entry: two stages. The builder stage runs the install and `npm run build`. The run stage copies the output directory named in the build script or in tsconfig outDir, if supplied; if neither is supplied, use dist and mark it TO-CONFIRM. Node.js without a build entry: one stage. Python: one stage. Go: two stages, always.
6. Set the install command from the table below.

   | Supplied | Command | Status |
   |---|---|---|
   | package.json and package-lock.json | npm ci --omit=dev | IN-FILE |
   | package.json, no package-lock.json | npm install --omit=dev | TO-CONFIRM |
   | requirements.txt, every line pinned with == | pip install -r requirements.txt --no-cache-dir | IN-FILE |
   | requirements.txt, any line without == | pip install -r requirements.txt --no-cache-dir; that unpinned line is a TO-CONFIRM row | TO-CONFIRM |
   | go.mod and go.sum | go mod download | IN-FILE |
   | go.mod, no go.sum | go mod download | TO-CONFIRM |

   In a Node.js builder stage (two-stage build), run `npm ci` (or `npm install`) without --omit=dev, so that build tools are installed. The run stage keeps the --omit=dev command from the table.

7. Lay out the Dockerfile in this fixed order, one instruction each: WORKDIR /app; COPY of the manifest files only; RUN of the install command; COPY . .; EXPOSE if step 4 found a port; USER with the run user; CMD. For Python and Go, insert `RUN adduser -D -u 10001 app` (alpine) or `RUN useradd -u 10001 app` (slim) directly before USER, and record it as a RULE row (rule, step 7). Each TO-CONFIRM row gets a comment in the Dockerfile that starts with its ID.
8. List environment names. Collect every name read in the supplied files (process.env.NAME, os.environ["NAME"], os.getenv("NAME"), os.Getenv("NAME")), except PORT when step 4 used it. Each name gets a row with the value "name only, not set" and status IN-FILE. Never write ENV or ARG with a value. A name that contains KEY, SECRET, TOKEN, PASSWORD or CREDENTIAL gets the note "supply at run time, never in the image".
9. Write the .dockerignore from the fixed list for the runtime. Add a further line only when a supplied file names that path, and mark it IN-FILE.

   | Runtime | Lines, in this order |
   |---|---|
   | Node.js | node_modules, .git, .env, *.log, Dockerfile, .dockerignore |
   | Python | __pycache__/, .venv/, .git, .env, *.pyc, Dockerfile, .dockerignore |
   | Go | .git, .env, bin/, Dockerfile, .dockerignore |

10. Build the Assumptions table. It has one row per decision in steps 2 to 9. Number rows A-01, A-02 and so on in step order. A-01 is always the base image pin, which is always TO-CONFIRM. The Source column names the file and quoted key or line, or "rule, step N" for RULE rows.
11. Check consistency before output. Each TO-CONFIRM row must appear in the Open questions list, and each TO-CONFIRM row that changes a Dockerfile line must also have a comment in the Dockerfile. Each IN-FILE row must name a source that was actually pasted. Each Dockerfile line must map to an A-row or to a fixed-layout instruction from step 7. Fix any mismatch before writing the output.
12. Set the Status. complete: the only TO-CONFIRM row is A-01. partial: at least one other row is TO-CONFIRM. blocked: a Stop rule fired and no Dockerfile was written.

## Output contract

Produce exactly these six H2 headings, in this order, and no others:

1. `## Inventory`: table with columns File | Role | Used for.
2. `## Dockerfile`: one fenced block with the dockerfile language tag, or "Not produced." when blocked.
3. `## .dockerignore`: one fenced block, or "Not produced." when blocked.
4. `## Assumptions`: table with columns ID | Item | Value | Source | Status. Status is IN-FILE, RULE or TO-CONFIRM. When blocked, write "Not produced."
5. `## Open questions`: numbered list, one item per TO-CONFIRM row, written as "A-06: <question>", plus one item per refused clause, written as "Refused: <request>". Write "None." when there are neither.
6. `## Status`: one word, complete, partial or blocked.

## Stop rules

Stop with status blocked, and return a numbered list of questions under Open questions, when:

- the supplied files contain no manifest from the intake list, or the user supplied no files;
- the only Python manifest is pyproject.toml, which has no pinned install line this skill can write;
- step 3 finds no entry point;
- the start script or the entry file names a file that was not supplied.

Refuse only the clause that breaks a rule, keep the rest of the draft, set status partial and list the refused item under Open questions, when:

- the user asks for a port, host name, secret value or credential that no supplied file contains;
- the user asks for a command that no supplied manifest script contains, other than the install and build lines from steps 5 and 6;
- the user asks for a Kubernetes manifest, Compose file, CI pipeline or deployment step, which is outside this skill;
- the user asks for the container to run as root. Keep the USER line from step 2 and list the request as refused.

When the user asks for a secret to be written into ENV or ARG, refuse that clause, write no value, and keep the environment name row from step 8.

## Shipped files

- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text for this skill.
- [fixtures/package.json](fixtures/package.json) and [fixtures/server.js](fixtures/server.js): the offline smoke pair. Paste both into a session to reproduce the example in the listing.
