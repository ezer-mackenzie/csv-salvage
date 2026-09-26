# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Core salvage tokenizer based on finite state automata (DFA / manual state machine) in Rust.
- Heuristic orphan quote repair and unescaped newline resynchronization.
- Ragged row alignment policies (padding with nulls, truncation, and overflow bucket).
- "Lifesaver" mode ensuring zero panics on severely corrupted files.
- Dedicated quarantine stream routing mathematically unrecoverable rows with diagnostic reasons.
- Parallel file normalization and chunking engine using `rayon`.
- Python bindings via PyO3 exposing `salvage_file` and streaming `open` iterators returning dicts/tuples at native speed.
- Comprehensive benchmark suite comparing performance against Python regex scripts, standard `csv`, `clevercsv`, and `pandas`.

## [0.1.0] - 2026-09-25

### Added
- Initial project scaffolding using Rust 2024 edition, PyO3, and Maturin.
- Multi-platform CI pipeline (`.github/workflows/ci.yml`) covering Rust formatting (`cargo fmt`), Clippy linting, unit testing, Codecov integration, and multi-OS smoke builds.
- Automated release workflow (`.github/workflows/publish.yml`) triggered on tags (`v*`) with CI-status verification, multi-platform wheel generation (Linux glibc & musl, Windows, macOS, and sdist), build provenance attestations, PyPI publishing, and GitHub Releases.
- Automated Dependabot PR auto-merge workflow.
- Full English documentation suite: `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `AGENTS.md`, and `CLAUDE.md`.
- Apache 2.0 license configuration.
