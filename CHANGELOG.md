# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Parallel multi-threaded file normalization and chunking engine using `rayon`.
- Direct zero-copy export to Apache Arrow RecordBatches for DuckDB and Polars integration.
- Comprehensive benchmark suite comparing performance against Python regex scripts, standard `csv`, `clevercsv`, and `pandas`.
- CLI tool (`csv-salvage fix input.csv --output clean.csv`).

## [0.1.0] - 2026-09-25

### Added
- Resilient DFA & state-machine tokenizer (`src/parser.rs`) capable of disambiguating unescaped stray quotes (e.g. `101,"15" Monitor",49.99`) and recovering multiline cells with a Zero-Panic Guarantee.
- Dialect sniffer and schema inference heuristics (`src/heuristics.rs`) for automatic delimiter detection (`,`, `;`, `\t`, `|`) and column count inference based on statistical mode.
- Core salvage and normalization engine (`src/salvage.rs`) featuring ragged row padding, overflow column merging, and dedicated quarantine logging with diagnostic reasons.
- Native Python bindings via PyO3 0.29:
  - `csv_salvage.salvage_file(...)` returning a detailed `SalvageSummary`.
  - `csv_salvage.sniff(...)` for standalone delimiter detection.
  - `csv_salvage.SalvageReader(...)` streaming iterator.
- Initial project scaffolding using Rust 2024 edition, PyO3, and Maturin.
- Multi-platform CI pipeline (`.github/workflows/ci.yml`) covering Rust formatting (`cargo fmt`), Clippy linting, unit testing, Codecov integration, and multi-OS smoke builds.
- Automated release workflow (`.github/workflows/publish.yml`) triggered on tags (`v*`) with CI-status verification, multi-platform wheel generation (Linux glibc & musl, Windows, macOS, and sdist), build provenance attestations, PyPI publishing, and GitHub Releases.
- Automated Dependabot PR auto-merge workflow.
- Full English documentation suite: `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `AGENTS.md`, and `CLAUDE.md`.
- Apache 2.0 license configuration.
