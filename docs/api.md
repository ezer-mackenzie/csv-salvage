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
The source is read through a read-only memory map, avoiding a separate full-file
input buffer. Parsed rows are still materialized in memory, and the input file
must not be modified while the operation is running. Input and output may refer
to the same path.

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
The source is read through a memory map, but rows are currently materialized
before iteration; this API does not guarantee constant memory usage.

### `read_pyarrow()` and `read_polars()`

```python
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
) -> pyarrow.Table: ...

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
) -> polars.DataFrame: ...
```

These adapters use the same parsing and normalization options as `open()`.
Columns are strings. If `column_names` is omitted, they are named
`column_1`, `column_2`, and so on. Install the adapters independently with
`csv-salvage[arrow]` or `csv-salvage[polars]`. Both currently materialize rows
in Python before building the result; zero-copy parsing is not supported. Input
header rows remain data rows, as they do with `SalvageReader`; `column_names`
only labels the output schema and does not change the inferred column count.
Rows routed to quarantine by the normalization options are omitted.

---

## Classes

### `SalvageSummary`

Contains metadata and statistics about the salvage operation:

- **`total_rows`** (`int`): Total count of rows processed.
- **`salvaged_rows`** (`int`): Count of successfully salvaged rows.
- **`repaired_rows`** (`int`): Count of rows modified by ragged-row padding or overflow merging.
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
