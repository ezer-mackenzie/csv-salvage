# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Extend benchmark comparisons to CleverCSV, pandas, and representative cleanup scripts for v1.0.0.

## [0.6.0] - 2026-10-20

### Added
- Read-only memory-mapped input for file salvage and `SalvageReader`, avoiding a separate full-file input buffer.
- Configurable, standard-library benchmark comparisons for Python's CSV parser, csv-salvage file APIs, and installed PyArrow/Polars adapters.
- Tests for empty inputs and in-place file salvage.

### Changed
- Document that memory mapping removes the raw input copy but does not make row parsing or dataframe adapters constant-memory.

## [0.5.0] - 2026-10-19

### Added
- Optional `read_pyarrow()` and `read_polars()` adapters that return string-typed tables using separately installable extras.
- Configurable output column names for Arrow and Polars results.

### Changed
- Document that dataframe integrations currently materialize parsed rows and do not promise zero-copy parsing.

## [0.4.0] - 2026-10-19

### Added
- `csv-salvage fix` command for repairing CSV files, configuring row normalization, and optionally writing quarantined rows.
- `python -m csv_salvage` entry point for environments where the console script is unavailable.

## [0.3.0] - 2026-10-19

### Added
- Parallel row normalization with Rayon for inputs containing at least 1,024 parsed rows, preserving output order.
- SIMD-accelerated byte searching with `memchr` while looking ahead for quote-closing candidates.

### Fixed
- Quarantine diagnostics now report each record's starting source line, including rows following embedded newlines.

## [0.2.0] - 2026-10-01

### Changed
- Streamlined CI pipeline (`.github/workflows/ci.yml`) by delegating the multi-platform wheel matrix build strictly to release publishing, keeping CI fast (< 2 min) for all pushes and pull requests.
- Moved `extension-module` into an optional Cargo feature in `Cargo.toml` to support pure Rust test compilation without linking against Python shared libraries.

### Fixed
- Resolved macOS test linking errors by passing `--no-default-features` and dynamic lookup linker flags during CI test runs.
- Resolved `typing_extensions` import failure on Python 3.9/3.10 during isolated wheel verification by adding graceful fallback handling in `reader.py`.
- Fixed refspec resolution bug in `publish.yml` during git tag push events.
- Integrated automated GitHub Release asset upload and release notes generation using `softprops/action-gh-release@v2`.

## [0.1.0] - 2026-09-25

### Added
- Resilient DFA & state-machine tokenizer (`src/parser.rs`) capable of disambiguating unescaped stray quotes (e.g. `101,"15" Monitor",49.99`) and recovering multiline cells with a Zero-Panic Guarantee.
- Dialect sniffer and schema inference heuristics (`src/heuristics.rs`) for automatic delimiter detection (`,`, `;`, `\t`, `|`) and column count inference based on statistical mode.
- Core salvage and normalization engine (`src/salvage.rs`) featuring ragged row padding, overflow column merging, and dedicated quarantine logging with diagnostic reasons.
- Native Python bindings via PyO3 0.29:
  - `csv_salvage.salvage_file(...)` returning a detailed `SalvageSummary`.
  - `csv_salvage.sniff(...)` for standalone delimiter detection.
  - `csv_salvage.SalvageReader(...)` streaming iterator.
- Benchmarking suite powered by `benchcore` (`tools/benchmark.py`) for measuring delimiter sniffing, streaming iterator throughput, and end-to-end file salvage performance.
- Initial project scaffolding using Rust 2024 edition, PyO3, and Maturin.
- Multi-platform CI pipeline (`.github/workflows/ci.yml`) covering Rust formatting (`cargo fmt`), Clippy linting, unit testing, Codecov integration, and multi-OS smoke builds.
- Automated release workflow (`.github/workflows/publish.yml`) triggered on tags (`v*`) with CI-status verification, multi-platform wheel generation (Linux glibc & musl, Windows, macOS, and sdist), build provenance attestations, PyPI publishing, and GitHub Releases.
- Automated Dependabot PR auto-merge workflow.
- Full English documentation suite: `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `AGENTS.md`, and `CLAUDE.md`.
- Apache 2.0 license configuration.
