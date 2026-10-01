"""Streaming reader for salvaged CSV records."""
from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType

if sys.version_info >= (3, 11):
    from typing import Self
else:
    try:
        from typing_extensions import Self
    except ImportError:  # pragma: no cover
        Self = object  # type: ignore[assignment,misc]

from . import _csv_salvage_backend
from .errors import CorruptedFileError
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
        delimiter: str | None = None,
        quote_char: str = '"',
        fill_ragged_rows: bool = True,
        merge_overflow: bool = True,
        expected_columns: int | None = None,
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

    def __iter__(self) -> Iterator[list[str]]:
        return iter(self._backend_reader)

    def __next__(self) -> list[str]:
        return next(self._backend_reader)

    def __len__(self) -> int:
        return len(self._backend_reader)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        return None

    def __repr__(self) -> str:
        return f"<SalvageReader rows={len(self)} summary={self.summary!r}>"
