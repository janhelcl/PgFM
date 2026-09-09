# ADR 0005: Stabilize the logical model before choosing the large-scale physical format

- Status: Accepted
- Date: 2026-09-09

## Context

The eventual corpus can contain millions of flights and billions of fixes, for which one-JSON-file-per-flight is not an appropriate analytical representation. We do not yet know the final workload split between object storage, Parquet/Arrow, a catalogue database and training-time streaming.

Choosing the lake/table technology now would couple acquisition semantics to an infrastructure guess.

## Decision

Define stable logical contracts (`Tracklog`, `TrackPoint`, `SourceReference`, raw artifact and canonical-store protocols) before committing to the production physical representation.

Provide filesystem-backed raw and canonical stores only as deterministic reference implementations for local development and tests. The production canonical store will be selected in a later ADR from measured workload requirements, without changing connector or canonical-domain contracts.

## Consequences

- Acquisition can begin immediately.
- Production storage can become columnar/partitioned without rewriting source connectors.
- The local canonical JSON store must not be mistaken for the target at corpus scale.
