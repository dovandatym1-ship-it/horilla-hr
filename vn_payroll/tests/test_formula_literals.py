from decimal import Decimal

from django.test import SimpleTestCase

from vn_payroll.expression import InvalidFormula, evaluate, validate_expression


class FormulaLiteralTests(SimpleTestCase):
    def test_exact_decimal_literal(self):
        self.assertEqual(evaluate("gross * 0.105", {"gross": "10000000"}), Decimal("1050000"))

    def test_fractional_overtime_multiplier(self):
        self.assertEqual(
            evaluate("rate * hours * 1.5", {"rate": "30000", "hours": "7.5"}),
            Decimal("337500"),
        )

    def test_validate_without_fake_values(self):
        self.assertTrue(validate_expression("gross / (days - 1)", ["gross", "days"]))

    def test_unknown_variable_rejected_during_validation(self):
        with self.assertRaises(InvalidFormula):
            validate_expression("gross - insurance", ["gross"])

    def test_expression_remains_sandboxed(self):
        for expr in ('(1).__class__', '[1]', "pow(2, 30000)", '2 ** 10'):
            with self.subTest(expr=expr):
                with self.assertRaises(InvalidFormula):
                    validate_expression(expr, [])
