# ADR 0004: Store rights provenance and minimize personal data

- Status: Accepted
- Date: 2026-09-09

## Context

Publicly downloadable does not necessarily mean permitted for bulk acquisition or model training. Tracklogs can also contain identifying pilot/device metadata and precise location history.

## Decision

Every acquisition carries a point-in-time `RightsStatement` with an explicit status, capture time, optional terms URL and note. Unknown rights remain `unknown`; source access and downstream-use decisions are not inferred from technical availability.

Raw artifacts are preserved for provenance, but the canonical tracklog intentionally excludes names, emails, arbitrary IGC headers and device identifiers. Where repeated-pilot information is useful, connectors may emit a source-scoped pseudonymous `subject_key` rather than the source-visible identity.

## Consequences

- Rights can be audited and filtering policies can later exclude restricted/unknown records.
- Canonical ML datasets expose less unnecessary personal information than source files.
- Identity resolution across sources is not attempted implicitly.
