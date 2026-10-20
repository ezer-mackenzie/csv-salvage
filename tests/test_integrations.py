from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import csv_salvage as cs
from csv_salvage.errors import ConfigurationError


class OptionalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.input_path = Path(self.temporary.name) / "broken.csv"
        self.input_path.write_text(
            'id,name,role\n1,Alice,Engineer\n2,"15" Monitor"\n',
            encoding="utf-8",
        )

    @unittest.skipUnless(
        importlib.util.find_spec("pyarrow"), "PyArrow extra not installed"
    )
    def test_read_pyarrow_returns_string_table_with_repaired_rows(self):
        table = cs.read_pyarrow(self.input_path, column_names=["id", "name", "role"])

        self.assertEqual(table.column_names, ["id", "name", "role"])
        self.assertEqual(table.num_rows, 3)
        self.assertEqual(str(table.schema.field("name").type), "string")
        self.assertEqual(table.column("name").to_pylist()[-1], '15" Monitor')
        self.assertEqual(table.column("role").to_pylist()[-1], "")

    @unittest.skipUnless(
        importlib.util.find_spec("polars"), "Polars extra not installed"
    )
    def test_read_polars_returns_string_frame_with_repaired_rows(self):
        import polars as pl

        frame = cs.read_polars(self.input_path, column_names=["id", "name", "role"])

        self.assertEqual(frame.columns, ["id", "name", "role"])
        self.assertEqual(frame.shape, (3, 3))
        self.assertEqual(frame.schema["name"], pl.String)
        self.assertEqual(frame["name"].to_list()[-1], '15" Monitor')
        self.assertEqual(frame["role"].to_list()[-1], "")

    @unittest.skipUnless(
        importlib.util.find_spec("pyarrow"), "PyArrow extra not installed"
    )
    def test_empty_file_can_keep_explicit_arrow_schema(self):
        self.input_path.write_text("", encoding="utf-8")

        table = cs.read_pyarrow(
            self.input_path,
            column_names=["id", "name"],
            expected_columns=2,
        )

        self.assertEqual(table.column_names, ["id", "name"])
        self.assertEqual(table.num_rows, 0)

    @unittest.skipUnless(
        importlib.util.find_spec("pyarrow"), "PyArrow extra not installed"
    )
    def test_column_name_count_must_match_expected_columns(self):
        with self.assertRaises(ConfigurationError):
            cs.read_pyarrow(
                self.input_path,
                column_names=["id", "name"],
                expected_columns=3,
            )

    @unittest.skipUnless(
        importlib.util.find_spec("pyarrow"), "PyArrow extra not installed"
    )
    def test_column_names_do_not_change_inferred_column_count(self):
        with self.assertRaisesRegex(ConfigurationError, "inferred column count"):
            cs.read_pyarrow(self.input_path, column_names=["id", "name"])

    @patch("csv_salvage.integrations.import_module", side_effect=ModuleNotFoundError)
    def test_missing_pyarrow_extra_has_install_guidance(self, _import_module):
        with self.assertRaisesRegex(ImportError, r"csv-salvage\[arrow\]"):
            cs.read_pyarrow(self.input_path)

    @patch("csv_salvage.integrations.import_module", side_effect=ModuleNotFoundError)
    def test_missing_polars_extra_has_install_guidance(self, _import_module):
        with self.assertRaisesRegex(ImportError, r"csv-salvage\[polars\]"):
            cs.read_polars(self.input_path)


if __name__ == "__main__":
    unittest.main()
