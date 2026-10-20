"""Compare salvage parsing and repair with CSV libraries and a regex baseline."""

from __future__ import annotations

import csv
import importlib.util
import os
import re
import statistics
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

import csv_salvage

DEFAULT_ROWS = 50_000
_ORPHAN_QUOTE = re.compile(r'(?<=[^,])"(?!,|$)')


def _positive_row_count() -> int:
    raw_value = os.environ.get("CSV_SALVAGE_BENCH_ROWS", str(DEFAULT_ROWS))
    try:
        row_count = int(raw_value)
    except ValueError as exc:
        raise ValueError("CSV_SALVAGE_BENCH_ROWS must be a positive integer") from exc
    if row_count <= 0:
        raise ValueError("CSV_SALVAGE_BENCH_ROWS must be a positive integer")
    return row_count


def _write_dataset(path: Path, row_count: int, *, malformed: bool = False) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        if malformed:
            output.write("id,name,description,price,status\n")
            for index in range(row_count):
                description = f'Description with "orphan" quote {index}'
                output.write(
                    f'{index},Widget {index},"{description}",'
                    f"{index / 100:.2f},{'active' if index % 2 == 0 else 'pending'}\n"
                )
            return

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


def _regex_cleaned_lines(lines: Iterable[str]) -> Iterator[str]:
    """Repair unescaped quotes in simple, single-line comma-separated fields."""
    for line in lines:
        yield _ORPHAN_QUOTE.sub('""', line)


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
    print(" Comparing csv-salvage with CSV readers and a regex cleanup baseline")
    print("=" * 60)
    print(f"Dataset rows: {row_count:,} (set CSV_SALVAGE_BENCH_ROWS to change)")
    print(
        "Valid-CSV reader timings exclude headers; salvage_file also writes output, "
        "and dataframe adapters materialize columns. The regex baseline only repairs "
        "single-line comma-separated rows with unescaped quotes; it is not a "
        "general-purpose CSV repairer."
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_file = Path(tmp_dir) / "benchmark.csv"
        malformed_file = Path(tmp_dir) / "malformed.csv"
        clean_file = Path(tmp_dir) / "clean.csv"
        _write_dataset(input_file, row_count)
        _write_dataset(malformed_file, row_count, malformed=True)
        print(f"Input size: {input_file.stat().st_size:,} bytes")
        print(f"Malformed input size: {malformed_file.stat().st_size:,} bytes")

        def benchmark_python_csv() -> int:
            with input_file.open("r", encoding="utf-8", newline="") as source:
                return sum(1 for _ in csv.reader(source)) - 1

        def benchmark_salvage_reader() -> int:
            with csv_salvage.open(input_file) as reader:
                return sum(1 for _ in reader) - 1

        expected_rows = row_count
        _assert_row_count("Python csv.reader", benchmark_python_csv(), expected_rows)
        _assert_row_count(
            "csv-salvage reader", benchmark_salvage_reader(), expected_rows
        )

        print("\n[1] Valid CSV parser comparison")
        _run_benchmark("python.csv.reader", benchmark_python_csv, expected_rows)

        _run_benchmark("csv_salvage.open", benchmark_salvage_reader, expected_rows)

        def benchmark_clevercsv() -> int:
            import clevercsv

            with input_file.open("r", encoding="utf-8", newline="") as source:
                return sum(1 for _ in clevercsv.reader(source)) - 1

        if importlib.util.find_spec("clevercsv") is not None:
            _assert_row_count("CleverCSV", benchmark_clevercsv(), expected_rows)
            _run_benchmark("clevercsv.reader", benchmark_clevercsv, expected_rows)
        else:
            print("Skipping CleverCSV: install with `uv sync --group bench`.")

        def benchmark_pandas() -> int:
            import pandas

            return len(pandas.read_csv(input_file))

        if importlib.util.find_spec("pandas") is not None:
            _assert_row_count("pandas", benchmark_pandas(), expected_rows)
            _run_benchmark("pandas.read_csv", benchmark_pandas, expected_rows)
        else:
            print("Skipping pandas: install with `uv sync --group bench`.")

        def benchmark_salvage_file() -> int:
            return csv_salvage.salvage_file(input_file, clean_file).salvaged_rows - 1

        _assert_row_count(
            "csv-salvage file API", benchmark_salvage_file(), expected_rows
        )
        _run_benchmark(
            "csv_salvage.salvage_file", benchmark_salvage_file, expected_rows
        )

        print("\n[2] Corrupted CSV repair comparison")

        def benchmark_regex_cleanup() -> int:
            with malformed_file.open("r", encoding="utf-8", newline="") as source:
                return sum(1 for _ in csv.reader(_regex_cleaned_lines(source))) - 1

        def benchmark_salvage_malformed() -> int:
            with csv_salvage.open(malformed_file) as reader:
                return sum(1 for _ in reader) - 1

        _assert_row_count("regex cleanup", benchmark_regex_cleanup(), expected_rows)
        _assert_row_count(
            "csv-salvage malformed reader",
            benchmark_salvage_malformed(),
            expected_rows,
        )
        _run_benchmark(
            "regex_cleanup + csv.reader", benchmark_regex_cleanup, expected_rows
        )
        _run_benchmark(
            "csv_salvage.open (malformed)",
            benchmark_salvage_malformed,
            expected_rows,
        )

        print("\n[3] Optional dataframe adapters")
        if importlib.util.find_spec("pyarrow") is not None:

            def benchmark_pyarrow() -> int:
                return csv_salvage.read_pyarrow(input_file).num_rows - 1

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
                return csv_salvage.read_polars(input_file).height - 1

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
