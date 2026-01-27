"""Report generation system with multiple format support.

This module provides an extensible reporter system for generating
validation reports in various formats (HTML, CSV, Markdown, JSON, JUnit).

## Architecture

The reporter system is built on these principles:
1. **Protocol-based typing** for flexible duck typing
2. **Backend-agnostic interfaces** for loose coupling with truthound
3. **Adapter pattern** for external reporter integration
4. **Factory pattern** for reporter instantiation
5. **Backward compatibility** with existing code

## Usage

### New Style (Recommended)

```python
from truthound_dashboard.core.reporters import (
    ReportData,
    ReporterConfig,
    get_reporter,
    generate_report_from_validation,
)

# From validation model
output = await generate_report_from_validation(
    validation,
    format="html",
    locale="ko",
)

# From ReportData (backend-agnostic)
data = ReportData.from_validation_model(validation)
reporter = get_reporter("json")
output = await reporter.generate(data)
```

### Legacy Style (Still Supported)

```python
from truthound_dashboard.core.reporters import generate_report

report = await generate_report(validation, format="html")
```

## Extension Points

1. Register custom reporters:
```python
from truthound_dashboard.core.reporters import register_reporter_factory

@register_reporter_factory("custom")
def create_custom_reporter(**kwargs):
    return MyCustomReporter(**kwargs)
```

2. Use truthound reporters directly:
```python
from truthound_dashboard.core.reporters.adapters import (
    TruthoundReporterAdapter,
    create_truthound_reporter,
)

reporter = create_truthound_reporter("json", locale="ko")
```
"""

# =============================================================================
# New Interface-based API (v2)
# =============================================================================

from .interfaces import (
    # Data classes
    ReportData,
    ReporterConfig,
    ReportOutput,
    ValidationIssueData,
    ValidationSummary,
    DataStatistics,
    # Enums
    ReportFormatType,
    ReportThemeType,
    # Protocols/Base classes
    ReporterProtocol,
    BaseReporter,
    ReporterAdapterProtocol,
    ReporterFactoryProtocol,
)

from .factory import (
    ReporterFactory,
    get_reporter_factory,
    reset_factory,
    register_reporter as register_reporter_factory,
    get_reporter as get_reporter_v2,
    get_available_formats as get_available_formats_v2,
    is_format_available,
    generate_report as generate_report_v2,
    generate_report_from_validation,
)

from .adapters import (
    TruthoundReporterAdapter,
    ValidationModelAdapter,
    create_truthound_reporter,
    create_ci_reporter,
    is_truthound_available,
    get_truthound_formats,
    is_ci_environment,
    get_detected_ci_platform,
)

from .compat import (
    legacy_generate_report,
    convert_validation_to_report_data,
    LegacyReportResult,
)

# =============================================================================
# Legacy API (v1) - Backward Compatibility
# =============================================================================

from .base import (
    Reporter,
    ReportFormat,
    ReportMetadata,
    ReportResult,
    ReportTheme,
)
from .csv_reporter import CSVReporter
from .html_reporter import HTMLReporter
from .json_reporter import JSONReporter
from .markdown_reporter import MarkdownReporter
from .registry import (
    ReporterRegistry,
    generate_report,
    get_available_formats,
    get_reporter,
    register_reporter,
)

# =============================================================================
# Built-in Reporters
# =============================================================================

from .builtin import (
    BuiltinCSVReporter,
    BuiltinHTMLReporter,
    BuiltinJSONReporter,
    BuiltinJUnitReporter,
    BuiltinMarkdownReporter,
)

__all__ = [
    # =========================================================================
    # New Interface-based API (v2) - Recommended
    # =========================================================================
    # Data classes
    "ReportData",
    "ReporterConfig",
    "ReportOutput",
    "ValidationIssueData",
    "ValidationSummary",
    "DataStatistics",
    # Enums
    "ReportFormatType",
    "ReportThemeType",
    # Protocols/Base classes
    "ReporterProtocol",
    "BaseReporter",
    "ReporterAdapterProtocol",
    "ReporterFactoryProtocol",
    # Factory
    "ReporterFactory",
    "get_reporter_factory",
    "reset_factory",
    "register_reporter_factory",
    "get_reporter_v2",
    "get_available_formats_v2",
    "is_format_available",
    "generate_report_v2",
    "generate_report_from_validation",
    # Adapters
    "TruthoundReporterAdapter",
    "ValidationModelAdapter",
    "create_truthound_reporter",
    "create_ci_reporter",
    "is_truthound_available",
    "get_truthound_formats",
    "is_ci_environment",
    "get_detected_ci_platform",
    # Compatibility
    "legacy_generate_report",
    "convert_validation_to_report_data",
    "LegacyReportResult",
    # Built-in reporters
    "BuiltinCSVReporter",
    "BuiltinHTMLReporter",
    "BuiltinJSONReporter",
    "BuiltinJUnitReporter",
    "BuiltinMarkdownReporter",
    # =========================================================================
    # Legacy API (v1) - Backward Compatibility
    # =========================================================================
    # Base classes
    "Reporter",
    "ReportFormat",
    "ReportMetadata",
    "ReportResult",
    "ReportTheme",
    # Legacy Implementations
    "CSVReporter",
    "HTMLReporter",
    "JSONReporter",
    "MarkdownReporter",
    # Legacy Registry
    "ReporterRegistry",
    "generate_report",
    "get_available_formats",
    "get_reporter",
    "register_reporter",
]
