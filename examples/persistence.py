from django_modern_schemas import ModelSchema

from .models import Event


class EventWriteSchema(ModelSchema):
    class Config:
        model = Event
        fields = ['title']


def create_event(title: str) -> Event:
    """Create an Event from validated schema input."""
    schema = EventWriteSchema.model_validate({'title': title})
    return schema.create()


def rename_event(event: Event, title: str) -> Event:
    """Update an existing Event from validated schema input."""
    schema = EventWriteSchema.model_validate({'title': title})
    return schema.update(event)
