from __future__ import annotations

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from csv_salvage.cli import main


class CommandLineTests(unittest.TestCase):
    def test_fix_writes_repaired_csv_and_reports_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "broken.csv"
            output_path = root / "clean.csv"
            quarantine_path = root / "quarantine.csv"
            input_path.write_text(
                'id,name,role\n1,Alice,Engineer\n2,"15" Monitor"\n',
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "fix",
                        str(input_path),
                        "--out",
                        str(output_path),
                        "--quarantine",
                        str(quarantine_path),
                        "--expected-columns",
                        "3",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Processed 3 rows: 3 salvaged", stdout.getvalue())
            with output_path.open(encoding="utf-8", newline="") as output_file:
                rows = list(csv.reader(output_file))
            self.assertEqual(rows[-1], ["2", '15" Monitor', ""])
            self.assertTrue(quarantine_path.is_file())

    def test_invalid_input_returns_error_status(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(["fix", "missing-input.csv", "--output", "clean.csv"])

        self.assertEqual(exit_code, 2)
        self.assertIn("Input file not found", stderr.getvalue())

    def test_non_positive_column_count_is_rejected_by_argument_parser(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            main(
                [
                    "fix",
                    "input.csv",
                    "--output",
                    "output.csv",
                    "--expected-columns",
                    "0",
                ]
            )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("must be a positive integer", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
