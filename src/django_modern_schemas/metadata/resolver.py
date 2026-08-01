from collections.abc import Mapping
from typing import Any

from django.db.models import ForeignKey, Manager, QuerySet

from .exceptions import SourceResolutionError
from .source import MethodSource, Source


class SourceResolver:
    """Resolve Source metadata without materializing related collections."""

    def resolve(self, instance: Any, source: Source | MethodSource) -> Any:
        if isinstance(source, MethodSource):
            return self.resolve_method(instance, source)

        value = instance
        for index, attribute in enumerate(source.parts):
            if value is None:
                return None

            value = self._resolve_attribute(value, attribute, source.path)
            if self._is_collection(value):
                if index < len(source.parts) - 1:
                    raise SourceResolutionError(
                        f'Unable to resolve {source.path!r}: attribute {attribute!r} resolves to a collection '
                        'that cannot be traversed.'
                    )
                if not self._is_reverse_foreign_key_manager(value):
                    raise SourceResolutionError(
                        f'Unable to resolve {source.path!r}: Source only supports reverse ForeignKey collections.'
                    )

        return value

    def resolve_method(self, instance: Any, source: MethodSource) -> Any:
        if instance is None:
            return None

        method = self._resolve_attribute(instance, source.name, source.name)
        if not callable(method):
            raise SourceResolutionError(
                f'Unable to resolve method {source.name!r}: method {source.name!r} is not callable.'
            )

        try:
            return method()
        except TypeError as exc:
            raise SourceResolutionError(
                f'Unable to resolve method {source.name!r}: methods cannot require arguments.'
            ) from exc

    @staticmethod
    def _is_collection(value: Any) -> bool:
        return isinstance(value, (Manager, QuerySet))

    @staticmethod
    def _is_reverse_foreign_key_manager(value: Any) -> bool:
        return isinstance(value, Manager) and isinstance(getattr(value, 'field', None), ForeignKey)

    @staticmethod
    def _resolve_attribute(value: Any, attribute: str, source_path: str) -> Any:
        if isinstance(value, Mapping):
            try:
                return value[attribute]
            except KeyError as exc:
                raise SourceResolutionError(
                    f'Unable to resolve {source_path!r}: key {attribute!r} was not found.'
                ) from exc

        try:
            return getattr(value, attribute)
        except AttributeError as exc:
            raise SourceResolutionError(
                f'Unable to resolve {source_path!r}: attribute {attribute!r} was not found on {type(value).__name__}. '
            ) from exc
