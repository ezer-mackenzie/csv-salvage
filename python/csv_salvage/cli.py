"""Command-line interface for csv-salvage."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .errors import SalvageError
from .salvage import salvage_file


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="csv-salvage")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fix_parser = subparsers.add_parser("fix", help="repair a malformed CSV file")
    fix_parser.add_argument("input", type=Path, help="path to the input CSV file")
    fix_parser.add_argument(
        "-o",
        "--out",
        "--output",
        required=True,
        type=Path,
        dest="output",
        help="path for the repaired CSV",
    )
    fix_parser.add_argument(
        "--quarantine", type=Path, help="optional path for unrecoverable rows"
    )
    fix_parser.add_argument(
        "--delimiter", help="single-character field delimiter (default: auto-detect)"
    )
    fix_parser.add_argument(
        "--quote-char", default='"', help='single-character quote (default: ")'
    )
    fix_parser.add_argument(
        "--expected-columns", type=_positive_int, help="expected number of columns"
    )
    fix_parser.add_argument(
        "--no-repair-quotes",
        action="store_false",
        dest="repair_quotes",
        help="do not repair stray quotes",
    )
    fix_parser.add_argument(
        "--no-fill-ragged-rows",
        action="store_false",
        dest="fill_ragged_rows",
        help="quarantine rows with too few columns instead of padding them",
    )
    fix_parser.add_argument(
        "--no-merge-overflow",
        action="store_false",
        dest="merge_overflow",
        help="quarantine rows with extra columns instead of merging them",
    )
    fix_parser.set_defaults(
        repair_quotes=True,
        fill_ragged_rows=True,
        merge_overflow=True,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return its process exit status."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        summary = salvage_file(
            input_path=args.input,
            output_path=args.output,
            quarantine_path=args.quarantine,
            delimiter=args.delimiter,
            quote_char=args.quote_char,
            fill_ragged_rows=args.fill_ragged_rows,
            merge_overflow=args.merge_overflow,
            expected_columns=args.expected_columns,
            repair_quotes=args.repair_quotes,
        )
    except (OSError, SalvageError, TypeError) as exc:
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return 2

    print(
        f"Processed {summary.total_rows} rows: "
        f"{summary.salvaged_rows} salvaged, "
        f"{summary.repaired_rows} repaired, "
        f"{summary.quarantined_rows} quarantined; "
        f"delimiter={summary.detected_delimiter!r}, "
        f"columns={summary.inferred_columns}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
