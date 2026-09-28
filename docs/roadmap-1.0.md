# Roadmap to 1.0

This document outlines the milestones and roadmap leading to the 1.0 production release of `csv-salvage`.

---

## v0.1.0 (Current)

- [x] Initial Rust DFA state-machine tokenizer.
- [x] Disambiguation of unescaped and stray quotes.
- [x] Automatic delimiter sniffing and schema/column inference.
- [x] Ragged row normalization (padding and overflow merging).
- [x] Quarantine diagnostic stream for unrecoverable records.
- [x] PyO3 Python bindings and streaming reader.
- [x] GitHub CI and multi-platform publishing workflows.

---

## v0.2.0 (Parallelism & Performance)

- [ ] Multi-threaded parallel chunk parsing using `rayon`.
- [ ] SIMD-accelerated delimiter and newline scanning (`memchr`).
- [ ] Memory-mapped file I/O for multi-gigabyte dataset salvage.

---

## v0.3.0 (Ecosystem Integrations)

- [ ] Direct Arrow RecordBatch export for zero-copy DuckDB and Polars ingestion:
  ```python
  df = cs.read_polars("corrupt.csv")
  ```
- [ ] Dedicated command-line interface (`csv-salvage fix input.csv --out clean.csv`).

---

## v1.0.0 (Production Hardening)

- [ ] Zero-copy stream normalization benchmarks against CleverCSV and custom regex cleanups.
- [ ] Support contract freezing and stable public API commitment.
