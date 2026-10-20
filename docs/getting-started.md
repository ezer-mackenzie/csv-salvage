# Getting started

## Installation

Install `csv-salvage` using your preferred Python package manager:

```bash
pip install csv-salvage
```

Or using `uv`:

```bash
uv add csv-salvage
```

## Basic Usage

### Command-line interface

Install the package, then repair a file from the terminal:

```bash
csv-salvage fix data/broken.csv --output data/clean.csv
```

Optionally specify a quarantine file and a fixed column count:

```bash
csv-salvage fix data/broken.csv \
  --output data/clean.csv \
  --quarantine data/quarantine.csv \
  --expected-columns 5
```

Run `csv-salvage fix --help` to see all options. The same command is available
as `python -m csv_salvage`.

### Optional PyArrow and Polars integrations

Install an adapter separately from the core package:

```bash
pip install "csv-salvage[arrow]"
# or
pip install "csv-salvage[polars]"
```

Then request a typed string table or DataFrame:

```python
import csv_salvage as cs

table = cs.read_pyarrow("data/broken.csv", column_names=["id", "name"])
frame = cs.read_polars("data/broken.csv", column_names=["id", "name"])
```

Column names are optional; when omitted, columns are named `column_1`,
`column_2`, and so on. Both adapters materialize salvaged values and do not
provide zero-copy parsing. Input headers remain rows in the result, just as
they do when iterating with `cs.open()`. Rows routed to quarantine are omitted.

### 1. Salvaging a Corrupted File

The primary workflow uses `salvage_file()` to clean a file on disk and produce standard RFC-4180 output ready for Polars, DuckDB, or Pandas:

```python
import csv_salvage as cs

summary = cs.salvage_file(
    input_path="data/raw_corrupted.csv",
    output_path="data/clean_salvaged.csv",
)

print(summary)
# <SalvageSummary total_rows=1500 salvaged_rows=1500 repaired_rows=42 quarantined_rows=0 delimiter=',' inferred_columns=12>
```

File input is memory-mapped to avoid a second full-size copy of the raw bytes.
Parsed rows are still materialized in memory, so this does not guarantee
constant-memory operation. Do not modify the input file during salvage.

### 2. Streaming Rows Directly

You can open and iterate through salvaged rows in Python without writing an intermediate file:

```python
import csv_salvage as cs

with cs.open("data/broken_export.csv") as reader:
    print(f"Detected delimiter: {reader.summary.detected_delimiter}")
    for row in reader:
        print(row)
```

### 3. Delimiter Detection

Detect delimiters from a string snippet:

```python
import csv_salvage as cs

snippet = "user_id|email|status\n101|alice@example.com|active\n"
delimiter = cs.sniff(snippet)
assert delimiter == "|"
```

### 4. Custom Normalization Options

Fine-tune how ragged rows and internal quotes are repaired:

```python
import csv_salvage as cs

summary = cs.salvage_file(
    input_path="legacy.csv",
    output_path="normalized.csv",
    quarantine_path="quarantine.log",
    delimiter=";",
    quote_char='"',
    fill_ragged_rows=True,      # Pad short rows with empty strings
    merge_overflow=True,        # Merge extra trailing columns into last field
    expected_columns=5,         # Force exact column count
    repair_quotes=True,         # Fix stray unescaped quotes
)
```
