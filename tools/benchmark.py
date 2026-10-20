"""Compare salvage parsing and its optional dataframe adapters with Python csv."""
from __future__ import annotations

import csv
import importlib.util
import os
import statistics
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import csv_salvage

DEFAULT_ROWS = 50_000


def _positive_row_count() -> int:
    raw_value = os.environ.get("CSV_SALVAGE_BENCH_ROWS", str(DEFAULT_ROWS))
    try:
        row_count = int(raw_value)
    except ValueError as exc:
        raise ValueError("CSV_SALVAGE_BENCH_ROWS must be a positive integer") from exc
    if row_count <= 0:
        raise ValueError("CSV_SALVAGE_BENCH_ROWS must be a positive integer")
    return row_count


def _write_dataset(path: Path, row_count: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("id", "name", "description", "price", "status"))
        for index in range(row_count):
            writer.writerow(
                (
                    index,
                    f"Widget {index}",
                    f"Representative product description {index}",
                    f"{index / 100:.2f}",
                    "active" if index % 2 == 0 else "pending",
                )
            )


def _assert_row_count(name: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise RuntimeError(f"{name} returned {actual} rows; expected {expected}")


def _run_benchmark(name: str, fn: Callable[[], int], row_count: int) -> None:
    durations = []
    for _ in range(5):
        start = time.perf_counter_ns()
        fn()
        durations.append(time.perf_counter_ns() - start)
    median_ns = statistics.median(durations)
    print(
        f"{name}: median={median_ns / 1_000_000:.3f} ms, "
        f"range={min(durations) / 1_000_000:.3f}-"
        f"{max(durations) / 1_000_000:.3f} ms, "
        f"throughput={row_count / (median_ns / 1_000_000_000):,.0f} rows/s "
        "(5 rounds)"
    )


def run_benchmarks() -> None:
    row_count = _positive_row_count()
    print("=" * 60)
    print(" Comparing csv-salvage with Python CSV readers")
    print("=" * 60)
    print(f"Dataset rows: {row_count:,} (set CSV_SALVAGE_BENCH_ROWS to change)")
    print(
        "Python csv is a parse-only reference; salvage and adapter timings include "
        "inference, normalization, and materialization."
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_file = Path(tmp_dir) / "benchmark.csv"
        clean_file = Path(tmp_dir) / "clean.csv"
        _write_dataset(input_file, row_count)
        print(f"Input size: {input_file.stat().st_size:,} bytes")

        def benchmark_python_csv() -> int:
            with input_file.open("r", encoding="utf-8", newline="") as source:
                return sum(1 for _ in csv.reader(source))

        def benchmark_salvage_reader() -> int:
            with csv_salvage.open(input_file) as reader:
                return sum(1 for _ in reader)

        expected_rows = row_count + 1
        _assert_row_count("Python csv.reader", benchmark_python_csv(), expected_rows)
        _assert_row_count(
            "csv-salvage reader", benchmark_salvage_reader(), expected_rows
        )

        print("\n[1/4] Python standard-library CSV parser")
        _run_benchmark("python.csv.reader", benchmark_python_csv, expected_rows)

        print("\n[2/4] csv-salvage reader (memory-mapped input)")
        _run_benchmark("csv_salvage.open", benchmark_salvage_reader, expected_rows)

        print("\n[3/4] csv-salvage end-to-end repair (mapped input + output I/O)")

        def benchmark_salvage_file() -> int:
            return csv_salvage.salvage_file(input_file, clean_file).salvaged_rows

        _assert_row_count(
            "csv-salvage file API", benchmark_salvage_file(), expected_rows
        )
        _run_benchmark(
            "csv_salvage.salvage_file", benchmark_salvage_file, expected_rows
        )

        print("\n[4/4] Optional dataframe adapters")
        if importlib.util.find_spec("pyarrow") is not None:
            def benchmark_pyarrow() -> int:
                return csv_salvage.read_pyarrow(input_file).num_rows

            _assert_row_count("PyArrow adapter", benchmark_pyarrow(), expected_rows)
            _run_benchmark(
                "csv_salvage.read_pyarrow",
                benchmark_pyarrow,
                expected_rows,
            )
        else:
            print("Skipping PyArrow adapter: install csv-salvage[arrow].")

        if importlib.util.find_spec("polars") is not None:
            def benchmark_polars() -> int:
                return csv_salvage.read_polars(input_file).height

            _assert_row_count("Polars adapter", benchmark_polars(), expected_rows)
            _run_benchmark(
                "csv_salvage.read_polars",
                benchmark_polars,
                expected_rows,
            )
        else:
            print("Skipping Polars adapter: install csv-salvage[polars].")

    print("=" * 60)
    print(" Benchmarks completed. Results depend on hardware, OS, and cache state.")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmarks()
