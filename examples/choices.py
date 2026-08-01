from django_modern_schemas import ModelSchema

from .models import Student


class StudentSchema(ModelSchema):
    class Config:
        model = Student
        fields = '__all__'


def validate_semester(semester: str) -> dict[str, object]:
    """Validate a Django choices value through the generated Pydantic schema."""
    return StudentSchema.model_validate({'semester': semester}).model_dump()
