"""Built-in reporter implementations.

These reporters provide dashboard-native report generation
without depending on external libraries.

They serve as fallbacks when truthound reporters are not available
and can be used independently.
"""

from .csv_reporter import BuiltinCSVReporter
from .html_reporter import BuiltinHTMLReporter
from .json_reporter import BuiltinJSONReporter
from .junit_reporter import BuiltinJUnitReporter
from .markdown_reporter import BuiltinMarkdownReporter

__all__ = [
    "BuiltinCSVReporter",
    "BuiltinHTMLReporter",
    "BuiltinJSONReporter",
    "BuiltinJUnitReporter",
    "BuiltinMarkdownReporter",
]
