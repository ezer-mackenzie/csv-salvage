# csv-salvage

[![CI](https://github.com/eliezer-reuven/csv-salvage/actions/workflows/ci.yml/badge.svg)](https://github.com/eliezer-reuven/csv-salvage/actions/workflows/ci.yml)
[![Publish](https://github.com/eliezer-reuven/csv-salvage/actions/workflows/publish.yml/badge.svg)](https://github.com/eliezer-reuven/csv-salvage/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/eliezer-reuven/csv-salvage/branch/main/graph/badge.svg)](https://codecov.io/gh/eliezer-reuven/csv-salvage)
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
* **Parallel Normalization with Rayon:** Multi-threaded chunking and parallel repair using `rayon` to saturate multi-core CPUs during large batch salvage.

---

## 🌟 Value Proposition

1. **"Lifesaver" Mode (Zero Panic Guarantee):**
   * The parser **never crashes**.
   * Automatically repairs orphan quotes and equalizes ragged rows.
   * If a row is mathematically unrecoverable, it cleanly routes the corrupted record into a dedicated **discard / quarantine stream** (with line numbers and diagnostic reasons) rather than halting execution.
2. **High-Throughput Parallel Normalization:**
   * Utilizes `rayon` to repair and normalize large files in parallel.
   * Exports directly to cleaned, RFC-4180-compliant CSV files ready for instant loading into DuckDB, Polars, or Pandas.
   * Streams repaired dictionaries or tuples directly into Python at native C/Rust speed.

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
    fill_ragged_rows=True,    # Pad short rows with nulls
    threads=8                 # Parallel normalization via Rayon
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

# Stream cleaned rows directly as Python tuples/dicts at native speed
with cs.open("broken_records.csv", mode="lifesaver") as stream:
    for record in stream:
        # record is a clean list of string tokens
        process_row(record)
        
    for discarded in stream.quarantine:
        print(f"Line {discarded.line_number}: {discarded.raw_line} -> {discarded.reason}")
```

### 3. Rust Crate Usage

```rust
use csv_salvage::{SalvageEngine, SalvageOptions};

let options = SalvageOptions::builder()
    .repair_quotes(true)
    .fill_ragged_rows(true)
    .build();

let engine = SalvageEngine::new(options);
let summary = engine.salvage_file_parallel("corrupted.csv", "clean.csv", Some("quarantine.csv"))?;

println!("Successfully salvaged {} rows!", summary.salvaged_rows);
```

---

## 🗺️ Roadmap

- [x] Initial scaffolding (Rust 2024 edition, PyO3, Maturin).
- [x] Multi-platform CI pipeline with formatting, clippy, unit testing, and Codecov.
- [x] Automated tag-triggered release workflow (`publish.yml`) with build provenance attestations, PyPI publishing, and GitHub Releases.
- [ ] Core DFA / state-machine salvage tokenizer.
- [ ] Orphan quote repair and newline resynchronization heuristics.
- [ ] Multi-threaded parallel file processing with `rayon`.
- [ ] Discard / quarantine stream with diagnostic error logging.
- [ ] Direct export to Apache Arrow format for zero-copy Polars / DuckDB handoff.
- [ ] Benchmarks against Python regex scripts, standard `csv`, and `clevercsv`.

---

## 🛠️ Development & Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, development commands, and coding guidelines.

```bash
# Clone and enter repo
git clone https://github.com/eliezer-reuven/csv-salvage.git
cd csv-salvage

# Build & install locally in development mode
maturin develop

# Run tests
cargo test
```

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE.md).
