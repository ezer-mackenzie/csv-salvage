# Roadmap to 1.0

This document outlines the milestones and roadmap leading to the 1.0 production release of `csv-salvage`.

---

## v0.1.0

- [x] Initial Rust DFA state-machine tokenizer.
- [x] Disambiguation of unescaped and stray quotes.
- [x] Automatic delimiter sniffing and schema/column inference.
- [x] Ragged row normalization (padding and overflow merging).
- [x] Quarantine diagnostic stream for unrecoverable records.
- [x] PyO3 Python bindings and streaming reader.
- [x] GitHub CI and multi-platform publishing workflows.

---

## v0.2.0 (Published)

- [x] Core parser, inference, normalization, PyO3 bindings, and release automation.

The parallel processing and large-file I/O items planned for this version were not
included in the published `v0.2.0`; they are tracked in the next milestone.

## v0.3.0 (Performance)

- [x] Parallel row normalization using `rayon` for inputs with at least 1,024 parsed rows.
- [x] `memchr`-accelerated lookahead for quote-closing candidates.

Memory-mapped file I/O was deferred to v0.6.0.

## v0.4.0 (CLI)

- [x] CLI for repairing files, configuring repair options, and routing quarantine output.

## v0.5.0 (Ecosystem Integrations)

- [x] Optional PyArrow Table and Polars DataFrame APIs with separately installable dependencies.
- [x] Define current materialization and copy behavior; no zero-copy parsing claim.

## v0.6.0 (Scale and Validation)

- [ ] Memory-mapped file I/O for multi-gigabyte dataset salvage.
- [ ] Benchmark the native parser and integrations against representative alternatives.

---

## v1.0.0 (Production Hardening)

- [ ] Benchmark suite against CleverCSV, Python csv, and representative cleanup scripts.
- [ ] Support contract freezing and stable public API commitment.
