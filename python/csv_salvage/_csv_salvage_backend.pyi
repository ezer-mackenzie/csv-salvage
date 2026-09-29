import sys
from collections.abc import Iterator
from types import TracebackType
from typing import Any

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

class SalvageSummary:
    total_rows: int
    salvaged_rows: int
    repaired_rows: int
    quarantined_rows: int
    detected_delimiter: str
    inferred_columns: int

    def to_dict(self) -> dict[str, Any]: ...

class SalvageReader:
    summary: SalvageSummary

    def __init__(
        self,
        file_path: str,
        delimiter: str | None = None,
        quote_char: str = '"',
        fill_ragged_rows: bool = True,
        merge_overflow: bool = True,
        expected_columns: int | None = None,
        repair_quotes: bool = True,
    ) -> None: ...
    def __iter__(self) -> Iterator[list[str]]: ...
    def __next__(self) -> list[str]: ...
    def __len__(self) -> int: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> bool: ...

def salvage_file(
    input_path: str,
    output_path: str,
    quarantine_path: str | None = None,
    delimiter: str | None = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: int | None = None,
    repair_quotes: bool = True,
) -> SalvageSummary: ...

def sniff(sample: str) -> str: ...

def open(
    file_path: str,
    delimiter: str | None = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: int | None = None,
    repair_quotes: bool = True,
) -> SalvageReader: ...
