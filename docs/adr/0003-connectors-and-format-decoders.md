# ADR 0003: Separate source connectors from file-format decoders

- Status: Accepted
- Date: 2026-09-09

## Context

Several sources expose the same underlying format (especially IGC). If each scraper parses its own tracklogs, source quirks leak into the data model and parsing fixes must be repeated.

## Decision

A source connector owns only source interaction: discovery, pagination, authentication/rate limits and retrieval of source bytes. A format decoder owns the byte-level semantics. The ingestion pipeline composes the two.

The initial connector protocol is `discover` + `fetch`; the initial shared decoder is IGC.

## Consequences

- New IGC sources are small adapters.
- IGC correctness is tested once.
- Source HTML/API changes do not alter canonical tracklog semantics.
- Future GPX/KML/device formats can add decoders without changing source or storage contracts.
