# csv-salvage

`csv-salvage` is a high-performance, fault-tolerant CSV salvage and reconstruction engine.
It rescues corrupted, malformed CSV files where strict parsers (Polars, DuckDB, Pandas, standard `csv`)
abort with unrecoverable `ParserError`.

Powered by a native Rust core and PyO3 bindings, `csv-salvage` provides native speed while exposing
an ergonomic Python interface.

## What it provides

- **DFA & State-Machine Tokenizer:** Disambiguates stray or unescaped orphan quotes (e.g. `101,"15" Monitor",49.99`) without data truncation.
- **Embedded Newline Recovery:** Handles multiline text records without desynchronizing column boundaries.
- **Dialect & Schema Sniffing:** Infers delimiters (`,`, `;`, `\t`, `|`) and column counts automatically using statistical mode heuristics.
- **Ragged Row Normalization:** Automatically pads short rows and merges overflow tokens.
- **Quarantine Stream:** Routes mathematically unrecoverable rows to an isolated diagnostic log without aborting execution.
- **Zero-Panic Guarantee:** Safe execution in production pipelines with graceful error handling.

## Quick example

```python
import csv_salvage as cs

# Repair a corrupted CSV file directly
summary = cs.salvage_file(
    input_path="corrupted_legacy_export.csv",
    output_path="clean_standard.csv",
    quarantine_path="discarded_rows.log",
)

print(f"Salvaged {summary.salvaged_rows} of {summary.total_rows} rows.")
print(f"Repaired rows: {summary.repaired_rows}, Quarantined: {summary.quarantined_rows}")
```

Continue with [Getting started](getting-started.md), or inspect the
[API reference](api.md), [Architecture](architecture.md),
[Support and heuristics](support.md), and [Roadmap to 1.0](roadmap-1.0.md).
