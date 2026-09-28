# Architecture

```text
Python Application (Pandas, Polars, DuckDB, Pipelines)
    |
    v
Public Python API (csv_salvage)
    |
    v
PyO3 native extension: _csv_salvage_backend
    |
    v
Rust Core Engine:
  ├── ResilientParser (DFA state machine, quote disambiguation)
  ├── Sniffer & Schema Heuristics (delimiter sniffing, mode column inference)
  └── Salvage Pipeline (ragged row padding, overflow merging, quarantine stream)
```

## Python Layer

The Python layer provides the high-level public interface:

- Typed API with IDE autocomplete and type hints (`py.typed`, `_csv_salvage_backend.pyi`).
- Public exceptions hierarchy in `csv_salvage.errors`.
- Convenient streaming iterator and context manager via `csv_salvage.open()`.
- Standard RFC-4180 file export via `csv_salvage.salvage_file()`.

The `_csv_salvage_backend` extension name is intentionally private. Applications should import from the public `csv_salvage` module directly.

## Rust Layer

The Rust core is built for maximum throughput and resilience:

- **Zero-Panic Guarantee:** Uses `Result<T, SalvageError>` internally and avoids panics on malformed input.
- **DFA State Machine:** Manages in-cell transitions between unquoted, quoted, escaped, and trailing quote states.
- **Zero-Copy Byte Slices:** Operates on raw byte slices for high parsing throughput.
- **Decoupled Architecture:** Core logic (`parser`, `heuristics`, `salvage`, `error`) is decoupled from PyO3, allowing standalone Rust usage.
