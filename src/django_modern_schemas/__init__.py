"""
Django Modern Schema - Builds Pydantic Schemas from Django Models with default field type validations
"""

from importlib.metadata import version as _version

from .metadata import MethodSource, Source, SourceResolutionError, SourceResolver
from .orm.factory import SchemaFactory
from .orm.model_schema import ModelSchema
from .orm.schema import Schema

# Read from the installed distribution so the version lives only in pyproject.toml.
__version__ = _version('django-modern-schemas')

__all__ = [
    'MethodSource',
    'ModelSchema',
    'Schema',
    'SchemaFactory',
    'Source',
    'SourceResolutionError',
    'SourceResolver',
    '__version__',
]
