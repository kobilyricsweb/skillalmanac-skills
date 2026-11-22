# Doc type skeletons

Read only the part for the type you are writing. Headings are worded so the audit accepts them.

## Contents

- Where the split comes from
- readme
- reference
- how-to
- tutorial
- explanation
- runbook
- Last-verified line

## Where the split comes from

The four-way split of tutorial, how-to, reference and explanation is the Diataxis framework (https://diataxis.fr/). It separates pages by what the reader is doing: studying, working, looking up or understanding. README and runbook are added here because both are common and each has a fixed job: orient a newcomer, and help someone fix a live problem. The required sections below are this skill's own working choices, not part of that framework.

## readme

```markdown
# Name

One to three sentences: what it is, who it is for, what it is not.

## Install
Pinned install command in a bash block, then the supported versions.

## Usage
The smallest real example, with its real output.

## Documentation
Links to the how-to, reference and explanation pages.

## License
Name and link.
```

The first working command appears within 40 lines. Badges and tables of contents are optional and never replace the intro sentence.

## reference

One entry per item (endpoint, option, function), in a fixed order, with no narrative. Each entry: signature or route, parameters in a table (name, type, required, default, meaning), the response or return value, then the failures.

```markdown
# <Thing> reference
Last verified: YYYY-MM-DD against <version>

## Endpoints (or Parameters, Methods)
### POST /v1/items
| Parameter | Type | Required | Default | Meaning |

## Errors
| Status or code | Meaning | What the caller does |

## Examples
A request and the real response.
```

Generate reference from the source (an OpenAPI file, docstrings, `--help`) where a generator exists, and write only the prose around it.

## how-to

```markdown
# <Verb> <object>   (for example: Rotate the signing key)
Last verified: YYYY-MM-DD against <version>

## Prerequisites
Access, roles, tools with versions.

## Steps
1. Imperative sentence, then the command in a fenced block.

## Verify
The command that proves it worked, and its real output.

## Troubleshooting (optional)
Symptom, cause, fix; three entries at most.
```

Start the title with a verb, not "About X". 3 to 12 steps. Choices ("if you use X, do this") are rare; with more than two branches, write one how-to per branch.

## tutorial

Like a how-to, but the reader may know nothing, so every step shows its output and the path ends in something that works. Sections: What you will build, Prerequisites, Steps, Summary or Next steps. No options and no digressions; link to explanation pages instead.

## explanation

Sections: Background (the problem), How it works (the design in prose, one diagram if it helps), Trade-offs (what was given up, alternatives rejected). No commands the reader is expected to run. No verified line needed, but name the version the description applies to.

## runbook

```markdown
# Runbook: <situation>
Last verified: YYYY-MM-DD against <version>

## Symptoms
The alert name and the user-visible effect, in the words the pager uses.

## Procedure
1. Command. Expected: <output>. If different: <next action>.

## Verification
The metric or command and the threshold that means recovered, with a time limit.

## Rollback
How to undo the procedure, or "None: the procedure is not reversible".

## Escalation
Who to page, by rota name, after how many minutes without recovery.
```

Write for a tired reader: commands copy-pastable, no placeholder left unexplained, every irreversible step marked. Facts the incident notes do not settle are written as `Unknown: owner to fill`, never guessed.

## Last-verified line

Format: `Last verified: YYYY-MM-DD against <version or commit>`, on the line under the title. The audit finds it anywhere in the prose, takes the first one, and needs an ISO date.
