"""Tracklog source connectors.

Only working source adapters belong here. Source-independent IGC semantics live in `igc.py`.
"""

from pgfm.data.acquisition.tracklogs.connectors.local import LocalIgcConnector
from pgfm.data.acquisition.tracklogs.connectors.skylines import (
    SkyLinesConnector,
    SkyLinesFlight,
    skylines_rights,
)

__all__ = [
    "LocalIgcConnector",
    "SkyLinesConnector",
    "SkyLinesFlight",
    "skylines_rights",
]
