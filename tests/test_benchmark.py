from __future__ import annotations

import csv
import io
import unittest

from tools.benchmark import _regex_cleaned_lines


class BenchmarkTests(unittest.TestCase):
    def test_regex_baseline_repairs_the_documented_single_line_case(self):
        source = io.StringIO(
            'id,name,description\n1,Widget,"Description with "orphan" quote"\n'
        )

        rows = list(csv.reader(_regex_cleaned_lines(source)))

        self.assertEqual(
            rows,
            [
                ["id", "name", "description"],
                ["1", "Widget", 'Description with "orphan" quote'],
            ],
        )


if __name__ == "__main__":
    unittest.main()
