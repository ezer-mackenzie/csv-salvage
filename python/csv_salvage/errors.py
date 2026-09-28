"""Exceptions for csv-salvage."""
from __future__ import annotations


class SalvageError(Exception):
    """Base exception for all csv-salvage errors."""


class CorruptedFileError(SalvageError):
    """Raised when a CSV input file cannot be parsed or salvaged."""


class InferenceError(SalvageError, ValueError):
    """Raised when delimiter or column count inference fails."""


class ConfigurationError(SalvageError, ValueError):
    """Raised when an invalid parser or salvage option is provided."""
