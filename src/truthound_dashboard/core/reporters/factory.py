"""Reporter factory with flexible backend selection.

This module provides a unified factory for creating reporters from
various backends (dashboard-native, truthound, custom).

The factory supports:
1. Multiple backend priority (truthound first, then fallback)
2. Dynamic reporter registration
3. Lazy loading of backends
4. Configuration-based reporter creation

Example:
    from truthound_dashboard.core.reporters.factory import (
        get_reporter_factory,
        ReporterFactory,
    )

    factory = get_reporter_factory()

    # Get reporter by format
    reporter = factory.get_reporter("json")

    # Generate report
    output = await reporter.generate(data)

    # Check available formats
    formats = factory.get_available_formats()
"""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from .interfaces import (
    BaseReporter,
    ReportData,
    ReporterConfig,
    ReporterProtocol,
    ReportFormatType,
    ReportOutput,
    ReportThemeType,
)

logger = logging.getLogger(__name__)

ReporterT = TypeVar("ReporterT", bound=ReporterProtocol)


class ReporterFactory:
    """Factory for creating reporter instances.

    This factory supports multiple backends with priority ordering:
    1. Explicitly registered reporters (highest priority)
    2. Truthound reporters (if available)
    3. Dashboard built-in reporters (fallback)

    The factory uses lazy loading to avoid importing unnecessary
    dependencies until they're actually needed.

    Attributes:
        backends: List of backend names in priority order.
    """

    def __init__(
        self,
        use_truthound: bool = True,
        default_locale: str = "en",
    ) -> None:
        """Initialize factory.

        Args:
            use_truthound: Whether to try truthound reporters first.
            default_locale: Default locale for i18n.
        """
        self._use_truthound = use_truthound
        self._default_locale = default_locale

        # Registered reporter classes (format -> class)
        self._registered: dict[ReportFormatType, type[ReporterProtocol]] = {}

        # Registered reporter instances (format -> instance)
        self._instances: dict[str, ReporterProtocol] = {}

        # Factory functions for custom reporters
        self._factories: dict[ReportFormatType, Callable[..., ReporterProtocol]] = {}

        # Cached truthound availability
        self._truthound_available: bool | None = None

    @property
    def backends(self) -> list[str]:
        """Get list of backend names in priority order."""
        backends = ["registered"]
        if self._use_truthound and self._is_truthound_available():
            backends.append("truthound")
        backends.append("builtin")
        return backends

    def _is_truthound_available(self) -> bool:
        """Check if truthound is available (cached)."""
        if self._truthound_available is None:
            from .adapters import is_truthound_available

            self._truthound_available = is_truthound_available()
        return self._truthound_available

    def register(
        self,
        format_type: ReportFormatType | str,
        reporter_class: type[ReporterProtocol],
    ) -> None:
        """Register a reporter class for a format.

        Registered reporters have highest priority and will be used
        instead of truthound or built-in reporters.

        Args:
            format_type: Report format to register for.
            reporter_class: Reporter class to use.
        """
        if isinstance(format_type, str):
            format_type = ReportFormatType.from_string(format_type)

        self._registered[format_type] = reporter_class
        logger.debug(f"Registered reporter {reporter_class.__name__} for {format_type.value}")

    def register_factory(
        self,
        format_type: ReportFormatType | str,
        factory_func: Callable[..., ReporterProtocol],
    ) -> None:
        """Register a factory function for creating reporters.

        This is useful for reporters that need complex initialization
        or dependency injection.

        Args:
            format_type: Report format.
            factory_func: Factory function that returns a reporter.
        """
        if isinstance(format_type, str):
            format_type = ReportFormatType.from_string(format_type)

        self._factories[format_type] = factory_func
        logger.debug(f"Registered factory for {format_type.value}")

    def register_instance(
        self,
        format_name: str,
        reporter: ReporterProtocol,
    ) -> None:
        """Register a specific reporter instance.

        This is useful for sharing pre-configured reporter instances.

        Args:
            format_name: Format name (used as key).
            reporter: Reporter instance.
        """
        self._instances[format_name.lower()] = reporter
        logger.debug(f"Registered instance for {format_name}")

    def unregister(self, format_type: ReportFormatType | str) -> None:
        """Unregister a reporter for a format.

        Args:
            format_type: Format to unregister.
        """
        if isinstance(format_type, str):
            format_type = ReportFormatType.from_string(format_type)

        self._registered.pop(format_type, None)
        self._factories.pop(format_type, None)
        self._instances.pop(format_type.value, None)

    def get_reporter(
        self,
        format: ReportFormatType | str,
        config: ReporterConfig | None = None,
        locale: str | None = None,
        prefer_truthound: bool = False,
        **kwargs: Any,
    ) -> ReporterProtocol:
        """Get a reporter for the specified format.

        The factory tries backends in this order:
        1. Registered instance (exact match by format name)
        2. Registered factory function
        3. Registered class
        4. Built-in dashboard reporter (default)
        5. Truthound reporter (if prefer_truthound=True or format not in builtin)

        Note: By default, built-in reporters are preferred because they work
        reliably with our ReportData format. Truthound reporters require
        a real truthound Report/ValidationResult object for full compatibility.

        Args:
            format: Report format (enum or string).
            config: Optional configuration.
            locale: Locale override (uses default if not specified).
            prefer_truthound: If True, try truthound reporters before built-in.
            **kwargs: Additional arguments passed to reporter constructor.

        Returns:
            Reporter instance.

        Raises:
            ValueError: If no reporter is available for the format.
        """
        # Normalize format
        if isinstance(format, str):
            format_str = format.lower()
            try:
                format_type = ReportFormatType.from_string(format_str)
            except ValueError:
                format_type = None
        else:
            format_type = format
            format_str = format.value

        effective_locale = locale or self._default_locale

        # 1. Check for registered instance
        if format_str in self._instances:
            return self._instances[format_str]

        # 2. Check for factory function
        if format_type and format_type in self._factories:
            return self._factories[format_type](
                config=config,
                locale=effective_locale,
                **kwargs,
            )

        # 3. Check for registered class
        if format_type and format_type in self._registered:
            reporter_class = self._registered[format_type]
            return reporter_class(**kwargs)

        # 4 & 5. Try built-in or truthound based on preference
        if prefer_truthound and self._use_truthound and self._is_truthound_available():
            reporter = self._create_truthound_reporter(
                format_str,
                locale=effective_locale,
                **kwargs,
            )
            if reporter:
                return reporter

        # 4. Try built-in reporter first (default preference)
        if format_type:
            reporter = self._create_builtin_reporter(format_type, locale=effective_locale)
            if reporter:
                return reporter

        # 5. Try truthound reporter as fallback (for formats not in builtin)
        if self._use_truthound and self._is_truthound_available():
            reporter = self._create_truthound_reporter(
                format_str,
                locale=effective_locale,
                **kwargs,
            )
            if reporter:
                return reporter

        raise ValueError(
            f"No reporter available for format: {format_str}. "
            f"Available formats: {self.get_available_formats()}"
        )

    def _create_truthound_reporter(
        self,
        format_name: str,
        locale: str,
        **kwargs: Any,
    ) -> ReporterProtocol | None:
        """Create a truthound reporter if available."""
        from .adapters import create_truthound_reporter

        return create_truthound_reporter(format_name, locale=locale, **kwargs)

    def _create_builtin_reporter(
        self,
        format_type: ReportFormatType,
        locale: str = "en",
    ) -> ReporterProtocol | None:
        """Create a built-in dashboard reporter."""
        # Lazy import to avoid circular imports
        try:
            if format_type == ReportFormatType.JSON:
                from .builtin.json_reporter import BuiltinJSONReporter

                return BuiltinJSONReporter(locale=locale)

            elif format_type == ReportFormatType.HTML:
                from .builtin.html_reporter import BuiltinHTMLReporter

                return BuiltinHTMLReporter(locale=locale)

            elif format_type == ReportFormatType.CSV:
                from .builtin.csv_reporter import BuiltinCSVReporter

                return BuiltinCSVReporter()

        except ImportError as e:
            logger.warning(f"Built-in reporter for {format_type.value} not available: {e}")

        return None

    def get_available_formats(self) -> list[str]:
        """Get list of available format names.

        Returns:
            List of format name strings.
        """
        formats = set()

        # Add registered formats
        for fmt in self._registered.keys():
            formats.add(fmt.value)
        for fmt in self._factories.keys():
            formats.add(fmt.value)
        for fmt in self._instances.keys():
            formats.add(fmt)

        # Add truthound formats
        if self._use_truthound and self._is_truthound_available():
            from .adapters import get_truthound_formats

            formats.update(get_truthound_formats())

        # Add built-in formats
        builtin_formats = ["json", "html", "csv"]
        formats.update(builtin_formats)

        return sorted(formats)

    def is_format_available(self, format: ReportFormatType | str) -> bool:
        """Check if a format is available.

        Args:
            format: Format to check.

        Returns:
            True if the format is available.
        """
        if isinstance(format, str):
            format_str = format.lower()
        else:
            format_str = format.value

        return format_str in self.get_available_formats()


