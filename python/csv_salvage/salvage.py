"""Core public salvage operations for csv-salvage."""
from __future__ import annotations

from pathlib import Path

from . import _csv_salvage_backend
from .errors import CorruptedFileError, InferenceError
from .reader import SalvageReader
from .validation import (
    validate_delimiter,
    validate_expected_columns,
    validate_input_path,
    validate_output_path,
    validate_quarantine_path,
    validate_quote_char,
)

SalvageSummary = _csv_salvage_backend.SalvageSummary


def salvage_file(
    input_path: str | Path,
    output_path: str | Path,
    quarantine_path: str | Path | None = None,
    delimiter: str | None = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: int | None = None,
    repair_quotes: bool = True,
) -> _csv_salvage_backend.SalvageSummary:
    """Salvage a corrupted CSV file and write a clean, standard RFC-4180 file.

    Args:
        input_path: Path to the corrupted CSV input file.
        output_path: Destination path where the clean CSV will be written.
        quarantine_path: Optional destination path for unrecoverable records.
        delimiter: Optional single-character delimiter. If None, auto-sniffed.
        quote_char: Quote character enclosure (default: '"').
        fill_ragged_rows: If True, pads short rows with empty strings. Default True.
        merge_overflow: If True, merges extra tokens into the last field. Default True.
        expected_columns: Optional explicit column count. If None, inferred automatically.
        repair_quotes: If True, repairs stray internal quotes. Default True.

    Returns:
        SalvageSummary with statistics on recovered, repaired, and quarantined rows.
    """
    in_path = validate_input_path(input_path)
    out_path = validate_output_path(output_path)
    quar_path = validate_quarantine_path(quarantine_path)
    delim = validate_delimiter(delimiter)
    quote = validate_quote_char(quote_char)
    expected = validate_expected_columns(expected_columns)

    try:
        return _csv_salvage_backend.salvage_file(
            str(in_path),
            str(out_path),
            quarantine_path=str(quar_path) if quar_path else None,
            delimiter=delim,
            quote_char=quote,
            fill_ragged_rows=fill_ragged_rows,
            merge_overflow=merge_overflow,
            expected_columns=expected,
            repair_quotes=repair_quotes,
        )
    except Exception as exc:
        raise CorruptedFileError(f"Salvage operation failed on {in_path}: {exc}") from exc


def sniff(sample: str) -> str:
    """Detect the most likely delimiter from a CSV text sample.

    Args:
        sample: Non-empty string containing representative CSV lines.

    Returns:
        Detected single-character delimiter (e.g. ',', ';', '\\t', '|').
    """
    if not sample.strip():
        raise InferenceError("Cannot sniff delimiter from an empty sample.")

    try:
        return _csv_salvage_backend.sniff(sample)
    except Exception as exc:
        raise InferenceError(f"Failed to infer delimiter: {exc}") from exc


def open(
    file_path: str | Path,
    delimiter: str | None = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: int | None = None,
    repair_quotes: bool = True,
) -> SalvageReader:
    """Open and stream records from a corrupted CSV file.

    Args:
        file_path: Path to the corrupted CSV file.
        delimiter: Optional single-character delimiter.
        quote_char: Quote character enclosure.
        fill_ragged_rows: If True, pads short rows with empty strings.
        merge_overflow: If True, merges extra tokens into the last column.
        expected_columns: Optional explicit column count.
        repair_quotes: If True, repairs stray quotes.

    Returns:
        SalvageReader instance acting as context manager and iterator.
    """
    return SalvageReader(
        file_path=file_path,
        delimiter=delimiter,
        quote_char=quote_char,
        fill_ragged_rows=fill_ragged_rows,
        merge_overflow=merge_overflow,
        expected_columns=expected_columns,
        repair_quotes=repair_quotes,
    )
