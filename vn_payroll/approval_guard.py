"""Internal capability flag for approval transitions in model.save().

Always call via the permission-checked service layer, never from views or admin
directly. The guard is not an authorization system by itself; the service is.
"""

from contextlib import contextmanager
from contextvars import ContextVar

_approved_transition = ContextVar("vn_formula_approval_transition", default=False)


@contextmanager
def allow_approval_transition():
    token = _approved_transition.set(True)
    try:
        yield
    finally:
        _approved_transition.reset(token)


def approval_transition_enabled():
    return _approved_transition.get()
