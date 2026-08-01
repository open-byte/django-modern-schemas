from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.db.models import Model as DjangoModel
from pydantic import BaseModel, model_validator
from pydantic.json_schema import GenerateJsonSchema
from pydantic_core.core_schema import ValidationInfo

from django_modern_schemas.metadata import MethodSource, Source
from django_modern_schemas.orm.getters import DjangoGetter
from django_modern_schemas.orm.utils.utils import has_child_model
from django_modern_schemas.types import DictStrAny

if TYPE_CHECKING:
    from pydantic.functional_validators import ModelWrapValidatorHandler

    ModelWrapValidatorHandlerAny = TypeVar('ModelWrapValidatorHandlerAny', bound=ModelWrapValidatorHandler[Any])


M = TypeVar('M', bound=DjangoModel)


class SchemaOperationMixin(Generic[M]):
    """
    Mixin class for schema operations related to Django models.

    This mixin provides methods for creating, updating, and saving Django model instances
    based on the data in the schema. It also includes a root validator to handle validation
    against the schema's fields.
    """

    _object: M | None = None  # This can hold the Django model instance used by save.

    def _source_field_names(self) -> set[str]:
        return {
            field_name
            for field_name, field_info in self.__class__.model_fields.items()  # ty:ignore[unresolved-attribute]
            if any(isinstance(metadata, (Source, MethodSource)) for metadata in field_info.metadata)
        }

    def update(
        self,
        instance: M,
        partial: bool | None = False,
        **kwargs: Any,
    ) -> M:
        """
        Updates an existing Django model instance using the schema's data.

        If `partial` is True, only updates fields that are set.
        This method can be overridden to implement custom update logic.
        """
        if has_child_model(self.__class__):  # ty:ignore[invalid-argument-type]
            raise NotImplementedError(
                'Updating models with child Pydantic models is not supported yet. '
                'Please override the `update` method in your schema.'
            )

        source_field_names = self._source_field_names()
        if partial:
            for attr, value in self.model_dump(exclude_unset=True, by_alias=True).items():  # ty:ignore[unresolved-attribute]
                if attr not in source_field_names and hasattr(instance, attr):
                    setattr(instance, attr, value)
        else:
            for attr, value in self.model_dump().items():  # ty:ignore[unresolved-attribute]
                if attr not in source_field_names and hasattr(instance, attr):
                    setattr(instance, attr, value)

        instance.save()

        return instance

    def create(self, *args: Any, **kwargs: Any) -> M:
        """
        Creates a new Django model instance based on the schema's data.

        This method can be overridden by subclasses to customize creation logic.

        Parameters:
            data (dict[str, Any]): Data to create the model instance.
            *args (Any): Additional positional arguments.
            **kwargs (Any): Additional keyword arguments.
        Returns:
            M: The newly created model instance.


        """
        if has_child_model(self.__class__):  # ty:ignore[invalid-argument-type]
            raise NotImplementedError(
                'Creating models with child Pydantic models is not supported yet. '
                'Please override the `create` method in your schema.'
            )
        ModelClass: type[M] = self.Config.model  # ty:ignore[unresolved-attribute]
        exclude_computed_fields = self.model_computed_fields.keys()  # ty:ignore[unresolved-attribute]
        excluded_fields = set(exclude_computed_fields) | self._source_field_names()

        ## Just in case,  by_alias=True is used to insert related fields
        ## that are not part of the model, but are needed for creation.
        ## the instance.
        data = self.model_dump(exclude=excluded_fields, by_alias=True, **kwargs)  # ty:ignore[unresolved-attribute]

        try:
            record: M = ModelClass._default_manager.create(**data)

        except Exception as e:
            # Handle case where the model does not accept certain fields

            raise TypeError(
                f'Error creating {ModelClass.__name__} instance: {e}. '
                "Ensure that all fields in the schema match the model's fields."
            ) from e

        return record

    def save(self, instance: M | None = None, partial: bool | None = None, **kwargs: Any) -> M:
        """
        This method handles both creation and update scenarios:
        - If an instance exists in `self._object`, it updates that instance
        - If an external instance is provided, it updates that instance
        - If no instance exists, it creates a new one

        Parameters:
            instance (M | None): Optional model instance to update. Default is None.
            partial (bool | None): Whether to perform a partial update. Default is None.
            **kwargs (Any): Additional keyword arguments passed to the update method.

        Returns:
            M: The saved model instance.
        """
        if self._object:  # ty:ignore[unresolved-attribute]
            record = self.update(self._object, partial=partial, **kwargs)  #  # ty:ignore[unresolved-attribute]

        elif instance is not None:
            record = self.update(instance, partial=partial, **kwargs)

        else:
            record = self.create(**kwargs)
        record.save()
        return record


class BaseMixins:
    model_config: dict[str, Any]

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


class SchemaBaseMixins(BaseMixins):
    pass
