"""
Django Modern Schema - Builds Pydantic Schemas from Django Models with default field type validations
"""

__version__ = '0.0.1'

from .metadata import MethodSource, Source, SourceResolutionError, SourceResolver
from .orm.factory import SchemaFactory
from .orm.model_schema import ModelSchema
from .orm.schema import Schema

__all__ = [
    'MethodSource',
    'ModelSchema',
    'Schema',
    'SchemaFactory',
    'Source',
    'SourceResolutionError',
    'SourceResolver',
]
