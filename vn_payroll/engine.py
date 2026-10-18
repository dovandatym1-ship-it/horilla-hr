"""Safe, deterministic, Decimal-based expression evaluation for Vietnam payroll.

No eval(), exec(), arbitrary Python functions, object access or comprehensions.
All inputs are explicit numeric values. This module does NOT represent an
approved statutory formula by itself.
"""

import ast
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MAX_EXPRESSION_LENGTH = 700
MAX_AST_NODES = 100
MAX_DEPTH = 20
MAX_ABS_VALUE = Decimal("1000000000000000")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class FormulaError(ValueError):
    """Formula is invalid, unsafe or cannot be evaluated."""


def as_decimal(value):
    """Convert trusted numeric inputs without binary floating point arithmetic."""
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise FormulaError("Only Decimal, integer or numeric string inputs are allowed.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FormulaError("Invalid decimal value.") from exc
    if not number.is_finite() or abs(number) > MAX_ABS_VALUE:
        raise FormulaError("Value must be finite and within the allowed range.")
    return number


def _number(result):
    if isinstance(result, bool) or not isinstance(result, Decimal):
        raise FormulaError("A numeric value is required.")
    if not result.is_finite() or abs(result) > MAX_ABS_VALUE:
        raise FormulaError("Formula result is out of bounds.")
    return result


def _calculate(node, variables, depth):
    if depth > MAX_DEPTH:
        raise FormulaError("Formula nesting is too deep.")
    call = lambda child: _calculate(child, variables, depth + 1)
    if isinstance(node, ast.Constant):
        if type(node.value) is bool:
            return node.value
        if type(node.value) in (int, float):
            return as_decimal(str(node.value))
        raise FormulaError("Only numeric and boolean constants are allowed.")
    if isinstance(node, ast.Name):
        if not NAME_PATTERN.fullmatch(node.id) or node.id not in variables:
            raise FormulaError("Unknown variable: " + node.id)
        return variables[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        x = _number(call(node.operand))
        return _number(x if isinstance(node.op, ast.UAdd) else -x)
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
    ):
        a, b = _number(call(node.left)), _number(call(node.right))
        try:
            if isinstance(node.op, ast.Add):
                value = a + b
            elif isinstance(node.op, ast.Sub):
                value = a - b
            elif isinstance(node.op, ast.Mult):
                value = a * b
            else:
                if not b:
                    raise FormulaError("Division by zero.")
                value = a / b
        except (InvalidOperation, OverflowError) as exc:
            raise FormulaError("Invalid arithmetic operation.") from exc
        return _number(value)
    if isinstance(node, ast.Compare):
        left = _number(call(node.left))
        for op, expr in zip(node.ops, node.comparators):
            right = _number(call(expr))
            if isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            elif isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            else:
                raise FormulaError("Unsupported comparison.")
            if not ok:
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        # Short circuit and require actual boolean conditions.
        for item in node.values:
            flag = call(item)
            if type(flag) is not bool:
                raise FormulaError("Boolean operators require comparisons.")
            if isinstance(node.op, ast.And) and not flag:
                return False
            if isinstance(node.op, ast.Or) and flag:
                return True
        return isinstance(node.op, ast.And)
    if isinstance(node, ast.IfExp):
        condition = call(node.test)
        if type(condition) is not bool:
            raise FormulaError("Conditional expression requires a comparison.")
        return call(node.body if condition else node.orelse)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.keywords:
            raise FormulaError("Only approved positional functions are allowed.")
        name = node.func.id
        if name not in {"min", "max", "abs", "round_vnd"}:
            raise FormulaError("Function is not permitted: " + name)
        args = [_number(call(arg)) for arg in node.args]
        if name in {"min", "max"} and 1 <= len(args) <= 10:
            return _number(min(args) if name == "min" else max(args))
        if name == "abs" and len(args) == 1:
            return _number(abs(args[0]))
        if name == "round_vnd" and len(args) == 1:
            return _number(args[0].quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        raise FormulaError("Invalid function arguments.")
    raise FormulaError("Unsupported or unsafe formula syntax.")


# Allowed parse nodes for static validation of formulas at save time.
_ALLOWED_NODES = (
    ast.Expression, ast.Constant, ast.Name, ast.Load, ast.UnaryOp,
    ast.UAdd, ast.USub, ast.BinOp, ast.Add, ast.Sub, ast.Mult,
    ast.Div, ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Eq, ast.NotEq, ast.BoolOp, ast.And, ast.Or, ast.IfExp,
    ast.Call,
)


def validate_syntax(expression):
    """Validate expression structure without executing it or binding inputs."""
    if not isinstance(expression, str) or not 1 <= len(expression) <= MAX_EXPRESSION_LENGTH:
        raise FormulaError("Formula must be between 1 and 700 characters.")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise FormulaError("Formula syntax is invalid.") from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > MAX_AST_NODES:
        raise FormulaError("Formula is too complex.")
    for node in nodes:
        if not isinstance(node, _ALLOWED_NODES):
            raise FormulaError("Formula syntax is not permitted.")
        if isinstance(node, ast.Name) and not NAME_PATTERN.fullmatch(node.id):
            raise FormulaError("Invalid name in expression.")
        if isinstance(node, ast.Constant):
            if type(node.value) not in (bool, int, float):
                raise FormulaError("Only numeric/boolean literals are allowed.")
            if type(node.value) is not bool:
                as_decimal(str(node.value))
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in {
                "min", "max", "abs", "round_vnd"
            } or node.keywords:
                raise FormulaError("Unapproved function call.")
            nargs = len(node.args)
            if not (
                (node.func.id in {"min", "max"} and 1 <= nargs <= 10)
                or (node.func.id in {"abs", "round_vnd"} and nargs == 1)
            ):
                raise FormulaError("Invalid function argument count.")
    return tree


def evaluate(expression, variables):
    """Evaluate one formula from explicitly supplied, strictly numeric values.

    Use a ternary conditional for rate bands, e.g.
      'min(taxable, ceiling) * rate if taxable > 0 else 0'
    Rates and ceilings must be supplied via approved rules/inputs.
    """
    tree = validate_syntax(expression)
    if not isinstance(variables, dict) or len(variables) > 80:
        raise FormulaError("Invalid formula inputs.")
    clean = {}
    for key, value in variables.items():
        if not isinstance(key, str) or not NAME_PATTERN.fullmatch(key):
            raise FormulaError("Invalid variable name.")
        clean[key] = as_decimal(value)
    try:
        return _number(_calculate(tree.body, clean, 0))
    except (InvalidOperation, OverflowError, RecursionError) as exc:
        raise FormulaError("Unable to evaluate formula.") from exc


def calculate_lines(rules, inputs):
    """Run ordered rules; later lines can reference the earlier output codes.

    rules: iterable of {code, category, expression}; returns (lines, context).
    This is for preview/approved adapter integration, not auto-writing Payslip.
    """
    ctx = {k: as_decimal(v) for k, v in inputs.items()}
    lines = []
    seen = set(ctx)
    for item in rules:
        code = item["code"]
        if not isinstance(code, str) or not NAME_PATTERN.fullmatch(code):
            raise FormulaError("Invalid rule code.")
        if code in seen:
            raise FormulaError("Rule code conflicts with an input or prior rule.")
        amount = evaluate(item["expression"], ctx)
        lines.append({"code": code, "category": item["category"], "amount": amount})
        ctx[code] = amount
        seen.add(code)
    return lines, ctx
