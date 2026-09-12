# ADR 0006: Make external acquisition resumable and polite by default

- Status: Accepted
- Date: 2026-09-12

## Context

PgFM can eventually acquire tens or hundreds of thousands of tracklogs from one source. A connector that assumes a short interactive request can accidentally hammer a public service, and an interrupted long run can waste hours of already completed discovery.

## Decision

Network-backed connectors must support deterministic resumability at the natural source cursor (page, token, timestamp or equivalent) and conservative request pacing by default. They must use an identifiable user agent where the protocol permits it and must not enable parallel bulk download implicitly.

Source locators are validated before fetch so a stored or malformed candidate cannot silently turn a connector into an arbitrary URL fetcher.

Source-specific limits remain configurable because sanctioned bulk endpoints or explicit partnerships may permit a higher rate.

## Consequences

- First runs favor source safety over maximum throughput.
- Long acquisitions can be checkpointed by orchestration without changing the canonical data model.
- A future concurrent downloader must be an explicit policy layer with its own source-specific limits rather than behavior hidden inside a connector.
