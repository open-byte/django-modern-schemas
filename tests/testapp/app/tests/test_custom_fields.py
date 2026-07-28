import json

import pytest
from pydantic import ValidationError
from tests.models import Student, StudentEmail

from django_modern_schemas import ModelSchema


class TestCustomFields:
    def test_enum_field(self):
        class StudentSchema(ModelSchema):
            model_config = {'model': Student, 'include': '__all__'}

        assert StudentSchema.model_json_schema() == {
            '$defs': {
                'SemesterEnum': {
                    'enum': ['1', '2', '3'],
                    'title': 'SemesterEnum',
                    'type': 'string',
                }
            },
            'properties': {
                'id': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Id',
                },
                'semester': {
                    '$ref': '#/$defs/SemesterEnum',
                    'default': '1',
                    'description': '',
                    'title': 'Semester',
                },
            },
            'title': 'StudentSchema',
            'type': 'object',
        }
        schema_instance = StudentSchema(semester='1')
        assert str(schema_instance.model_dump_json()) == '{"id":null,"semester":"1"}'
        with pytest.raises(ValidationError):
            StudentSchema(semester='something')

    def test_enum_field_or_greater(self):
        class StudentSchema(ModelSchema):
            model_config = {'model': Student, 'include': '__all__'}

        assert StudentSchema.model_json_schema() == {
            '$defs': {
                'SemesterEnum': {
                    'enum': ['1', '2', '3'],
                    'title': 'SemesterEnum',
                    'type': 'string',
                }
            },
            'properties': {
                'id': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Id',
                },
                'semester': {
                    '$ref': '#/$defs/SemesterEnum',
                    'default': '1',
                    'description': '',
                    'title': 'Semester',
                },
            },
            'title': 'StudentSchema',
            'type': 'object',
        }
        schema_instance = StudentSchema(semester='1')
        assert str(schema_instance.model_dump_json()) == '{"id":null,"semester":"1"}'
        with pytest.raises(ValidationError):
            StudentSchema(semester='something')

    def test_email_field(self):
        class StudentEmailSchema(ModelSchema):
            class Config:
                model = StudentEmail
                include = '__all__'

        assert StudentEmailSchema.model_json_schema() == {
            'properties': {
                'id': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Id',
                },
                'email': {
                    'description': '',
                    'format': 'email',
                    'title': 'Email',
                    'type': 'string',
                },
            },
            'required': ['email'],
            'title': 'StudentEmailSchema',
            'type': 'object',
        }
        assert (
            str(StudentEmailSchema(email='email@example.com').model_dump_json())
            == '{"id":null,"email":"email@example.com"}'
        )
        with pytest.raises(ValidationError):
            StudentEmailSchema(email='emailexample.com')
