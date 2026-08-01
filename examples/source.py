from typing import Annotated

from django_modern_schemas import MethodSource, ModelSchema, Source, SourceResolver

from .models import Category, Event, Question


class EventSourceSchema(ModelSchema):
    category_name: Annotated[str | None, Source('category.name')]
    display_title: Annotated[str, MethodSource('display_title')]

    class Config:
        model = Event
        fields = ['title']


class QuestionSchema(ModelSchema):
    class Config:
        model = Question
        fields = ['text']


class CategoryQuestionsSchema(ModelSchema):
    questions: Annotated[list[QuestionSchema], Source('questions')]

    class Config:
        model = Category
        fields = ['name']


def resolve_category_name(event: Event) -> str | None:
    """Resolve a Source path without constructing a schema."""
    return SourceResolver().resolve(event, Source('category.name'))


def resolve_mapping_category_name(data: dict[str, dict[str, str]]) -> str:
    """Resolve the same Source path from mapping input."""
    return SourceResolver().resolve(data, Source('category.name'))


def serialize_event(event: Event) -> dict[str, object]:
    """Expose a nested attribute and a zero-argument model method."""
    return EventSourceSchema.model_validate(event).model_dump()


def serialize_category(category: Category) -> dict[str, object]:
    """Serialize a prefetched reverse ForeignKey collection."""
    return CategoryQuestionsSchema.model_validate(category).model_dump()
