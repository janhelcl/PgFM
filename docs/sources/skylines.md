# SkyLines

SkyLines is the first external tracklog source implemented in PgFM. It is useful both as a source of soaring trajectories and as a low-friction proof-of-concept corpus because SkyLines publishes its flight database under the Open Data Commons Attribution License (ODC-By).

## Public source contract

The connector relies on behavior visible in the SkyLines open-source application:

- `GET /api/flights/all?page=N` returns a JSON object containing `flights` and a total `count`;
- the production list size is currently 50 flights per page;
- each listable flight can expose `igcFile.filename`;
- the UI downloads that file from `/files/<igcFile.filename>`;
- aircraft model type is explicitly classified as `glider`, `motorglider`, `paraglider`, `hangglider`, `ul` or `unspecified`.

The connector treats these as an external source contract and fails loudly if the response shape changes.

## Rights

SkyLines' public homepage states that its flight database is made available under ODC-By. PgFM records this as `RightsStatus.PUBLIC_TERMS` with the ODC-By 1.0 licence URL. This is provenance, not a legal opinion about rights outside the database licence.

Attribution must be carried forward when publishing or distributing derived databases that trigger ODC-By attribution requirements. The source record must therefore never be discarded from canonical provenance.

## Privacy

The SkyLines API exposes pilot and owner information, but PgFM does not need it for the initial trajectory model. `SkyLinesFlight` deliberately extracts only:

- flight ID;
- IGC filename;
- date;
- aircraft type/model;
- takeoff country.

Pilot names, account IDs, registration and competition IDs are not copied into the canonical acquisition candidate.

## Politeness and resumability

The connector defaults to one request per second and identifies itself with a PgFM user agent. Discovery accepts a page cursor so long catalogue runs can resume without starting from page one. There is no default parallel downloader.

The current page-size assumption is 50, matching the public SkyLines deployment. It is configurable so a deployment change does not require changing the canonical acquisition model.

## Census

Run a metadata-only census without downloading IGC files:

```bash
pgfm-skylines-census
```

For a smoke run:

```bash
pgfm-skylines-census --max-pages 2 --delay-seconds 1
```

The census reports currently listable flights, flights with downloadable IGCs, and distributions by aircraft type, year and takeoff country. Exact raw-byte/fix statistics should be computed from the immutable raw store after acquisition rather than downloading the same IGC files twice.
