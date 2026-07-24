from typing import TYPE_CHECKING

from django.db.models import Model

from .schema import Schema
from .utils.utils import is_valid_class, is_valid_django_model

if TYPE_CHECKING:
    from ..orm.model_schema import ModelSchema

__all__ = ['SchemaRegister', 'registry']


class SchemaRegisterBorg:
    _shared_state: dict[str, dict] = {}

    def __init__(self) -> None:
        self.__dict__ = self._shared_state


class SchemaRegister(SchemaRegisterBorg):
    schemas: dict[type[Model], type['ModelSchema'] | type[Schema]]
    fields: dict[str, tuple]

    def __init__(self) -> None:
        SchemaRegisterBorg.__init__(self)
        if not hasattr(self, 'schemas'):
            self._shared_state.update(schemas={}, fields={})

    def register_model(self, model: type[Model], schema: type['ModelSchema']) -> None:
        from ..orm.model_schema import ModelSchema

        assert is_valid_class(schema) and issubclass(schema, (ModelSchema,)), (
            f'Only Schema can be registered, received "{schema.__name__}"'
        )
        assert is_valid_django_model(model), f'Only Django Models are allowed. {model.__name__}'
        # TODO: register model as module_name.model_name
        self.register_schema(model, schema)

    def register_schema(self, name: type[Model], schema: type['ModelSchema'] | type[Schema]) -> None:
        self.schemas[name] = schema

    def get_model_schema(self, model: type[Model]) -> type['ModelSchema'] | type[Schema] | None:
        if model in self.schemas:
            return self.schemas[model]
        return None


registry = SchemaRegister()
