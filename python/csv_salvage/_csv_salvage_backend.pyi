from typing import Any, Dict, Iterator, List, Optional

class SalvageSummary:
    total_rows: int
    salvaged_rows: int
    repaired_rows: int
    quarantined_rows: int
    detected_delimiter: str
    inferred_columns: int

    def to_dict(self) -> Dict[str, Any]: ...

class SalvageReader:
    summary: SalvageSummary

    def __init__(
        self,
        file_path: str,
        delimiter: Optional[str] = None,
        quote_char: str = '"',
        fill_ragged_rows: bool = True,
        merge_overflow: bool = True,
        expected_columns: Optional[int] = None,
        repair_quotes: bool = True,
    ) -> None: ...
    def __iter__(self) -> Iterator[List[str]]: ...
    def __next__(self) -> List[str]: ...
    def __len__(self) -> int: ...
    def __enter__(self) -> SalvageReader: ...
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> bool: ...

def salvage_file(
    input_path: str,
    output_path: str,
    quarantine_path: Optional[str] = None,
    delimiter: Optional[str] = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: Optional[int] = None,
    repair_quotes: bool = True,
) -> SalvageSummary: ...

def sniff(sample: str) -> str: ...

def open(
    file_path: str,
    delimiter: Optional[str] = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: Optional[int] = None,
    repair_quotes: bool = True,
) -> SalvageReader: ...
