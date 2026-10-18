"""Sandboxed Decimal expression evaluation for business-configured payroll rules.

No Python eval/exec, attribute access, indexing, comprehensions, imports or
arbitrary calls. The engine consumes explicitly supplied numeric variables only.
This module is purely computational; it does not assert statutory compliance.
"""

import ast
import re
from decimal import Decimal, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_UP


class InvalidFormula(ValueError):
    """Rejected expression or unsupported input."""


MAX_FORMULA_LENGTH = 1000
MAX_AST_NODES = 100
MAX_DEPTH = 20


def _decimal(value):
    if isinstance(value, bool):
        raise InvalidFormula("Boolean values are not amounts")
    if not isinstance(value, (int, str, Decimal)):
        raise InvalidFormula("Input must be Decimal, integer or decimal string")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InvalidFormula("Invalid decimal input") from exc
    if not result.is_finite() or (result and abs(result.adjusted()) > 18):
        raise InvalidFormula("Amount out of supported bounds")
    return result


def evaluate(expression, variables, *, places=0):
    """Evaluate a single arithmetic formula and return an auditable VND Decimal.

    Examples:
      gross - employee_insurance - personal_income_tax
      max(0, taxable_income - personal_deduction)
      base_pay * overtime_hours * overtime_multiplier

    All variables must be passed explicitly. Division by zero, exponentiation,
    function calls other than min/max/abs, and unsafe syntax are rejected.
    """
    if not isinstance(expression, str) or not expression.strip() or len(expression) > MAX_FORMULA_LENGTH:
        raise InvalidFormula("Formula is missing or too long")
    if not isinstance(variables, dict) or len(variables) > 100:
        raise InvalidFormula("Invalid variable mapping")
    env = {}
    for name, value in variables.items():
        if not isinstance(name, str) or not name.isidentifier() or name.startswith("_"):
            raise InvalidFormula("Invalid variable name")
        env[name] = _decimal(value)
    if isinstance(places, bool) or not isinstance(places, int) or places < 0 or places > 6:
        raise InvalidFormula("Decimal places must be between 0 and 6")
    try:
        parsed = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise InvalidFormula("Invalid expression syntax") from exc
    if sum(1 for _ in ast.walk(parsed)) > MAX_AST_NODES:
        raise InvalidFormula("Formula is too complex")

    def walk(node, depth=0):
        if depth > MAX_DEPTH:
            raise InvalidFormula("Formula nesting limit exceeded")
        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                # Python AST converts 0.105 to binary float. Parse its exact
                # source text instead so payroll never inherits float error.
                source = ast.get_source_segment(expression, node)
                if source is None or not re.fullmatch(
                    r"(?:[0-9][0-9_]*)(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?|\.[0-9_]+(?:[eE][+-]?[0-9_]+)?",
                    source,
                ):
                    raise InvalidFormula("Invalid numeric literal")
                return _decimal(source.replace("_", ""))
            raise InvalidFormula("Only numeric literals are allowed")
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise InvalidFormula("Unknown variable: " + node.id)
            return env[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = walk(node.operand, depth + 1)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = walk(node.left, depth + 1), walk(node.right, depth + 1)
            try:
                if isinstance(node.op, ast.Add):
                    result = a + b
                elif isinstance(node.op, ast.Sub):
                    result = a - b
                elif isinstance(node.op, ast.Mult):
                    result = a * b
                else:
                    if not b:
                        raise InvalidFormula("Division by zero")
                    result = a / b
            except (InvalidOperation, DivisionByZero, Overflow, OverflowError) as exc:
                raise InvalidFormula("Arithmetic error") from exc
            return _decimal(result)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.keywords or node.func.id not in ("min", "max", "abs"):
                raise InvalidFormula("Function is not allowed")
            args = [walk(arg, depth + 1) for arg in node.args]
            if node.func.id == "abs" and len(args) == 1:
                return abs(args[0])
            if node.func.id in ("min", "max") and 1 <= len(args) <= 10:
                return min(args) if node.func.id == "min" else max(args)
            raise InvalidFormula("Invalid function arguments")
        raise InvalidFormula("Unsupported formula operation")

    result = _decimal(walk(parsed))
    quantum = Decimal("1").scaleb(-places)
    try:
        return result.quantize(quantum, rounding=ROUND_HALF_UP)
    except (InvalidOperation, Overflow) as exc:
        raise InvalidFormula("Rounding failed") from exc
