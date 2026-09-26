# CLAUDE.md

This file provides context and operational guidelines for Claude Code interacting with `csv-salvage`.

## Core Mission
- **Name:** `csv-salvage`
- **Objective:** High-performance, fault-tolerant CSV salvage and reconstruction engine.
- **Problem Solved:** Rescues corrupted/malformed CSVs where Polars, DuckDB, and Pandas fail with `ParserError` (unescaped newlines inside cells, unbalanced quotes, variable delimiters, ragged columns). Replaces slow, brittle Python regex scripts.
- **Architecture:** Rust (2024 edition) DFA / finite state machine parser with PyO3 bindings, parallel processing via `rayon`, and schema inference heuristics.
- **Lifesaver Mode:** Zero-panic guarantee. Automatically repairs orphan quotes and routes unrecoverable rows to a quarantine stream with diagnostics.

## Commands
- **Build development package:** `maturin develop`
- **Build release wheels:** `maturin build --release`
- **Rust Tests:** `cargo test`
- **Python Tests:** `pytest`
- **Formatting:** `cargo fmt --all -- --check` / `cargo fmt --all`
- **Clippy:** `cargo clippy --all-targets --all-features -- -D warnings`
- **Python Linting:** `ruff check .` and `ruff format --check .`

## CI/CD Workflow Rules
- `ci.yml`: Runs on pushes to `main`, pull requests, and tags (fmt, clippy, unit tests, codecov, smoke builds).
- `publish.yml`: Runs strictly on tags (`v*`) and manual dispatch. Always gates execution on `ci.yml` passing first, then builds multi-platform wheels and publishes to PyPI and GitHub Releases.

## Git Commit Conventions
All commits **MUST follow Conventional Commits** (`<type>(<scope>): <description>` in imperative mood):
- `feat:` New features or capabilities.
- `fix:` Bug fixes or parser heuristic repairs.
- `refactor:` Code restructuring without behavior changes.
- `ci:` CI/CD and GitHub Actions workflow changes.
- `perf:` Performance optimizations or memory improvements.
- `test:` Adding or updating unit tests/benchmarks.
- `docs:` Documentation updates only.
- `chore:` Dependency bumps, tool configuration, maintenance.

See [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) for deeper architecture notes.

