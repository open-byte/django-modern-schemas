from collections.abc import Iterator
from itertools import chain
from typing import (
    Any,
    Optional,
    TypeVar,
    cast,
    no_type_check,
)

from django.db.models import Field, ManyToManyRel, ManyToOneRel
from django.db.models import Model as DjangoModel
from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo

from ..errors import ConfigError
from ..pydanticutils import compute_field_annotations
from .mixins import SchemaBaseMixins, SchemaOperationMixin
from .schema_registry import registry as global_registry
from .utils.converter import convert_django_field_with_choices

ALL_FIELDS = '__all__'

__all__ = ['ModelSchema']


PydanticNamespace = None

T = TypeVar('T', bound=DjangoModel)


def update_class_missing_fields(cls: type, bases: list[type[BaseModel]], namespace: dict):  # pragma: no cover
    return cls


class ModelSchemaConfigAdapter:
    def __init__(self, config: dict) -> None:
        self.__dict__ = config


class ModelSchemaConfig:
    def __init__(
        self,
        schema_class_name: str,
        options: dict[str, Any] | ModelSchemaConfigAdapter | None = None,
    ):
        self.model = getattr(options, 'model', None)
        _include = getattr(options, 'include', None) or ALL_FIELDS
        self.include = set() if _include == ALL_FIELDS else set(_include or ())
        self.exclude = set(getattr(options, 'exclude', None) or ())
        self.skip_registry = getattr(options, 'skip_registry', False)
        self.registry = getattr(options, 'registry', global_registry)
        self.abstract = getattr(options, 'ninja_schema_abstract', False)
        _optional = getattr(options, 'optional', None)
        self.optional = {ALL_FIELDS} if _optional == ALL_FIELDS else set(_optional or ())
        self.depth = int(getattr(options, 'depth', 0))
        self.schema_class_name = schema_class_name
        if not self.abstract:
            self.validate_configuration()
            self.process_build_schema_parameters()

    @classmethod
    def clone_field(cls, field: FieldInfo, **kwargs: Any) -> FieldInfo:
        field_dict = dict(field.__repr_args__())
        field_dict.update(**kwargs)
        new_field = FieldInfo(**field_dict)
        return new_field

    def model_fields(self) -> Iterator[Field]:
        """returns iterator with all the fields that can be part of schema"""
        for fld in self.model._meta.get_fields():  # ty:ignore[unresolved-attribute]
            if isinstance(fld, (ManyToOneRel, ManyToManyRel)):
                # skipping relations
                continue
            yield cast(Field, fld)

    def validate_configuration(self) -> None:
        self.include = set() if self.include == ALL_FIELDS else set(self.include or ())

        if not self.model:
            raise ConfigError("Invalid Configuration. 'model' is required")

        if self.include and self.exclude:
            raise ConfigError("Only one of 'include' or 'exclude' should be set in configuration.")

    def check_invalid_keys(self, **field_names: dict[str, Any]) -> None:
        keys = field_names.keys()
        invalid_include_exclude_fields = (set(self.include or []) | set(self.exclude or [])) - keys
        if invalid_include_exclude_fields:
            raise ConfigError(f'Field(s) {invalid_include_exclude_fields} are not in model.')
        if ALL_FIELDS not in self.optional:
            invalid_options_fields = set(self.optional) - keys
            if invalid_options_fields:
                raise ConfigError(f'Field(s) {invalid_options_fields} are not in model.')

    def is_field_in_optional(self, field_name: str) -> bool:
        if not self.optional:
            return False
        if ALL_FIELDS in self.optional:
            return True
        if isinstance(self.optional, (set, tuple, list)) and field_name in self.optional:
            return True
        return False

    def process_build_schema_parameters(self) -> None:
        model_pk = getattr(
            self.model._meta.pk,  # type: ignore
            'name',
            self.model._meta.pk.attname,  # type: ignore
        )  # no type:ignore
        if model_pk not in self.include and model_pk not in self.exclude and ALL_FIELDS not in self.optional:
            self.optional.add(str(model_pk))  # ty:ignore[invalid-argument-type]


class ModelSchemaMetaclass(ModelMetaclass):
    @no_type_check
    def __new__(
        mcs,
        name: str,
        bases: tuple,
        namespace: dict,
        **kwargs: Any,
    ):
        if bases == (SchemaBaseModel,) or not namespace.get('Config', namespace.get('model_config')):
            return super().__new__(mcs, name, bases, namespace, **kwargs)

        config = namespace.get('Config')
        if not config:
            model_config = namespace.get('model_config')
            if model_config:
                config = ModelSchemaConfigAdapter(model_config)

        config_instance = None

        if config:
            config_instance = ModelSchemaConfig(name, config)

        if config_instance and config_instance.model and not config_instance.abstract:
            annotations = namespace.get('__annotations__', {})
            try:
                fields = list(config_instance.model_fields())
            except AttributeError as exc:
                raise ConfigError(f'{exc} (Is `Config.model` a valid Django model class?)') from exc

            field_values, _seen = {}, set()

            all_fields = {f.name: f for f in fields}
            config_instance.check_invalid_keys(**all_fields)

            for field in chain(fields, annotations.copy()):
                field_name = getattr(field, 'name', getattr(field, 'related_name', field))

                if (
                    field_name in _seen
                    or (
                        (config_instance.include and field_name not in config_instance.include)
                        or (config_instance.exclude and field_name in config_instance.exclude)
                    )
                    and field_name not in annotations
                ):
                    continue

                _seen.add(field_name)
                if field_name in annotations and field_name in namespace:
                    python_type = annotations.pop(field_name)
                    pydantic_field = namespace[field_name]
                    if hasattr(pydantic_field, 'default_factory') and pydantic_field.default_factory:
                        pydantic_field = pydantic_field.default_factory()

                elif field_name in annotations:
                    python_type = annotations.pop(field_name)
                    pydantic_field = None if Optional[python_type] == python_type else Ellipsis  # noqa: UP045

                else:
                    python_type, pydantic_field = convert_django_field_with_choices(
                        field,
                        registry=config_instance.registry,
                        depth=config_instance.depth,
                        skip_registry=config_instance.skip_registry,
                    )

                    if pydantic_field.default is None:
                        python_type = Optional[python_type]  # noqa: UP045

                    if config_instance.is_field_in_optional(field_name):
                        pydantic_field = ModelSchemaConfig.clone_field(
                            field=pydantic_field, default=None, default_factory=None
                        )
                        python_type = Optional[python_type]  # noqa: UP045

                field_values[field_name] = (python_type, pydantic_field)

            return super().__new__(
                mcs,
                name,
                bases,
                compute_field_annotations(namespace, **field_values),
                **kwargs,
            )
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class SchemaBaseModel(BaseModel, SchemaBaseMixins):
    pass


class BaseModelSchema(SchemaBaseModel, metaclass=ModelSchemaMetaclass):
    model_config = {'from_attributes': True, 'ninja_schema_abstract': True}  # ty:ignore[conflicting-metaclass]


class ModelSchema(BaseModelSchema, SchemaOperationMixin[T]):
    model_config = {'from_attributes': True, 'ninja_schema_abstract': True}
