"""Benchmark suite for csv-salvage powered by benchcore."""
from __future__ import annotations

import tempfile
from pathlib import Path

from benchcore import Bench
from benchcore.core.models.benchmark_config import BenchmarkConfig
from benchcore.reporting import TerminalReporter, create_report

import csv_salvage

SAMPLE_MALFORMED_CSV = """id,name,description,price,status
1,Widget A,"Clean standard item",19.99,active
2,Widget B,"Unescaped "quote" in middle",29.99,active
3,Widget C,"Multiline
description with unescaped newline",39.99,pending
4,Widget D,Missing closing quote, active, extra_column_data
5,Widget E,"Normal",49.99
6,Widget F,"Another "broken" quote",59.99,archived
7,Widget G,"Ragged row with missing columns"
8,Widget H,"Valid item",89.99,active
""" * 50


def benchmark_sniffer() -> None:
    csv_salvage.sniff(SAMPLE_MALFORMED_CSV)


def run_benchmarks() -> None:
    print("=" * 60)
    print(" Running csv-salvage benchmarks with BenchCore")
    print("=" * 60)

    config = BenchmarkConfig(rounds=5, target_round_time_ns=50_000_000)
    runner = Bench(config=config)
    reporter = TerminalReporter()

    # 1. Delimiter Sniffing
    print("\n[1/3] Benchmarking Delimiter Sniffing...")
    sniff_result = runner.run(benchmark_sniffer)
    sniff_report = create_report("csv_salvage.sniff", sniff_result)
    print(reporter.render(sniff_report))

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_file = Path(tmp_dir) / "corrupted_input.csv"
        input_file.write_text(SAMPLE_MALFORMED_CSV, encoding="utf-8")
        clean_file = Path(tmp_dir) / "salvaged_clean.csv"
        quarantine_file = Path(tmp_dir) / "quarantined.csv"

        # 2. Streaming with SalvageReader
        def benchmark_streaming() -> int:
            row_count = 0
            with csv_salvage.SalvageReader(input_file) as reader:
                for row in reader:
                    row_count += len(row)
            return row_count

        print("\n[2/3] Benchmarking SalvageReader Streaming...")
        stream_result = runner.run(benchmark_streaming)
        stream_report = create_report("csv_salvage.SalvageReader (streaming)", stream_result)
        print(reporter.render(stream_report))

        # 3. End-to-End File Salvage
        def benchmark_salvage_file() -> None:
            csv_salvage.salvage_file(
                input_file,
                clean_file,
                quarantine_path=quarantine_file,
            )

        print("\n[3/3] Benchmarking End-to-End File Salvage...")
        salvage_result = runner.run(benchmark_salvage_file)
        salvage_report = create_report("csv_salvage.salvage_file (disk I/O)", salvage_result)
        print(reporter.render(salvage_report))

    print("=" * 60)
    print(" All benchmarks completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmarks()
