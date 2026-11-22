# Design token naming lint

## One line

Checks one design-token JSON file for naming breaks, repeated raw values, raw hex inside semantic tokens, and references that dangle or loop.

## What it does

The skill runs a read-only Python script on one token file. The file can be nested objects or flat objects with dotted keys. The script builds a dotted name for each token and checks six things: whether each name is lowercase kebab-case joined by dots, whether a name is defined twice, whether two reference-free tokens share the same raw value, whether a `semantic.` or `alias.` token holds a raw hex color, whether a `{reference}` points to a token that exists, and whether a chain of references loops back on itself. The output is a JSON report, and the skill turns that report into a fix list ordered so that broken references come first. The script never edits the token file and never writes output to disk.

## When to use

Use it when a token file has been edited by hand over several releases and needs a structural check before a handoff. It is also useful when a reviewer asks whether tokens follow one naming rule, or when a semantic layer is supposed to reference base tokens and may have picked up literal colors. The report gives a count per finding code, so a team can see whether problems cluster in one namespace.

## When not to use

Do not use it to judge whether a color has enough contrast, whether a palette fits a brand, or whether a value is the right design choice. It does not read CSS, Figma exports, Tailwind configs or component code. It does not generate tokens, rename tokens for you, or merge duplicates. Its thresholds are working values for this skill, not a published standard.

## Requirements

Python 3.9 or newer, standard library only. No network access and no additional packages. The input must be one UTF-8 JSON file of at most 2 MB with at most 8 levels of object nesting.

## Example

Smoke run on the 12-token fixture (`python -I scripts/token_lint.py fixtures/tokens_smoke.json`, exit code 1):

```
{
  "tool": "token_lint",
  "file": "tokens_smoke.json",
  "token_count": 12,
  "finding_count": 7,
  "summary": {
    "CIRCULAR_REFERENCE": 1,
    "DANGLING_REFERENCE": 1,
    "DUPLICATE_VALUE": 2,
    "NAME_PATTERN": 1,
    "RAW_HEX_IN_SEMANTIC": 2
  },
  "findings": [
    {
      "code": "CIRCULAR_REFERENCE",
      "token": "radius.medium",
      "detail": "cycle: radius.medium -> radius.small -> radius.medium"
    },
    {
      "code": "DANGLING_REFERENCE",
      "token": "semantic.text.muted",
      "detail": "references missing token color.gray.700"
    },
    {
      "code": "DUPLICATE_VALUE",
      "token": "color.brand.500",
      "detail": "raw value #1a73e8 is used by color.brand.500, color.brand.600"
    },
    {
      "code": "DUPLICATE_VALUE",
      "token": "color.gray.100",
      "detail": "raw value #f5f5f5 is used by color.gray.100, semantic.surface.page"
    },
    {
      "code": "NAME_PATTERN",
      "token": "color.brand.Dark",
      "detail": "name must be lowercase kebab-case segments joined by dots"
    },
    {
      "code": "RAW_HEX_IN_SEMANTIC",
      "token": "semantic.surface.page",
      "detail": "semantic or alias token holds a raw hex value #f5f5f5"
    },
    {
      "code": "RAW_HEX_IN_SEMANTIC",
      "token": "semantic.text.primary",
      "detail": "semantic or alias token holds a raw hex value #111111"
    }
  ]
}
```

## Limits

The script reads one file per run and has no option to read a folder. Duplicate-value detection compares raw strings after trimming and lowercasing, so `#1a73e8` and `rgb(26,115,232)` are not treated as equal. Hex detection accepts only 3, 6 and 8 digit forms. The 2 MB size cap and 8-level nesting cap are working values. A token value that is a boolean, null or array stops the run with exit code 2.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
