"""Pure safe-rule-engine tests: no DB and no approved tax rates required."""

from decimal import Decimal

from django.test import SimpleTestCase

from vn_payroll.engine import FormulaError, calculate_lines, evaluate


class FormulaEngineTests(SimpleTestCase):
    def test_decimal_salary_proration_and_rounding(self):
        value = evaluate(
            "round_vnd(salary * paid_days / standard_days)",
            {"salary": "12600000", "paid_days": "19", "standard_days": 22},
        )
        self.assertEqual(value, Decimal("10881818"))

    def test_dynamic_rates_and_brackets(self):
        context = {"taxable": "35000000", "b1": "10000000",
                   "b2": "30000000", "r1": "0.05",
                   "r2": "0.10", "r3": "0.20"}
        formula = ("min(taxable, b1) * r1 + "
                   "max(min(taxable - b1, b2 - b1), 0) * r2 + "
                   "max(taxable - b2, 0) * r3")
        self.assertEqual(evaluate(formula, context), Decimal("3500000"))
        context["r3"] = "0.18"
        self.assertEqual(evaluate(formula, context), Decimal("3400000"))

    def test_ordered_categories_and_refs(self):
        rules = [
            {"code": "base", "category": "earning", "expression": "salary"},
            {"code": "ot", "category": "earning", "expression": "ot_hours * hourly_rate"},
            {"code": "gross", "category": "subtotal", "expression": "base + ot"},
            {"code": "insurance", "category": "deduction", "expression": "gross * insurance_rate"},
            {"code": "net", "category": "net", "expression": "gross - insurance"},
        ]
        lines, ctx = calculate_lines(rules, {"salary": "10000000", "ot_hours": 2, "hourly_rate": "50000", "insurance_rate": "0.1"})
        self.assertEqual([line["code"] for line in lines], ["base", "ot", "gross", "insurance", "net"])
        self.assertEqual(ctx["net"], Decimal("9090000"))

    def test_conditions(self):
        expr = "salary * rate if salary > 0 and rate > 0 else 0"
        self.assertEqual(evaluate(expr, {"salary": "20", "rate": "0.05"}), Decimal("1"))
        self.assertEqual(evaluate(expr, {"salary": "0", "rate": "0.05"}), Decimal("0"))

    def test_forbidden_code_and_unsafe_operations(self):
        for bad in (
            "__import__('os').system('id')",
            "salary.__class__", "salary[0]", "[1, 2, 3]",
            "1 ** 1000000", "(lambda x: x)(salary)",
            "open('/etc/passwd')", "str(salary)",
            "salary // 2", "sum([1,2])",
            "'hello'", "salary and 1",
        ):
            with self.subTest(formula=bad), self.assertRaises(FormulaError):
                evaluate(bad, {"salary": 100})

    def test_invalid_numbers_and_duplicate_rules(self):
        for value in ("nan", "infinity", "1e9999", "-1e9999", True, 1.1):
            with self.subTest(value=value), self.assertRaises(FormulaError):
                evaluate("salary", {"salary": value})
        with self.assertRaises(FormulaError):
            evaluate("1 / 0", {})
        with self.assertRaises(FormulaError):
            calculate_lines([{"code": "salary", "category": "earning", "expression": "1"}], {"salary": 2})

    def test_unknown_keys_cannot_be_silently_substituted(self):
        with self.assertRaises(FormulaError):
            evaluate("gross - insurance", {"gross": 100})
