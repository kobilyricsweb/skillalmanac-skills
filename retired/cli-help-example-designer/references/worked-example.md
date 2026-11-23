# Worked Example

Synthetic example; command names and values are invented for this example.

Input: command `catalog export`; required positional `source`; option `--format` with values `json|csv`; mutually exclusive options `--stdout` and `--output FILE`; `--pretty` requires `--format json`; shell omitted; prerequisite is an existing source identifier. Supplied synthetic example values: source=albums and output file=albums.csv.

Expected artifact:

Valid token arrays:

- `["catalog","export","albums","--format","json","--stdout","--pretty"]`
- `["catalog","export","albums","--format","csv","--output","albums.csv"]`

Because no shell is named, `shell` and `rendered_command` are null. A rejected token array combines `--stdout` and `--output` and identifies their supplied mutual exclusion. No output text is invented because none was supplied.
