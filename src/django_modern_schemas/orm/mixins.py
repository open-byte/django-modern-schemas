from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.core.exceptions import FieldDoesNotExist
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

    @staticmethod
    def _split_relations(model_cls: type[DjangoModel], data: DictStrAny) -> tuple[DictStrAny, DictStrAny]:
        """Split validated data into direct fields and many-to-many fields.

        Many-to-many values are removed because they cannot be passed to `create()`:
        they require a saved instance. Forward relations holding a primary key are
        rewritten to the Django attribute name (`category` -> `category_id`), since
        the ORM only accepts a model instance under the plain field name.
        """
        direct: DictStrAny = {}
        many_to_many: DictStrAny = {}

        for name, value in data.items():
            try:
                field = model_cls._meta.get_field(name)
            except FieldDoesNotExist:
                direct[name] = value
                continue

            if field.many_to_many:
                many_to_many[name] = value
            elif field.is_relation and field.concrete and not isinstance(value, DjangoModel):
                direct.setdefault(field.attname, value)
            else:
                direct[name] = value

        return direct, many_to_many

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
        dumped = self.model_dump(exclude_unset=bool(partial), by_alias=True)  # ty:ignore[unresolved-attribute]
        data = {attr: value for attr, value in dumped.items() if attr not in source_field_names}

        # Unlike `create()`, many-to-many values only need to wait for the save below,
        # because an existing instance already has the pk the relation is stored against.
        direct, many_to_many = self._split_relations(type(instance), data)

        for attr, value in direct.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)

        instance.save()

        # Set many-to-many fields after saving: doing so triggers signals that could
        # change the instance, and we do not want that colliding with the update above.
        for attr, value in many_to_many.items():
            getattr(instance, attr).set(value)

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

        # Many-to-many values are not valid arguments to `create()`: they require the
        # instance to already be saved, so they are applied afterwards.
        direct, many_to_many = self._split_relations(ModelClass, data)

        try:
            record: M = ModelClass._default_manager.create(**direct)

        except Exception as e:
            # Handle case where the model does not accept certain fields

            raise TypeError(
                f'Error creating {ModelClass.__name__} instance: {e}. '
                'This may be because the schema has a writable field that is not a valid '
                f'argument to {ModelClass.__name__}.{ModelClass._default_manager.name}.create(). '
                f'You may need to make the field read-only, or override {type(self).__name__}.create() '
                'to handle it.'
            ) from e

        for field_name, value in many_to_many.items():
            getattr(record, field_name).set(value)

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
        if isinstance(values, BaseModel):
            return handler(values)

        # `extra='forbid'` can only be checked before wrapping: DjangoGetter's
        # __getattr__ hides a dict's leftover keys.
        if isinstance(values, dict) and cls.model_config.get('extra') == 'forbid':
            handler(values)

        return handler(DjangoGetter(values, cls, info.context))


class SchemaBaseMixins(BaseMixins):
    pass
