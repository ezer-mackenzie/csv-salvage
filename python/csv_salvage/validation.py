"""Input validation for csv-salvage public API."""
from __future__ import annotations

from pathlib import Path

from .errors import ConfigurationError, CorruptedFileError


def validate_input_path(path: str | Path) -> Path:
    """Validate that the input CSV file exists and is a file."""
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    if not p.is_file():
        raise CorruptedFileError(f"Input path is not a regular file: {p}")
    return p


def validate_output_path(path: str | Path) -> Path:
    """Validate output destination path and ensure parent directory exists."""
    p = Path(path).resolve()
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    return p


def validate_quarantine_path(path: str | Path | None) -> Path | None:
    """Validate optional quarantine file destination path."""
    if path is None:
        return None
    
    p = Path(path).resolve()
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        
    return p


def validate_delimiter(delimiter: str | None) -> str | None:
    """Validate single-character delimiter if explicitly provided."""
    if delimiter is None:
        return None

    if len(delimiter) != 1:
        raise ConfigurationError(f"Delimiter must be a single character, got {delimiter!r} (length {len(delimiter)})")

    return delimiter


def validate_quote_char(quote_char: str) -> str:
    """Validate single-character quote enclosure."""
    if len(quote_char) != 1:
        raise ConfigurationError(f"quote_char must be a single character, got {quote_char!r} (length {len(quote_char)})")

    return quote_char


def validate_expected_columns(expected_columns: int | None) -> int | None:
    """Validate that expected_columns is a positive integer if provided."""
    if expected_columns is None:
        return None

    if expected_columns <= 0:
        raise ConfigurationError(f"expected_columns must be positive, got {expected_columns}")

    return expected_columns
