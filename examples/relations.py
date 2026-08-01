from django_modern_schemas import ModelSchema

from .models import Week


class WeekSchema(ModelSchema):
    class Config:
        model = Week
        fields = ['name', 'days']
        depth = 1


def serialize_week(week: Week) -> dict[str, object]:
    """Serialize a Week with nested ManyToMany Day schemas."""
    return WeekSchema.model_validate(week).model_dump()
