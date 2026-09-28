# API reference

## Functions

### `salvage_file()`

```python
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
) -> SalvageSummary:
```

Salvages a corrupted CSV file and writes a clean, standard RFC-4180 file.

- **`input_path`**: Path to the corrupted CSV input file.
- **`output_path`**: Destination path for the repaired clean CSV.
- **`quarantine_path`**: Optional file path where unrecoverable rows are logged with diagnostics.
- **`delimiter`**: Delimiter character. If `None`, automatically sniffed from file contents.
- **`quote_char`**: Quote character (default `"`).
- **`fill_ragged_rows`**: When `True`, rows with fewer columns than expected are padded with empty strings.
- **`merge_overflow`**: When `True`, rows with extra tokens have their trailing columns merged into the last field.
- **`expected_columns`**: Explicit column count. If `None`, inferred from statistical mode.
- **`repair_quotes`**: When `True`, stray internal quotes are repaired.

### `sniff()`

```python
def sniff(sample: str) -> str:
```

Analyzes a sample text snippet and detects the most probable delimiter character (`,`, `;`, `\t`, or `|`).

### `open()`

```python
def open(
    file_path: str,
    delimiter: str | None = None,
    quote_char: str = '"',
    fill_ragged_rows: bool = True,
    merge_overflow: bool = True,
    expected_columns: int | None = None,
    repair_quotes: bool = True,
) -> SalvageReader:
```

Opens a corrupted CSV file for streaming row iteration in Python.

---

## Classes

### `SalvageSummary`

Contains metadata and statistics about the salvage operation:

- **`total_rows`** (`int`): Total count of rows processed.
- **`salvaged_rows`** (`int`): Count of successfully salvaged rows.
- **`repaired_rows`** (`int`): Count of rows requiring modifications (padding, merging, quote repair).
- **`quarantined_rows`** (`int`): Count of unrecoverable rows routed to quarantine.
- **`detected_delimiter`** (`str`): Delimiter inferred or configured.
- **`inferred_columns`** (`int`): Column count inferred or configured.
- **`to_dict()`** (`dict[str, Any]`): Returns the summary as a Python dictionary.

### `SalvageReader`

Streaming iterator and context manager over salvaged rows:

- Supports `__iter__`, `__next__`, `__len__`, `__enter__`, `__exit__`.
- **`summary`** (`SalvageSummary`): Summary statistics for the file.

---

## Exceptions

Defined in `csv_salvage.errors`:

- **`SalvageError`**: Base exception.
- **`CorruptedFileError`**: Raised on unrecoverable file errors.
- **`InferenceError`**: Raised when delimiter or column inference fails.
- **`ConfigurationError`**: Raised on invalid parameters.
