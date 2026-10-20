# csv-salvage

Read the full documentation at [csv-salvage.readthedocs.io](https://csv-salvage.readthedocs.io/).

[![CI](https://github.com/ezer-mackenzie/csv-salvage/actions/workflows/ci.yml/badge.svg)](https://github.com/ezer-mackenzie/csv-salvage/actions/workflows/ci.yml)
[![Publish](https://github.com/ezer-mackenzie/csv-salvage/actions/workflows/publish.yml/badge.svg)](https://github.com/ezer-mackenzie/csv-salvage/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/ezer-mackenzie/csv-salvage/branch/main/graph/badge.svg)](https://codecov.io/gh/ezer-mackenzie/csv-salvage)
[![PyPI](https://img.shields.io/pypi/v/csv-salvage.svg)](https://pypi.org/project/csv-salvage/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)
[![Python Versions](https://img.shields.io/pypi/pyversions/csv-salvage.svg)](https://pypi.org/project/csv-salvage/)

**csv-salvage** is a high-performance, fault-tolerant CSV salvage and reconstruction engine written in Rust with native Python bindings (via PyO3 & Maturin).

It rescues corrupted, malformed, and irregular CSV data in scenarios where **Polars, DuckDB, and Pandas fail and throw `ParserError`**.

---

## 💥 The Pain Point It Solves

Real-world datasets from legacy systems, mainframe exports, and unvalidated third-party vendors often generate severely corrupted CSV files:

* **Unescaped newlines inside text cells:** Line breaks breaking rows in half without proper quote enclosures.
* **Unbalanced or orphan quotes:** Stray quotes inside text fields (e.g. `101,"15" Monitor",49.99`) throwing parsers completely out of sync.
* **Variable delimiters:** Inconsistent separators across files or mixed comma/semicolon/tab dialects.
* **Inconsistent column counts (ragged rows):** Missing trailing columns, phantom extra delimiters, or unexpected column drift.

### The Current State of the Art (And Why It Fails)
Today, data engineers and analysts resort to writing **slow, brittle Python regular expression scripts** to clean and patch corrupted files line-by-line before feeding them into Pandas, DuckDB, or Polars. These scripts take hours on multi-gigabyte datasets, consume massive RAM, and break on unseen edge cases.

---

## ⚡ Core Architecture in Rust

* **DFA & State-Machine Parser:** Custom finite state automaton (DFA via manual state machine or `regex-automata`) engineered specifically for error-recovery, token resynchronization, and zero-panic resilience.
* **Schema Inference Heuristics:** Adaptive detection of expected column counts, delimiters, and dialect conventions even in chaotic files.
* **Parallel Row Normalization:** Parsed rows are normalized with Rayon in parallel for larger inputs (1,024 or more rows); quote-aware parsing remains sequential to preserve multiline CSV boundaries.
* **Memory-Mapped File Input:** File-based APIs read from a read-only mapping instead of first allocating a second full-size input buffer.

---

## 🌟 Value Proposition

1. **"Lifesaver" Mode (Zero Panic Guarantee):**
   * The parser **never crashes**.
   * Automatically repairs orphan quotes and equalizes ragged rows.
   * If a row is mathematically unrecoverable, it cleanly routes the corrupted record into a dedicated **discard / quarantine stream** (with line numbers and diagnostic reasons) rather than halting execution.
2. **Parallel Batch Normalization:**
   * Uses `rayon` to normalize large batches of parsed rows in parallel while preserving row order.
   * Exports directly to cleaned, RFC-4180-compliant CSV files ready for instant loading into DuckDB, Polars, or Pandas.
   * Provides a Python iterator for salvaged rows.

---

## 📦 Installation

```bash
# Using pip
pip install csv-salvage

# Using uv
uv add csv-salvage
```

*(Pre-built wheels are compiled for Linux, musllinux, macOS, and Windows across major architectures).*

---

## 🚀 Quickstart & Proposed API

### 1. Rescuing Corrupted Files for DuckDB / Polars Ingestion

```python
import csv_salvage as cs

# Repair a corrupt CSV file and route unrecoverable rows to quarantine
summary = cs.salvage_file(
    input_path="legacy_export_corrupted.csv",
    output_path="clean_data.csv",
    quarantine_path="discarded_rows.log",
    repair_quotes=True,       # Auto-fix orphan/unbalanced quotes
    fill_ragged_rows=True,    # Pad short rows with empty strings
)

print(f"Total Rows:     {summary.total_rows}")
print(f"Salvaged Rows:  {summary.salvaged_rows}")
print(f"Quarantined:    {summary.quarantined_rows}")

# Now load clean_data.csv into Polars or DuckDB with zero errors!
import duckdb
df = duckdb.read_csv("clean_data.csv")
```

### 2. Native Python Streaming

```python
import csv_salvage as cs

# Iterate over salvaged rows
with cs.open("broken_records.csv") as stream:
    for record in stream:
        process_row(record)
```

### 3. Command-Line Usage

```bash
csv-salvage fix broken.csv --output clean.csv --quarantine discarded.csv
```

Use `--delimiter ';'` or `--expected-columns 5` to override inference. The
`--no-fill-ragged-rows`, `--no-merge-overflow`, and `--no-repair-quotes` options
disable the corresponding repairs. `python -m csv_salvage` provides the same
interface.

### 4. Optional PyArrow and Polars integrations

Install only the adapter you need:

```bash
pip install "csv-salvage[arrow]"
# or
pip install "csv-salvage[polars]"
```

```python
import csv_salvage as cs

arrow_table = cs.read_pyarrow("broken.csv", column_names=["id", "name", "role"])
polars_frame = cs.read_polars("broken.csv", column_names=["id", "name", "role"])
```

Both APIs eagerly materialize repaired rows as string columns; they do not
provide zero-copy parsing. Input header rows remain data rows, matching
`cs.open()`; `column_names` only labels the result columns. Rows quarantined by
the normalization settings are omitted from the dataframe.

File-based salvage uses memory-mapped input. The parser still materializes
parsed rows, so this reduces the raw-input copy but does not provide constant
memory usage. Do not modify an input file while a salvage operation is running.

### 5. Rust Library Usage

```rust
use csv_salvage::{SalvageOptions, rust_salvage_file};

let options = SalvageOptions::default();

let summary = rust_salvage_file(
    "corrupted.csv",
    "clean.csv",
    Some("quarantine.csv"),
    &options,
)?;

println!("Successfully salvaged {} rows!", summary.salvaged_rows);
```

---

## 🗺️ Roadmap

- [x] v0.1: resilient parser, dialect inference, row repair, and Python bindings.
- [x] v0.2: release automation and cross-platform CI.
- [x] v0.3: parallel normalization of large row sets and accelerated quote lookahead.
- [x] v0.4: CLI for file repair.
- [x] v0.5: optional PyArrow and Polars integrations.
- [x] v0.6: memory-mapped file input and configurable performance comparisons.
- [x] v0.7: optional comparisons with CleverCSV, pandas, and a constrained regex repair baseline.
- [ ] v1.0: benchmark suite, stable API/support contract, and production-readiness review.

---

## 🛠️ Development & Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, development commands, and coding guidelines.

```powershell
# Synchronize environment
uv sync

# Build & install locally in editable development mode
uv run maturin develop --uv

# Run Rust unit tests
cargo test

# Run Python integration and release tests
uv run python -m unittest discover -s tests -v

# Compare parser and adapter throughput (optional adapters run when installed)
uv run tools/benchmark.py
# Install CleverCSV and pandas to enable the full comparison suite
uv sync --group bench
uv run tools/benchmark.py
# Scale the generated input; for example, target approximately 1 million data rows
$env:CSV_SALVAGE_BENCH_ROWS = "1000000"
uv run tools/benchmark.py

# Check formatting and lints
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings

# Build documentation strictly
uv run --group docs mkdocs build --strict
```

The benchmark suite checks row counts before timing each implementation. Its
regex cleanup baseline only handles single-line, comma-separated rows with
unescaped quotes; it is a narrow comparison case, not a general CSV repair
strategy. Timings are informational and are not a claim that parsers perform
equivalent recovery or validation work.

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE.md).
