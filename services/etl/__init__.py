from __future__ import annotations

# Re-export public API used by the app
from . import fba_fee_ingestor as load_csv  # type: ignore[assignment]

__all__ = ["load_csv"]
