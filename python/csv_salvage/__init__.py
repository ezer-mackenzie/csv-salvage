"""High-performance, fault-tolerant CSV salvage and reconstruction engine.

Rescues corrupted, broken, and malformed CSV files where strict parsers
(Polars, DuckDB, Pandas) abort with ParserError.
"""
from __future__ import annotations

from .errors import (
    ConfigurationError,
    CorruptedFileError,
    InferenceError,
    SalvageError,
)
from .reader import SalvageReader
from .salvage import (
    SalvageSummary,
    open,
    salvage_file,
    sniff,
)

__version__ = "0.1.0"

__all__ = [
    "ConfigurationError",
    "CorruptedFileError",
    "InferenceError",
    "SalvageError",
    "SalvageReader",
    "SalvageSummary",
    "__version__",
    "open",
    "salvage_file",
    "sniff",
]
