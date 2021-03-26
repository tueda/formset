"""Determine suitable FORM setup parameters."""

from .formset import Setup, SystemInfo
from .formset import __version__ as __version__  # noqa: F401  # reexport for mypy
from .formset import main as main  # noqa: F401

__all__ = ["Setup", "SystemInfo"]
