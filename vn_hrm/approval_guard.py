"""Guard all in-process verification and amendment approvals.

Only permission-checked services should enter this context. This does not
replace the service's actor/company authorization.
"""

from contextlib import contextmanager
from contextvars import ContextVar

_transition = ContextVar("vn_hrm_approved_transition", default=False)


@contextmanager
def allow_hr_approval():
    token = _transition.set(True)
    try:
        yield
    finally:
        _transition.reset(token)


def hr_approval_enabled():
    return _transition.get()
