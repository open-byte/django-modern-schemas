from django_modern_schemas import ModelSchema, SchemaFactory

from .models import Event


def build_event_title_schema() -> type[ModelSchema]:
    """Build a one-field Event schema without using the global registry."""
    schema = SchemaFactory.create_schema(
        Event,
        name='EventTitleSchema',
        fields=['title'],
        skip_registry=True,
    )
    assert schema is not None
    return schema


def serialize_event(event: Event) -> dict[str, object]:
    """Serialize an Event with a schema generated at runtime."""
    return build_event_title_schema().model_validate(event).model_dump()
