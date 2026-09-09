# ADR 0002: Identify canonical tracklogs by normalized trajectory

- Status: Accepted
- Date: 2026-09-09

## Context

One physical flight can be uploaded to several services. The same IGC trajectory can also acquire different headers or wrapper metadata. Source record IDs and raw-file hashes therefore cannot be the canonical flight identity.

## Decision

Maintain two hashes:

1. `raw_sha256`: exact source bytes, used for immutable raw artifacts.
2. `trajectory_sha256`: ordered normalized physical fixes (UTC time, coordinates, separate pressure/GNSS altitudes, validity), excluding headers and source metadata.

`tracklog_id` is derived from `trajectory_sha256`. When another source produces the same trajectory identity, its `SourceReference` is merged into the existing canonical tracklog.

This is exact normalized deduplication. Fuzzy matching of resampled, clipped or slightly altered trajectories is a separate future reconciliation problem and must not silently redefine identity.

## Consequences

- Cross-source duplicates converge without losing provenance.
- Header edits do not create new canonical trajectories.
- Near-duplicate detection can evolve independently and conservatively.