# Global factory instance
_factory: ReporterFactory | None = None


def get_reporter_factory(
    use_truthound: bool = True,
    default_locale: str = "en",
) -> ReporterFactory:
    """Get the global reporter factory.

    Creates the factory on first call with default settings.
    Subsequent calls return the same instance.

    Args:
        use_truthound: Whether to enable truthound backend (only on first call).
        default_locale: Default locale (only on first call).

    Returns:
        Global ReporterFactory instance.
    """
    global _factory
    if _factory is None:
        _factory = ReporterFactory(
            use_truthound=use_truthound,
            default_locale=default_locale,
        )
    return _factory


def reset_factory() -> None:
    """Reset the global factory (for testing)."""
    global _factory
    _factory = None


def register_reporter(
    format_type: ReportFormatType | str,
) -> Callable[[type[ReporterT]], type[ReporterT]]:
    """Decorator to register a reporter class.

    Example:
        @register_reporter("custom")
        class MyCustomReporter(BaseReporter):
            ...
    """

    def decorator(cls: type[ReporterT]) -> type[ReporterT]:
        get_reporter_factory().register(format_type, cls)
        return cls

    return decorator


# Convenience functions that delegate to the global factory


def get_reporter(
    format: ReportFormatType | str,
    config: ReporterConfig | None = None,
    locale: str | None = None,
    **kwargs: Any,
) -> ReporterProtocol:
    """Get a reporter for the specified format.

    Convenience function that uses the global factory.

    Args:
        format: Report format.
        config: Optional configuration.
        locale: Locale override.
        **kwargs: Additional arguments.

    Returns:
        Reporter instance.
    """
    return get_reporter_factory().get_reporter(
        format,
        config=config,
        locale=locale,
        **kwargs,
    )


