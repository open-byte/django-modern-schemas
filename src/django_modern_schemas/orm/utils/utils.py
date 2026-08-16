import inspect
from typing import Annotated, Any

from django.db import models
from django.db.models import Model
from pydantic import BaseModel, Field

from ...metadata import MethodSource, Source


def is_valid_django_model(model: type[Model]) -> bool:
    return is_valid_class(model) and issubclass(model, models.Model)


def is_valid_class(klass: type) -> bool:
    return inspect.isclass(klass)


def has_child_model(model_cls: type[BaseModel]) -> bool:
    """Returns True if any field in the class links to a Pydantic model."""
    for field_name, field_info in model_cls.model_fields.items():
        # Get the underlying type or arguments from typing containers
        annotation = field_info.annotation

        # Helper to recursively check standard types, Unions, and Lists
        if _contains_basemodel(annotation):
            return True
    return False


def _contains_basemodel(tp) -> bool:
    """Helper to check if a type is or contains a BaseModel subclass."""
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return True
    # Handle typing structures like List[Child], Union[Child, None]
    if hasattr(tp, '__args__'):
        for arg in tp.__args__:
            if _contains_basemodel(arg):
                return True
    return False


def freeze_source_annotation(annotation: Any) -> Any:
    """Returns the annotation as a frozen field when it carries `Source` or `MethodSource`."""
    if any(isinstance(meta, (Source, MethodSource)) for meta in getattr(annotation, '__metadata__', ())):
        return Annotated[annotation, Field(frozen=True)]
    return annotation
