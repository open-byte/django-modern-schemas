from django_modern_schemas import ModelSchema

from .models import Event


class EventSummarySchema(ModelSchema):
    class Config:
        model = Event
        fields = ['title']


class EventPatchSchema(ModelSchema):
    class Config:
        model = Event
        fields = ['title']
        optional = ['title']


class EventWithoutCategorySchema(ModelSchema):
    class Config:
        model = Event
        exclude = ['category']


class EventWithCategorySchema(ModelSchema):
    class Config:
        model = Event
        fields = '__all__'
        depth = 1


def serialize_event(event: Event) -> dict[str, object]:
    """Serialize the fields selected by EventSummarySchema."""
    return EventSummarySchema.model_validate(event).model_dump()
