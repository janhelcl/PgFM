"""Tracklog source connectors.

Only working source adapters belong here. Source-independent IGC semantics live in `igc.py`.
"""

from pgfm.data.acquisition.tracklogs.connectors.local import LocalIgcConnector

__all__ = ["LocalIgcConnector"]
