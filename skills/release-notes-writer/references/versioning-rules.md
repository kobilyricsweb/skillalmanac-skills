# Versioning rules the script applies

Written in our own words from public specifications. Read when the user asks why the script chose a bump, or when a 0.x or pre-release version is involved.

## Sources

- Conventional Commits 1.0.0: https://www.conventionalcommits.org/en/v1.0.0/ . A `feat` commit corresponds to a minor release, a `fix` to a patch release, and a `!` after the type or scope, or a footer starting `BREAKING CHANGE:`, to a major release. Other types are allowed but carry no version meaning by themselves. The footer token must be uppercase.
- Semantic Versioning 2.0.0: https://semver.org/spec/v2.0.0.html . Version numbers are major.minor.patch. Incompatible public-interface changes need a major number; backward-compatible additions need a minor; backward-compatible fixes need a patch. Marking public functionality deprecated requires at least a minor release. Major version zero is for initial development, where anything may change at any time and the public interface should not be considered stable.
- Keep a Changelog 1.1.0: https://keepachangelog.com/en/1.1.0/ . A changelog is for humans, newest release first, with an Unreleased section on top, ISO dates (YYYY-MM-DD), and the change types Added, Changed, Deprecated, Removed, Fixed and Security.

## How the script maps them

| Evidence in the input | Bump |
|---|---|
| Any breaking marker | major |
| `feat`, CHANGELOG Added, Changed, Deprecated | minor |
| `fix`, `perf`, Security, a revert of released work | patch |
| Only docs and internal types | none; `proposed_version` is null |

Highest wins. The script never reads code, so an unmarked incompatible change cannot raise the bump by itself; `possible_unmarked_breaking` exists to prompt the human.

## Version 0.x

Semver gives no guarantee below 1.0.0. Many projects use the minor number as the breaking-change signal in this range. The script follows that habit: a breaking change in 0.x proposes a minor bump, and `bump_standard` shows what the plain rule would give. Whether to release 1.0.0 is a product decision; the script never proposes it unprompted.

## Pre-release current versions

For a current version such as 1.2.0-rc.1 the script computes from the numbers 1.2.0 and raises `prerelease_current`. The user decides between another candidate (1.2.0-rc.2) and the final release. A leading `v` on the current version is kept on the proposed version.

## Dates

The skeleton prints `<release date>`. The date is the user's to supply; use the ISO form.
