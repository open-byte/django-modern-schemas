from typing import TYPE_CHECKING, cast

from django.db.models import Model

from ..errors import ConfigError
from ..types import DictStrAny
from .schema_registry import SchemaRegister
from .schema_registry import registry as schema_registry

if TYPE_CHECKING:
    from .model_schema import ModelSchema
    from .schema import Schema

__all__ = ['SchemaFactory']


class SchemaFactory:
    @classmethod
    def get_model_config(cls, **kwargs: DictStrAny) -> type:
        class Config:
            pass

        for key, value in kwargs.items():
            setattr(Config, key, value)
        return Config

    @classmethod
    def create_schema(
        cls,
        model: type[Model],
        *,
        registry: SchemaRegister = schema_registry,
        name: str = '',
        depth: int = 0,
        fields: list[str] | None = None,
        exclude: list[str] | None = None,
        skip_registry: bool = False,
        optional_fields: str | list[str] | None = None,
        **model_config_options: DictStrAny,
    ) -> type['ModelSchema'] | type['Schema'] | None:
        from .model_schema import ModelSchema

        name = name or model.__name__

        if fields and exclude:
            raise ConfigError("Only one of 'include' or 'exclude' should be set.")

        schema = registry.get_model_schema(model)
        if schema and not skip_registry:
            return schema

        model_config_kwargs = {
            'model': model,
            'include': fields,
            'exclude': exclude,
            'skip_registry': skip_registry,
            'depth': depth,
            'registry': registry,
            'optional': optional_fields,
            **model_config_options,
        }
        cls.get_model_config(**model_config_kwargs)
        new_schema = cls._get_schema(name, model_config_kwargs, ModelSchema)

        new_schema = cast(type[ModelSchema], new_schema)
        if not skip_registry:
            registry.register_model(model, new_schema)
        return new_schema

    @classmethod
    def _get_schema(
        cls, name: str, model_config_kwargs: dict, model_type: type
    ) -> type['ModelSchema'] | type['Schema'] | None:
        model_config = cls.get_model_config(**model_config_kwargs)
        new_schema_result = {}
        new_schema_string = f"""class {name}(model_type):
            class Config(model_config):
                pass """

        exec(new_schema_string, locals(), new_schema_result)
        return new_schema_result.get(name)
