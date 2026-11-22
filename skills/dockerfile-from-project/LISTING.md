# dockerfile-from-project

## One line

Drafts a Dockerfile and .dockerignore from a pasted package.json, requirements.txt or go.mod plus its entry file, with every assumption listed in a table.

## What it does

The skill takes the manifest and entry file a user pastes and follows a fixed procedure. It identifies the runtime from the manifest, copies the start command from the scripts block into exec form, and reads the port from a literal in the source. It chooses a single-stage or two-stage build depending on whether a build script exists, picks the install command depending on whether a lockfile was supplied, and runs the container as a non-root user. The .dockerignore comes from a fixed list per runtime. Each decision is tagged IN-FILE, RULE or TO-CONFIRM in an Assumptions table that names its source. Values the files do not contain, such as the base image pin, a missing lockfile or a missing port, are not filled in. They appear as open questions instead. The output always has six sections in the same order, so a reviewer can check each line against the file it came from.

## When to use

- A user has a small Node.js, Python or Go service with no Dockerfile and wants a starting draft.
- The user wants to see which lines came from their own files and which came from a default rule.
- The user will read the draft, resolve the TO-CONFIRM rows and build the image on their own machine.

## When not to use

- Kubernetes manifests, Compose files, CI pipelines or deployment steps.
- Projects whose manifest is not package.json, requirements.txt or go.mod. A pyproject.toml without a requirements.txt is refused, because the skill cannot write a pinned install line from it.
- Images that need credentials or a private registry at build time. The skill never writes secret values.
- Security review or scanning of an image. The skill does not inspect base layers or packages.

## Requirements

A text-capable agent. The skill needs no shell, no network and no file access. The user pastes the manifest and the entry file into the conversation, and the agent works only on that text.

## Example

The output below comes from applying SKILL.md by hand to the two fixture files, a package.json with a start script and engines.node set to ">=20", and a server.js excerpt that reads PORT with a default of 4100.

````markdown
## Inventory

| File | Role | Used for |
|---|---|---|
| package.json | manifest | runtime, start command, build check, install command, devDependencies |
| server.js | entry | port, environment names |

## Dockerfile

```dockerfile
# A-01 TO-CONFIRM: pin an exact tag or digest for node:20-alpine
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
# A-06 TO-CONFIRM: no package-lock.json was supplied
RUN npm install --omit=dev
COPY . .
EXPOSE 4100
USER node
CMD ["node", "server.js"]
```

## .dockerignore

```
node_modules
.git
.env
*.log
Dockerfile
.dockerignore
```

## Assumptions

| ID | Item | Value | Source | Status |
|---|---|---|---|---|
| A-01 | Base image pin | node:20-alpine | package.json "engines.node": ">=20" (smallest major 20) | TO-CONFIRM |
| A-02 | Runtime | Node.js | package.json supplied | IN-FILE |
| A-03 | Entry command | CMD ["node", "server.js"] | package.json "scripts.start": "node server.js" | IN-FILE |
| A-04 | Port | EXPOSE 4100 | server.js "process.env.PORT || 4100" | IN-FILE |
| A-05 | Build stage | single stage | package.json has no "scripts.build" | IN-FILE |
| A-06 | Install command | npm install --omit=dev | no package-lock.json supplied | TO-CONFIRM |
| A-07 | Run user | node | Node.js rule, step 2 | RULE |
| A-08 | Working directory and copy order | /app; package.json copied before the rest | rule, step 7 | RULE |
| A-09 | Environment name | DATABASE_URL, name only, not set | server.js "process.env.DATABASE_URL" | IN-FILE |
| A-10 | .dockerignore | Node.js list | rule, step 9 | RULE |

## Open questions

1. A-01: Which exact tag or digest should node:20-alpine be pinned to?
2. A-06: Is there a package-lock.json to supply, so that npm ci can replace npm install?

## Status

partial
````

## Limits

- The base image is never pinned. Row A-01 stays TO-CONFIRM in every draft.
- The skill does not build the image, run the container or check that the app starts.
- It does not check whether the port is free, whether the environment names are set at run time, or whether the start command works outside the container.
- It reads only the text pasted into the conversation. A file that was not pasted is treated as unknown, and a build step named only in a file that was not supplied is not detected.
- Lockfile detection covers package-lock.json only. A yarn.lock or pnpm-lock.yaml is ignored.
- It does not judge image size, cost, base-image vulnerabilities or runtime security.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
