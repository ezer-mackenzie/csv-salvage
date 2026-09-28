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
