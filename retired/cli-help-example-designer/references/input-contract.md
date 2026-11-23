# Input Contract

Provide:

- `command`: command name and subcommand hierarchy.
- `options`: flags, values, defaults, required status, and domains.
- `positionals`: names and constraints.
- `relations`: mutually exclusive, dependent, or jointly required options.
- `shell`: optional shell name; omit for token-array output.
- `prerequisites`: supplied environment or input requirements.
- `expected_results`: optional documented outcomes.

Decision rules:

- Use only declared commands, options, values, and constraints.
- Quote only for a named shell; otherwise use token arrays.
- Mark incomplete constraints and expected results unknown.
- Make invalid examples violate one clearly stated supplied rule; if none is available, report the constraint gap instead of inventing invalidity.
- Do not execute commands or infer side effects.

Boundary: this designs examples from a grammar. It does not generate a full manual, implement a CLI, validate an installed binary, or run commands.
