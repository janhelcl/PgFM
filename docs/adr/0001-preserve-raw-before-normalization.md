# ADR 0001: Preserve raw artifacts before normalization

- Status: Accepted
- Date: 2026-09-09

## Context

PgFM will acquire tracklogs and other observations from multiple external systems. Parsers will evolve, source metadata can disappear, and remote artifacts may not remain downloadable forever. Storing only parsed records would make parser fixes and provenance audits depend on re-fetching the source.

## Decision

Every successfully fetched artifact is written to an immutable raw store before decoding or normalization. The raw object is content-addressed by SHA-256. A separate acquisition manifest records source identity, retrieval metadata, acquisition method and rights statement.

Decoder failure does not roll back the raw write.

## Consequences

- We can reprocess locally when parsers/schema change.
- Exact duplicate bytes deduplicate naturally.
- Failed parses remain inspectable.
- Raw storage can contain personal/source-specific fields that are intentionally absent from canonical training data, so access to raw data must eventually be more restrictive than access to derived datasets.
