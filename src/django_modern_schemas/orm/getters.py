from typing import Any

from django.db.models import Manager, QuerySet
from django.db.models.fields.files import FieldFile

__all__ = [
    'DjangoGetter',
]


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
        if isinstance(self._obj, dict):
            if key not in self._obj:
                raise AttributeError(key)
            value = self._obj[key]
        else:
            try:
                value = getattr(self._obj, key)
            except AttributeError as e:
                raise AttributeError(key) from e

        return self._convert_result(value)
