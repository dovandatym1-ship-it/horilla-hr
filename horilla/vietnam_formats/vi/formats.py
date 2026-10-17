"""Vietnamese display and accepted input formats for Django templates/forms.

Horilla's per-company date/time preferences, where explicitly configured,
take precedence in those screens. This is the Django-level fallback.
"""

DATE_FORMAT = "d/m/Y"
SHORT_DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"
TIME_FORMAT = "H:i"
YEAR_MONTH_FORMAT = "m/Y"
MONTH_DAY_FORMAT = "d/m"
DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]
DATETIME_INPUT_FORMATS = [
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
]
TIME_INPUT_FORMATS = ["%H:%M", "%H:%M:%S"]
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "."
NUMBER_GROUPING = 3
FIRST_DAY_OF_WEEK = 1  # Monday
