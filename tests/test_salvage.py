from __future__ import annotations

import csv
import os
import tempfile
import unittest

import csv_salvage as cs


class SalvageIntegrationTests(unittest.TestCase):
    def test_metadata(self):
        self.assertTrue(hasattr(cs, "__version__"))
        self.assertIsInstance(cs.__version__, str)
        self.assertEqual(cs.__version__, "0.1.0")
        for symbol in ("salvage_file", "sniff", "open", "SalvageReader", "SalvageSummary"):
            self.assertIn(symbol, cs.__all__)

    def test_sniff_delimiter(self):
        sample_comma = "id,name,value\n1,Alpha,100\n2,Beta,200\n"
        self.assertEqual(cs.sniff(sample_comma), ",")

        sample_semi = "id;name;city\n1;Madrid;Spain\n2;Paris;France\n"
        self.assertEqual(cs.sniff(sample_semi), ";")

        sample_pipe = "a|b|c\n1|2|3\n4|5|6\n"
        self.assertEqual(cs.sniff(sample_pipe), "|")

    def test_salvage_file_orphan_quotes(self):
        corrupted_data = (
            'id,product,price\n'
            '101,"15" Monitor",49.99\n'
            '102,"Standard Widget",10.00\n'
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "corrupt.csv")
            output_path = os.path.join(tmpdir, "clean.csv")

            with open(input_path, "w", encoding="utf-8") as f:
                f.write(corrupted_data)

            summary = cs.salvage_file(input_path, output_path)

            self.assertEqual(summary.total_rows, 3)
            self.assertEqual(summary.salvaged_rows, 3)
            self.assertEqual(summary.detected_delimiter, ",")
            self.assertEqual(summary.inferred_columns, 3)

            summary_dict = summary.to_dict()
            self.assertEqual(summary_dict["total_rows"], 3)
            self.assertEqual(summary_dict["salvaged_rows"], 3)

            with open(output_path, "r", encoding="utf-8") as f:
                reader = list(csv.reader(f))

            self.assertEqual(len(reader), 3)
            self.assertEqual(reader[0], ["id", "product", "price"])
            self.assertEqual(reader[1], ["101", '15" Monitor', "49.99"])
            self.assertEqual(reader[2], ["102", "Standard Widget", "10.00"])

    def test_salvage_file_ragged_rows_and_quarantine(self):
        ragged_data = (
            "id,name,role\n"
            "1,Alice,Engineer\n"
            "2,Bob\n"  # Short row: 2 cols instead of 3
            "3,Charlie,Designer,ExtraField\n"  # Long row: 4 cols instead of 3
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "ragged.csv")
            output_path = os.path.join(tmpdir, "clean.csv")

            with open(input_path, "w", encoding="utf-8") as f:
                f.write(ragged_data)

            summary = cs.salvage_file(
                input_path,
                output_path,
                fill_ragged_rows=True,
                merge_overflow=True,
            )

            self.assertEqual(summary.total_rows, 4)
            self.assertEqual(summary.salvaged_rows, 4)
            self.assertEqual(summary.repaired_rows, 2)

            with open(output_path, "r", encoding="utf-8") as f:
                rows = list(csv.reader(f))

            self.assertEqual(rows[1], ["1", "Alice", "Engineer"])
            self.assertEqual(rows[2], ["2", "Bob", ""])
            self.assertEqual(rows[3], ["3", "Charlie", "Designer,ExtraField"])

    def test_salvage_reader_and_context_manager(self):
        sample = "col1,col2\nval1,val2\nval3,val4\n"

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.csv")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(sample)

            with cs.open(file_path) as reader:
                self.assertEqual(len(reader), 3)
                rows = list(reader)

            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], ["col1", "col2"])
            self.assertEqual(rows[1], ["val1", "val2"])
            self.assertEqual(rows[2], ["val3", "val4"])


if __name__ == "__main__":
    unittest.main()
