"""No DB is needed to test the expression sandbox."""

from decimal import Decimal

from django.test import SimpleTestCase

from vn_payroll.expression import InvalidFormula, evaluate


class DynamicPayrollFormulaTests(SimpleTestCase):
    def test_net_salary(self):
        self.assertEqual(
            evaluate(
                "gross - employee_insurance - pit - advance",
                {"gross": "30000000", "employee_insurance": "2100000", "pit": "1500000", "advance": "1000000"},
            ),
            Decimal("25400000"),
        )

    def test_overtime_formula_is_configurable(self):
        amount = evaluate(
            "base_hourly * overtime_hours * multiplier",
            {"base_hourly": "30000", "overtime_hours": "7.5", "multiplier": "1.5"},
        )
        self.assertEqual(amount, Decimal("337500"))

    def test_nonnegative_taxable_income(self):
        self.assertEqual(evaluate("max(0, gross - deduction)", {"gross": 100, "deduction": 150}), Decimal(0))

    def test_decimal_rounding(self):
        self.assertEqual(evaluate("10 / 4", {}, places=0), Decimal("3"))
        self.assertEqual(evaluate("10 / 4", {}, places=2), Decimal("2.50"))

    def test_rejects_unsafe_python(self):
        payloads = [
            "__import__('os').system('id')",
            "gross.__class__",
            "gross[0]",
            "[x for x in (1, 2)]",
            "2 ** 10000000",
            "round(gross)",
            "(lambda: 1)()",
            "globals()",
        ]
        for formula in payloads:
            with self.subTest(formula=formula):
                with self.assertRaises(InvalidFormula):
                    evaluate(formula, {"gross": "100"})

    def test_missing_variable_and_division_by_zero(self):
        with self.assertRaises(InvalidFormula):
            evaluate("gross - tax", {"gross": 500})
        with self.assertRaises(InvalidFormula):
            evaluate("gross / 0", {"gross": 500})

    def test_rejects_non_finite_or_boolean_input(self):
        for value in ("NaN", "Infinity", True):
            with self.subTest(value=value):
                with self.assertRaises(InvalidFormula):
                    evaluate("gross", {"gross": value})

    def test_rejects_overlong_and_deep_expressions(self):
        with self.assertRaises(InvalidFormula):
            evaluate("1+" * 600 + "1", {})
        with self.assertRaises(InvalidFormula):
            evaluate("1" + "+1" * 120, {})
