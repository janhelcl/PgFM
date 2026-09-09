# Data acquisition

PgFM treats acquisition as a permanent subsystem, not a collection of one-off download scripts.

## Principles

1. **Preserve raw bytes first.** A successfully fetched artifact is stored before decoding. Parser bugs can therefore be fixed without re-downloading data, and malformed files remain auditable.
2. **One canonical model, many sources.** Source IDs, URLs and website-specific metadata are provenance; they do not define trajectory semantics.
3. **Separate source protocols from file formats.** XContest and XCGlobe may both expose IGC. Their connectors differ; their IGC decoder must not.
4. **Identity follows the trajectory.** Raw SHA-256 identifies exact files. A second SHA-256 over normalized physical fixes identifies the canonical trajectory across header/source differences.
5. **Rights are data.** Every acquisition stores a point-in-time rights statement. `unknown` means unknown; it is never silently upgraded to permission.
6. **Avoid unnecessary personal data.** Canonical tracklogs do not contain pilot names, email addresses or arbitrary IGC headers. A connector may provide a source-scoped pseudonymous `subject_key` when useful for modelling repeated-pilot behaviour.

## Acquisition flow

```text
Connector.discover()
      |
      v
AcquisitionCandidate
      |
Connector.fetch()
      |
      v
FetchedArtifact --------------------+
      |                              |
      v                              v
RawArtifactStore                raw bytes + manifest
      |
      v
shared format decoder (IGC)
      |
      v
TrackPoint[]
      |
      v
trajectory fingerprint + SourceReference
      |
      v
CanonicalTracklogStore
```

The raw-store write intentionally precedes parsing. A decoder failure should not cause loss of the source artifact.

## Canonical tracklog

A `Tracklog` contains:

- a schema version;
- stable `tracklog_id` derived from normalized trajectory SHA-256;
- ordered `TrackPoint` values;
- zero-loss distinction between GNSS and pressure altitude;
- one or more `SourceReference` records;
- source-independent metadata.

A `TrackPoint` currently contains UTC timestamp, WGS84 latitude/longitude, pressure altitude, GNSS altitude, fix validity and a typed extension map for later IGC extensions.

A `SourceReference` contains source, external record ID/locator, raw SHA-256, acquisition method, retrieval time, rights statement and optional source-scoped subject key.

## Raw layout

The local reference store uses content-addressed raw objects:

```text
<data-root>/
  raw/
    sha256/ab/abcdef....igc
    manifests/<source>/<external-id-hash>/abcdef....json
  canonical/
    tracklogs/ab/trk_sha256_abcdef....json
```

Raw content is globally content-addressed rather than namespaced by source, so an identical IGC downloaded from two sites occupies one blob while both acquisition manifests survive.

The JSON canonical store is a reference implementation for development and tests. The logical model and repository interface are deliberately independent from the eventual large-scale physical representation (likely columnar datasets plus an index/catalogue).

## Source portfolio

The target corpus should diversify *selection mechanisms*, not only websites.

| Family | Candidate sources | Why it matters | Current state |
| --- | --- | --- | --- |
| Claimed XC | XContest, XCGlobe, Leonardo, DHV-XC | Very large long-XC corpus | connectors pending |
| Competition | AirTribune / organizer archives | Same task/weather, successful and bomb-out pilots | partnership/import path pending |
| General/live | XCTrack, SportsTrackLive, Flymaster, OGN/PureTrack | Short/local/weak flights absent from OLC claims | access path pending |
| Pilot opt-in | device/Gaggle/other logbook exports | Least platform-dependent path, useful for consented data | local IGC connector exists |

A new source should only be added once its access method and rights status are recorded. We should prefer sanctioned APIs/bulk exports and partnerships over brittle scraping when they are available.

## Adding a connector

A connector implements only:

```python
class Connector(Protocol):
    source_id: str
    def discover(self, cursor: str | None = None) -> Iterable[AcquisitionCandidate]: ...
    def fetch(self, candidate: AcquisitionCandidate) -> FetchedArtifact: ...
```

Keep pagination, rate limits, authentication and source HTML/API quirks inside the connector. Keep IGC parsing, trajectory identity, raw storage and canonical storage outside it.

Do not add placeholder source classes that only raise `NotImplementedError`; add a source module when there is a working access path and tests/fixtures for it.
