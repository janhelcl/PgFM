# PgFM

Paragliding Foundation Model research monorepo.

The goal is to learn transferable representations of paraglider flight from full trajectories and the physical context around them: weather, terrain, airspace, launch geometry and other useful observations.

## Current focus: data acquisition

The first subsystem is `pgfm.data.acquisition`, with tracklogs as the first-class data source.

```text
remote source
    |
    v
connector: discover + fetch
    |
    v
immutable raw artifact + acquisition manifest
    |
    v
format decoder (IGC first)
    |
    v
canonical Tracklog / TrackPoint model
    |
    v
canonical store
```

The important boundary is that source-specific code does not define the data model. XContest, XCGlobe, Leonardo, competition archives and future pilot/device imports should all converge on the same canonical trajectory representation.

See [data acquisition](docs/data-acquisition.md) and the [architecture decision records](docs/adr/README.md).

## Development

Python 3.12+ is required.

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```
