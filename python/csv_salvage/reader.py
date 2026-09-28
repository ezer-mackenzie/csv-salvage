"""Streaming reader for salvaged CSV records."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Optional

from . import _csv_salvage_backend
from .errors import CorruptedFileError, SalvageError
from .validation import (
    validate_delimiter,
    validate_expected_columns,
    validate_input_path,
    validate_quote_char,
)


class SalvageReader:
    """Streaming iterator and context manager for salvaged CSV records."""

    def __init__(
        self,
        file_path: str | Path,
        delimiter: Optional[str] = None,
        quote_char: str = '"',
        fill_ragged_rows: bool = True,
        merge_overflow: bool = True,
        expected_columns: Optional[int] = None,
        repair_quotes: bool = True,
    ) -> None:
        path = validate_input_path(file_path)
        delim = validate_delimiter(delimiter)
        quote = validate_quote_char(quote_char)
        expected = validate_expected_columns(expected_columns)

        try:
            self._backend_reader = _csv_salvage_backend.open(
                str(path),
                delimiter=delim,
                quote_char=quote,
                fill_ragged_rows=fill_ragged_rows,
                merge_overflow=merge_overflow,
                expected_columns=expected,
                repair_quotes=repair_quotes,
            )
        except Exception as exc:
            raise CorruptedFileError(f"Failed to open CSV file for salvage: {exc}") from exc

    @property
    def summary(self) -> _csv_salvage_backend.SalvageSummary:
        """Return the salvage summary statistics."""
        return self._backend_reader.summary

    def __iter__(self) -> Iterator[List[str]]:
        return iter(self._backend_reader)

    def __next__(self) -> List[str]:
        return next(self._backend_reader)

    def __len__(self) -> int:
        return len(self._backend_reader)

    def __enter__(self) -> SalvageReader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def __repr__(self) -> str:
        return f"<SalvageReader rows={len(self)} summary={self.summary!r}>"
