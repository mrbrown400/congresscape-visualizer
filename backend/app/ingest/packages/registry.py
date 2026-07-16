"""Explicit registry for enabled jurisdiction ingestion packages."""
from __future__ import annotations

from collections.abc import Iterable

from .contracts import JurisdictionPackage


class PackageNotEnabledError(LookupError):
    """Raised when a package is unknown or not enabled by configuration."""


class PackageRegistry:
    """Resolve only packages explicitly enabled by the application."""

    def __init__(
        self,
        packages: Iterable[JurisdictionPackage],
        *,
        enabled: Iterable[str] = ("federal",),
    ) -> None:
        self._packages = {package.key: package for package in packages}
        self._enabled = frozenset(enabled)

    def get(self, key: str) -> JurisdictionPackage:
        if key not in self._enabled:
            raise PackageNotEnabledError(f"Ingestion package is not enabled: {key}")
        try:
            return self._packages[key]
        except KeyError as exc:
            raise PackageNotEnabledError(f"Unknown ingestion package: {key}") from exc

    def enabled(self) -> tuple[JurisdictionPackage, ...]:
        """Return enabled packages in stable key order."""
        return tuple(self._packages[key] for key in sorted(self._enabled) if key in self._packages)

    def keys(self) -> tuple[str, ...]:
        return tuple(package.key for package in self.enabled())
