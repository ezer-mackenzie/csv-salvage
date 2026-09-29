from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from csv_salvage import (
    ConfigurationError,
    CorruptedFileError,
    InferenceError,
    open as cs_open,
    salvage_file,
    sniff,
)
from csv_salvage.validation import (
    validate_delimiter,
    validate_expected_columns,
    validate_input_path,
    validate_output_path,
    validate_quarantine_path,
    validate_quote_char,
)


class InputValidationTests(unittest.TestCase):
    def test_input_path_must_exist_and_be_file(self):
        with self.assertRaises(FileNotFoundError):
            validate_input_path("non_existent_file_xyz_123.csv")

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(CorruptedFileError):
                validate_input_path(tmpdir)

    def test_delimiter_validation(self):
        self.assertIsNone(validate_delimiter(None))
        self.assertEqual(validate_delimiter(","), ",")
        self.assertEqual(validate_delimiter(";"), ";")
        self.assertEqual(validate_delimiter("\t"), "\t")

        for invalid in ("ab", "", "   "):
            with self.subTest(invalid=invalid), self.assertRaises(ConfigurationError):
                validate_delimiter(invalid)

        for invalid_type in (123, True):
            with self.subTest(invalid=invalid_type), self.assertRaises(TypeError):
                validate_delimiter(invalid_type)  # type: ignore[arg-type]

    def test_quote_char_validation(self):
        self.assertEqual(validate_quote_char('"'), '"')
        self.assertEqual(validate_quote_char("'"), "'")

        for invalid in ('""', ""):
            with self.subTest(invalid=invalid), self.assertRaises(ConfigurationError):
                validate_quote_char(invalid)

        for invalid_type in (1, None, False):
            with self.subTest(invalid=invalid_type), self.assertRaises(TypeError):
                validate_quote_char(invalid_type)  # type: ignore[arg-type]

    def test_expected_columns_validation(self):
        self.assertIsNone(validate_expected_columns(None))
        self.assertEqual(validate_expected_columns(1), 1)
        self.assertEqual(validate_expected_columns(10), 10)

        for invalid in (0, -1, -100):
            with self.subTest(invalid=invalid), self.assertRaises(ConfigurationError):
                validate_expected_columns(invalid)

        with self.assertRaises(TypeError):
            validate_expected_columns("5")  # type: ignore[arg-type]

    def test_sniff_validation(self):
        with self.assertRaises(InferenceError):
            sniff("")

        with self.assertRaises(InferenceError):
            sniff("   \n\t  ")

        with self.assertRaises(AttributeError):
            sniff(123)  # type: ignore[arg-type]

    def test_salvage_file_validates_before_native_execution(self):
        with self.assertRaises(FileNotFoundError):
            salvage_file("missing_input.csv", "out.csv")

        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "sample.csv"
            sample_file.write_text("a,b\n1,2\n", encoding="utf-8")
            out_file = Path(tmpdir) / "out.csv"

            with self.assertRaises(ConfigurationError):
                salvage_file(sample_file, out_file, delimiter="invalid_delim")

            with self.assertRaises(ConfigurationError):
                salvage_file(sample_file, out_file, expected_columns=-5)

    def test_open_validates_before_native_execution(self):
        with self.assertRaises(FileNotFoundError):
            cs_open("missing_file.csv")

        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "sample.csv"
            sample_file.write_text("a,b\n1,2\n", encoding="utf-8")

            with self.assertRaises(ConfigurationError):
                cs_open(sample_file, quote_char="invalid_quote")


if __name__ == "__main__":
    unittest.main()
