from typing import Any

from django.db.models import Manager, QuerySet
from django.db.models.fields.files import FieldFile

from ..metadata import MethodSource, Source, SourceResolver

__all__ = [
    'DjangoGetter',
]


source_resolver = SourceResolver()


class DjangoGetterMixin:
    def _convert_result(self, result: Any) -> Any:
        if isinstance(result, Manager):
            return list(result.all())

        elif isinstance(result, getattr(QuerySet, '__origin__', QuerySet)):
            return list(result)

        elif isinstance(result, FieldFile):
            if not result:
                return None
            return result.url

        return result


class DjangoGetter(DjangoGetterMixin):
    __slots__ = ('_obj', '_schema_cls', '_context')

    def __init__(self, obj: Any, schema_cls: Any, context: Any = None):
        self._obj = obj
        self._schema_cls = schema_cls
        self._context = context

    def __getattr__(self, key: str) -> Any:
        # if key.startswith("__pydantic"):
        #     return getattr(self._obj, key)
        source = self._get_source(key)
        if isinstance(self._obj, dict):
            if key in self._obj:
                value = self._obj[key]
            elif source:
                value = source_resolver.resolve(self._obj, source)
            else:
                raise AttributeError(key)
        elif source:
            value = source_resolver.resolve(self._obj, source)
        else:
            try:
                value = getattr(self._obj, key)
            except AttributeError as e:
                raise AttributeError(key) from e

        return self._convert_result(value)

    def _get_source(self, key: str) -> Source | MethodSource | None:
        field = self._schema_cls.model_fields.get(key)
        if not field:
            return None

        return next(
            (metadata for metadata in field.metadata if isinstance(metadata, (Source, MethodSource))),
            None,
        )
