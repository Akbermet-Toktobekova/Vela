"""Unit tests for CSV formula injection protection (vela.csv_safe)."""

from datetime import date
from decimal import Decimal
import io
from pathlib import Path
import sys
import unittest

api_root = Path(__file__).resolve().parents[1]
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))

from vela.csv_safe import escape_cell, escape_row, escape_table, format_safe_csv, is_pure_number


class TestCsvSafe(unittest.TestCase):
    """Verifies formula injection mitigation and preservation of financial numbers."""

    def test_all_six_dangerous_prefixes_are_escaped(self):
        """Cells starting with '=', '+', '-', '@', '\t', '\r' with formulas are escaped."""
        dangerous_cases = [
            ("=SUM(A1:A10)", "'=SUM(A1:A10)"),
            ("=1+1", "'=1+1"),
            ("=cmd|' /C calc'!A0", "'=cmd|' /C calc'!A0"),
            ("+cmd|' /C calc'!A0", "'+cmd|' /C calc'!A0"),
            ("+A1", "'+A1"),
            ("-2+3", "'-2+3"),
            ("-cmd|'/C calc'!A0", "'-cmd|'/C calc'!A0"),
            ("@SUM(B1:B5)", "'@SUM(B1:B5)"),
            ("@calc", "'@calc"),
            ("\t=1+1", "'\t=1+1"),
            ("\tcmd", "'\tcmd"),
            ("\r=1+1", "'\r=1+1"),
            ("\rcmd", "'\rcmd"),
        ]
        for raw, expected in dangerous_cases:
            with self.subTest(raw=raw):
                self.assertEqual(escape_cell(raw), expected)

    def test_pure_negative_and_positive_numbers_preserved(self):
        """Numbers (int, float, numeric strings) must NOT be prepended with an apostrophe."""
        number_cases = [
            # Integers
            (-150, "-150"),
            (-1, "-1"),
            (0, "0"),
            (100, "100"),
            (-100000, "-100000"),
            # Floats
            (-12.50, "-12.5"),
            (-0.99, "-0.99"),
            (42.0, "42.0"),
            # Numeric strings (common in statement amounts)
            ("-150", "-150"),
            ("-12.50", "-12.50"),
            ("-12,50", "-12,50"),  # European decimal comma
            ("+100", "+100"),
            ("+100.50", "+100.50"),
            ("0", "0"),
            ("42", "42"),
            ("-0", "-0"),
            ("-0.01", "-0.01"),
        ]
        for val, expected in number_cases:
            with self.subTest(val=val):
                self.assertEqual(escape_cell(val), expected)
                self.assertTrue(is_pure_number(val))

    def test_arithmetic_or_command_strings_with_plus_or_minus_are_escaped(self):
        """Expressions starting with + or - that are not pure numbers must be escaped."""
        tricky_expressions = [
            ("-2+3", "'-2+3"),
            ("-1*4", "'-1*4"),
            ("+1-2", "'+1-2"),
            ("-1.2.3", "'-1.2.3"),
            ("- 5", "'- 5"),  # space between sign and number can trigger formulas
            ("+ 10", "'+ 10"),
            ("-1;DROP TABLE", "'-1;DROP TABLE"),
            ("-payment for utilities", "'-payment for utilities"),
            ("+bonus from employer", "'+bonus from employer"),
        ]
        for raw, expected in tricky_expressions:
            with self.subTest(raw=raw):
                self.assertEqual(escape_cell(raw), expected)
                self.assertFalse(is_pure_number(raw))

    def test_ordinary_strings_and_dates_untouched(self):
        """Benign text, categories, dates, and None are passed through safely."""
        self.assertEqual(escape_cell("Rent payment"), "Rent payment")
        self.assertEqual(escape_cell("REWE Markt"), "REWE Markt")
        self.assertEqual(escape_cell("Salary October"), "Salary October")
        self.assertEqual(escape_cell("Netflix Abo"), "Netflix Abo")
        self.assertEqual(escape_cell(date(2026, 10, 24)), "2026-10-24")
        self.assertEqual(escape_cell(None), "")
        self.assertEqual(escape_cell(""), "")
        self.assertEqual(escape_cell(True), "True")
        self.assertEqual(escape_cell(False), "False")

    def test_leading_whitespace_formula_injection(self):
        """Formulas with leading whitespace (e.g. ' =cmd') are escaped."""
        self.assertEqual(escape_cell(" =SUM(1)"), "' =SUM(1)")
        self.assertEqual(escape_cell("   @calc"), "'   @calc")

    def test_escape_row_and_table(self):
        """Row and table escape functions apply escape_cell to every column."""
        header = ["Date", "Description", "Amount", "Category"]
        row1 = ["2026-10-24", "Salary", "+2500.00", "income"]
        row2 = ["2026-10-25", "=cmd|' /C calc'!A0", "-45.00", "shopping"]
        row3 = ["2026-10-26", "@special discount", "-12.50", "other"]

        escaped_table = escape_table([header, row1, row2, row3])

        self.assertEqual(escaped_table[0], header)
        self.assertEqual(escaped_table[1], ["2026-10-24", "Salary", "+2500.00", "income"])
        self.assertEqual(escaped_table[2], ["2026-10-25", "'=cmd|' /C calc'!A0", "-45.00", "shopping"])
        self.assertEqual(escaped_table[3], ["2026-10-26", "'@special discount", "-12.50", "other"])

    def test_format_safe_csv_output(self):
        """format_safe_csv produces RFC 4180 CSV with escaped formula injections."""
        table = [
            ["Date", "Merchant", "Amount"],
            ["2026-10-20", "=SUM(A1)", -150.0],
            ["2026-10-21", "+cmd|calc", "-12.50"],
            ["2026-10-22", "Ordinary Coffee", -4.50],
        ]
        csv_out = format_safe_csv(table)

        lines = csv_out.splitlines()
        self.assertEqual(lines[0], "Date,Merchant,Amount")
        self.assertEqual(lines[1], "2026-10-20,'=SUM(A1),-150.0")
        self.assertEqual(lines[2], "2026-10-21,'+cmd|calc,-12.50")
        self.assertEqual(lines[3], "2026-10-22,Ordinary Coffee,-4.5")


if __name__ == "__main__":
    unittest.main()
