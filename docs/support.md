# Support and heuristics

## Supported Platforms and Environments

`csv-salvage` provides precompiled binary wheels for:

- **Linux**: x86_64, aarch64 (glibc and musl)
- **Windows**: x64, x86, arm64
- **macOS**: Apple Silicon (aarch64) and Intel (x86_64)

### Python Compatibility

- Standard CPython 3.9 through 3.14.
- Compatible with PyPy 3.9+.

### Rust MSRV

- Minimum Supported Rust Version: **1.85.0**.

---

## Dialect & Sniffing Heuristics

`csv-salvage` implements resilient heuristics to detect file structure:

### Delimiter Sniffing
The sniffer samples up to 8KB of input text and tallies candidates (`,`, `;`, `\t`, `|`).
It ranks delimiters based on line-by-line consistency: the delimiter that produces the most uniform, non-zero token count across non-empty lines is selected.

### Column Inference
The column inference engine reads candidate rows across the sample and computes the statistical **mode** of token counts. Rows deviating from this mode are flagged for ragged row handling or quarantine.

### Quote Disambiguation
Internal unescaped quotes (e.g. `101,"15" Monitor",49.99`) are evaluated:
- If a quote is followed by delimiter or newline, it is treated as an enclosure delimiter.
- If preceded and followed by alphanumeric characters or symbols, it is preserved as an escaped literal quote (`""`).
