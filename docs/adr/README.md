# Architecture decision records

ADRs document decisions that constrain future PgFM work. They are append-only: when a decision changes, add a new ADR that supersedes the old one rather than rewriting history.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-preserve-raw-before-normalization.md) | Preserve raw artifacts before normalization | Accepted |
| [0002](0002-canonical-tracklog-identity.md) | Identify canonical tracklogs by normalized trajectory | Accepted |
| [0003](0003-connectors-and-format-decoders.md) | Separate source connectors from file-format decoders | Accepted |
| [0004](0004-rights-and-personal-data.md) | Store rights provenance and minimize personal data | Accepted |
| [0005](0005-logical-model-before-physical-lake-format.md) | Stabilize the logical storage model before choosing the large-scale physical format | Accepted |
| [0006](0006-rate-limited-resumable-connectors.md) | Make external acquisition resumable and polite by default | Accepted |