def get_available_formats() -> list[str]:
    """Get list of available report formats.

    Convenience function that uses the global factory.

    Returns:
        List of format name strings.
    """
    return get_reporter_factory().get_available_formats()


def is_format_available(format: ReportFormatType | str) -> bool:
    """Check if a format is available.

    Convenience function that uses the global factory.

    Args:
        format: Format to check.

    Returns:
        True if available.
    """
    return get_reporter_factory().is_format_available(format)


async def generate_report(
    data: ReportData,
    format: ReportFormatType | str = ReportFormatType.HTML,
    config: ReporterConfig | None = None,
    locale: str | None = None,
    **kwargs: Any,
) -> ReportOutput:
    """Generate a report using the appropriate reporter.

    High-level convenience function for report generation.

    Args:
        data: Report data.
        format: Output format.
        config: Reporter configuration.
        locale: Locale for i18n.
        **kwargs: Additional arguments passed to reporter.

    Returns:
        ReportOutput with generated content.

    Example:
        data = ReportData.from_validation_model(validation)
        output = await generate_report(data, format="html", locale="ko")
    """
    reporter = get_reporter(format, config=config, locale=locale, **kwargs)
    return await reporter.generate(data, config=config)


async def generate_report_from_validation(
    validation: Any,
    format: ReportFormatType | str = ReportFormatType.HTML,
    config: ReporterConfig | None = None,
    locale: str | None = None,
    **kwargs: Any,
) -> ReportOutput:
    """Generate a report from a Validation model.

    Convenience function that handles the conversion from
    Validation model to ReportData.

    Args:
        validation: Validation model from database.
        format: Output format.
        config: Reporter configuration.
        locale: Locale for i18n.
        **kwargs: Additional arguments.

    Returns:
        ReportOutput with generated content.

    Example:
        validation = await service.get_validation(validation_id)
        output = await generate_report_from_validation(
            validation,
            format="html",
            locale="ko",
        )
    """
    from .adapters import ValidationModelAdapter

    data = ValidationModelAdapter.to_report_data(validation)
    return await generate_report(data, format=format, config=config, locale=locale, **kwargs)
