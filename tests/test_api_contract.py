from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

import csv_salvage as cs


class PublicApiContractTests(unittest.TestCase):
    def test_public_exports_are_explicit(self):
        self.assertEqual(
            cs.__all__,
            [
                "ConfigurationError",
                "CorruptedFileError",
                "InferenceError",
                "SalvageError",
                "SalvageReader",
                "SalvageSummary",
                "__version__",
                "open",
                "read_polars",
                "read_pyarrow",
                "salvage_file",
                "sniff",
            ],
        )

    def test_supported_callable_parameter_names_and_defaults(self):
        signatures = {
            "salvage_file": (
                "input_path",
                "output_path",
                "quarantine_path",
                "delimiter",
                "quote_char",
                "fill_ragged_rows",
                "merge_overflow",
                "expected_columns",
                "repair_quotes",
            ),
            "open": (
                "file_path",
                "delimiter",
                "quote_char",
                "fill_ragged_rows",
                "merge_overflow",
                "expected_columns",
                "repair_quotes",
            ),
            "SalvageReader": (
                "file_path",
                "delimiter",
                "quote_char",
                "fill_ragged_rows",
                "merge_overflow",
                "expected_columns",
                "repair_quotes",
            ),
            "read_pyarrow": (
                "file_path",
                "column_names",
                "delimiter",
                "quote_char",
                "fill_ragged_rows",
                "merge_overflow",
                "expected_columns",
                "repair_quotes",
            ),
            "read_polars": (
                "file_path",
                "column_names",
                "delimiter",
                "quote_char",
                "fill_ragged_rows",
                "merge_overflow",
                "expected_columns",
                "repair_quotes",
            ),
        }
        for name, expected_parameters in signatures.items():
            with self.subTest(api=name):
                actual = inspect.signature(getattr(cs, name)).parameters
                self.assertEqual(tuple(actual), expected_parameters)

        for name in ("salvage_file", "open", "SalvageReader"):
            with self.subTest(api=name):
                parameters = inspect.signature(getattr(cs, name)).parameters
                self.assertIsNone(parameters["delimiter"].default)
                self.assertEqual(parameters["quote_char"].default, '"')
                self.assertIs(parameters["fill_ragged_rows"].default, True)
                self.assertIs(parameters["merge_overflow"].default, True)
                self.assertIsNone(parameters["expected_columns"].default)
                self.assertIs(parameters["repair_quotes"].default, True)

        for name in ("read_pyarrow", "read_polars"):
            with self.subTest(api=name):
                parameters = inspect.signature(getattr(cs, name)).parameters
                self.assertEqual(
                    parameters["column_names"].kind,
                    inspect.Parameter.KEYWORD_ONLY,
                )
                self.assertIsNone(parameters["column_names"].default)

    def test_error_and_summary_contract(self):
        self.assertTrue(issubclass(cs.ConfigurationError, cs.SalvageError))
        self.assertTrue(issubclass(cs.CorruptedFileError, cs.SalvageError))
        self.assertTrue(issubclass(cs.InferenceError, cs.SalvageError))
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "empty.csv"
            output = Path(tmpdir) / "clean.csv"
            source.write_bytes(b"")
            summary = cs.salvage_file(source, output)
            expected_fields = (
                "total_rows",
                "salvaged_rows",
                "repaired_rows",
                "quarantined_rows",
                "detected_delimiter",
                "inferred_columns",
            )
            for field in expected_fields:
                with self.subTest(field=field):
                    self.assertTrue(hasattr(summary, field))
            self.assertEqual(
                tuple(summary.to_dict()),
                expected_fields,
            )


if __name__ == "__main__":
    unittest.main()
