"""Optional dataframe integrations for csv-salvage."""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from pathlib import Path
from typing import Any

from .errors import ConfigurationError
from .reader import SalvageReader


def _read_rows(
    file_path: str | Path,
    delimiter: str | None,
    quote_char: str,
    fill_ragged_rows: bool,
    merge_overflow: bool,
    expected_columns: int | None,
    repair_quotes: bool,
    column_names: Sequence[str] | None,
) -> tuple[list[list[str]], list[str]]:
    has_column_names = column_names is not None
    if column_names is not None:
        if isinstance(column_names, (str, bytes)):
            raise ConfigurationError("column_names must be a sequence of strings")
        names = tuple(column_names)
        if any(not isinstance(name, str) or not name for name in names):
            raise ConfigurationError("column_names must contain non-empty strings")
        if len(set(names)) != len(names):
            raise ConfigurationError("column_names must be unique")
        if expected_columns is not None and len(names) != expected_columns:
            raise ConfigurationError("column_names length must match expected_columns")
    else:
        names = ()

    reader = SalvageReader(
        file_path=file_path,
        delimiter=delimiter,
        quote_char=quote_char,
        fill_ragged_rows=fill_ragged_rows,
        merge_overflow=merge_overflow,
        expected_columns=expected_columns,
        repair_quotes=repair_quotes,
    )
    rows = list(reader)
    summary = reader.summary
    column_count = summary.inferred_columns
    if summary.total_rows == 0:
        column_count = expected_columns if expected_columns is not None else len(names)
    if has_column_names and len(names) != column_count:
        raise ConfigurationError(
            f"column_names length must match the inferred column count ({column_count})"
        )
    if not has_column_names:
        names = tuple(f"column_{index + 1}" for index in range(column_count))
    return rows, list(names)


def read_pyarrow(
    file_path: str | Path,
    *,
    column_names: Sequence[str] | None = None,
    delimiter: str | None = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: int | None = None,
    repair_quotes: bool = True,
) -> Any:
    """Read salvaged rows into a PyArrow string Table.

    Input header rows are kept as data, matching :class:`SalvageReader`.
    ``column_names`` sets result schema names only. Rows quarantined by the
    normalization options are omitted from the result.
    This eagerly materializes the salvaged rows and creates Arrow arrays from
    Python strings; it does not provide zero-copy parsing.
    """
    try:
        pyarrow = import_module("pyarrow")
    except ImportError as exc:
        raise ImportError(
            "read_pyarrow() requires the optional 'arrow' extra; "
            "install csv-salvage[arrow]"
        ) from exc

    rows, names = _read_rows(
        file_path,
        delimiter,
        quote_char,
        fill_ragged_rows,
        merge_overflow,
        expected_columns,
        repair_quotes,
        column_names,
    )
    arrays = [
        pyarrow.array([row[index] for row in rows], type=pyarrow.string())
        for index in range(len(names))
    ]
    return pyarrow.Table.from_arrays(arrays, names=names)


def read_polars(
    file_path: str | Path,
    *,
    column_names: Sequence[str] | None = None,
    delimiter: str | None = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: int | None = None,
    repair_quotes: bool = True,
) -> Any:
    """Read salvaged rows into a Polars string DataFrame.

    Input header rows are kept as data, matching :class:`SalvageReader`.
    ``column_names`` sets result schema names only. Rows quarantined by the
    normalization options are omitted from the result.
    This eagerly materializes salvaged rows as Python strings before creating
    the DataFrame; it does not provide zero-copy parsing.
    """
    try:
        polars = import_module("polars")
    except ImportError as exc:
        raise ImportError(
            "read_polars() requires the optional 'polars' extra; "
            "install csv-salvage[polars]"
        ) from exc

    rows, names = _read_rows(
        file_path,
        delimiter,
        quote_char,
        fill_ragged_rows,
        merge_overflow,
        expected_columns,
        repair_quotes,
        column_names,
    )
    columns = [
        polars.Series(
            name,
            [row[index] for row in rows],
            dtype=polars.String,
        )
        for index, name in enumerate(names)
    ]
    return polars.DataFrame(columns)
