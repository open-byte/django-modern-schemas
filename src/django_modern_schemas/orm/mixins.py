from typing import TYPE_CHECKING, Any, TypeVar

from django.db.models import Model as DjangoModel
from pydantic import BaseModel, model_validator
from pydantic.json_schema import GenerateJsonSchema
from pydantic_core.core_schema import ValidationInfo

from django_modern_schemas.orm.getters import DjangoGetter
from django_modern_schemas.types import DictStrAny

if TYPE_CHECKING:
    from pydantic.functional_validators import ModelWrapValidatorHandler

    ModelWrapValidatorHandlerAny = TypeVar('ModelWrapValidatorHandlerAny', bound=ModelWrapValidatorHandler[Any])


class BaseMixins:
    model_config: dict[str, Any]

    def apply_to_model(self, model_instance: type[DjangoModel], **kwargs: DictStrAny) -> type[DjangoModel]:
        for attr, value in self.model_dump(**kwargs).items():  # ty:ignore[unresolved-attribute]
            setattr(model_instance, attr, value)
        return model_instance

    @model_validator(mode='wrap')
    @classmethod
    def _run_root_validator(
        cls,
        values: Any,
        handler: 'ModelWrapValidatorHandlerAny',
        info: ValidationInfo,
    ) -> Any:
        """
        If Pydantic intends to validate against the __dict__ of the immediate Schema
        object, then we need to call `handler` directly on `values` before the conversion
        to DjangoGetter, since any checks or modifications on DjangoGetter's __dict__
        will not persist to the original object.
        """
        forbids_extra = cls.model_config.get('extra') == 'forbid'
        should_validate_assignment = cls.model_config.get('validate_assignment', False)
        if forbids_extra or should_validate_assignment:
            handler(values)

        values = DjangoGetter(values, cls, info.context)
        return handler(values)

    @classmethod
    def from_orm(cls, obj: Any, **options: Any) -> BaseModel:
        """
        In normal Pydantic, `from_orm` is a class method that takes an object and returns a Pydantic model instance.
        In this case, we are overriding it to use `model_validate` instead of `from_orm`,
          which allows us to validate the object against the schema defined in the Pydantic model.

        """
        return cls.model_validate(  # ty:ignore[unresolved-attribute]
            obj, **options
        )


class SchemaMixins(BaseMixins):
    pass
