# Contributing to csv-salvage

Thank you for your interest in contributing to **csv-salvage**! We welcome bug reports, feature suggestions, test datasets, documentation improvements, and code contributions.

Please review this guide before submitting a pull request or opening an issue.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all community members with respect and kindness.

---

## How Can I Contribute?

### 1. Reporting Bugs & Malformed CSV Edge Cases
CSV corruption takes many bizarre forms in the real world. One of the highest-value contributions is sharing real-world or sanitized sample CSV snippets that break standard parsers or trip up `csv-salvage`.

When filing a bug report:
- Include a minimal reproducible example (MRE) or sample input data.
- Mention your environment (OS, Python version, Rust version).
- Describe the expected behavior versus the actual behavior (or error message).

### 2. Suggesting Features & Heuristics
If you have ideas for new repair heuristics, performance optimizations, or Python API improvements:
- Open a feature request issue.
- Explain the motivation and use cases.
- Provide pseudocode or examples if possible.

### 3. Submitting Pull Requests
- Keep changes focused: one PR per issue or feature.
- Include corresponding unit tests in Rust and/or Python.
- Ensure all CI checks (formatting, linter, tests) pass locally before opening the PR.
- Update `CHANGELOG.md` with a summary under the `[Unreleased]` section.

---

## Local Development Setup

### Prerequisites
- **Rust Toolchain:** Stable channel (1.80+ or 2024 edition compatible). Install via [rustup](https://rustup.rs/).
- **Python:** 3.8 or newer.
- **uv** (recommended) or **pip**:
  ```bash
  # Install uv (fast Python package manager)
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Or on Windows via PowerShell:
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **maturin:**
  ```bash
  pip install maturin
  ```

### Setting Up Your Environment

```bash
# 1. Clone your fork
git clone https://github.com/<your-username>/csv-salvage.git
cd csv-salvage

# 2. Create and activate a virtual environment
uv venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 3. Install development dependencies
pip install maturin pytest ruff

# 4. Compile and install in development mode (links the Rust extension into Python)
maturin develop
```

---

## Verification & Code Quality

Before committing, run the following checks:

### Rust Checks
```bash
# Format code
cargo fmt --all -- --check

# Run linter
cargo clippy --all-targets --all-features -- -D warnings

# Run Rust unit tests
cargo test --verbose
```

### Python Checks
```bash
# Lint and format check with Ruff
ruff check .
ruff format --check .

# Run Python tests (once test suite is populated)
pytest
```

---

## Git & Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

* `feat:` A new feature or user-facing functionality.
* `fix:` A bug fix or repair heuristic correction.
* `docs:` Documentation-only changes.
* `ci:` Changes to CI/CD workflows and automated pipelines.
* `refactor:` Code restructuring that does not fix a bug or add a feature.
* `perf:` Changes that improve performance or reduce memory allocations.
* `test:` Adding or updating tests.
* `chore:` Maintenance tasks, dependency bumps, etc.

Example:
```bash
git commit -m "feat: add heuristic quote disambiguation for unescaped text"
```

---

## Release Process

Releases are fully automated via GitHub Actions:
- Pushing a semver tag matching `v*` (e.g. `v0.1.0`) triggers `.github/workflows/publish.yml`.
- Multi-platform wheels are built for Linux, macOS, and Windows.
- Artifacts are attested with GitHub build provenance.
- The release is published to PyPI and attached to a new GitHub Release with auto-generated release notes.
