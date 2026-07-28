import json
import typing as t

import pydantic
import pytest
from django.db.models import Model as DjangoModel
from tests.models import Event

from django_modern_schemas import ModelSchema, SchemaFactory
from django_modern_schemas.errors import ConfigError

T = t.TypeVar('T', bound=DjangoModel)


class TestModelSchema:
    def test_schema_include_fields(self):
        class EventSchema(ModelSchema):
            class Config:
                model = Event
                include = '__all__'

        assert EventSchema.model_json_schema() == {
            'properties': {
                'id': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Id',
                },
                'title': {
                    'description': '',
                    'maxLength': 100,
                    'title': 'Title',
                    'type': 'string',
                },
                'category': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Category',
                },
                'start_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'Start Date',
                    'type': 'string',
                },
                'end_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'End Date',
                    'type': 'string',
                },
            },
            'required': ['title', 'start_date', 'end_date'],
            'title': 'EventSchema',
            'type': 'object',
        }

        class Event2Schema(ModelSchema):
            class Config:
                model = Event
                include = ['title', 'start_date', 'end_date']

        assert Event2Schema.model_json_schema() == {
            'properties': {
                'title': {
                    'description': '',
                    'maxLength': 100,
                    'title': 'Title',
                    'type': 'string',
                },
                'start_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'Start Date',
                    'type': 'string',
                },
                'end_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'End Date',
                    'type': 'string',
                },
            },
            'required': ['title', 'start_date', 'end_date'],
            'title': 'Event2Schema',
            'type': 'object',
        }

    def test_schema_depth(self):
        class EventDepthSchema(ModelSchema):
            class Config:
                model = Event
                include = '__all__'
                depth = 1

        assert EventDepthSchema.model_json_schema() == {
            '$defs': {
                'Category': {
                    'properties': {
                        'id': {
                            'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                            'default': None,
                            'description': '',
                            'title': 'Id',
                        },
                        'name': {
                            'description': '',
                            'maxLength': 100,
                            'title': 'Name',
                            'type': 'string',
                        },
                        'start_date': {
                            'description': '',
                            'format': 'date',
                            'title': 'Start Date',
                            'type': 'string',
                        },
                        'end_date': {
                            'description': '',
                            'format': 'date',
                            'title': 'End Date',
                            'type': 'string',
                        },
                    },
                    'required': ['name', 'start_date', 'end_date'],
                    'title': 'Category',
                    'type': 'object',
                }
            },
            'properties': {
                'id': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Id',
                },
                'title': {
                    'description': '',
                    'maxLength': 100,
                    'title': 'Title',
                    'type': 'string',
                },
                'category': {
                    'anyOf': [{'$ref': '#/$defs/Category'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Category',
                },
                'start_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'Start Date',
                    'type': 'string',
                },
                'end_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'End Date',
                    'type': 'string',
                },
            },
            'required': ['title', 'start_date', 'end_date'],
            'title': 'EventDepthSchema',
            'type': 'object',
        }

    def test_schema_exclude_fields(self):
        class Event3Schema(ModelSchema):
            class Config:
                model = Event
                exclude = ['id', 'category']

        assert Event3Schema.model_json_schema() == {
            'properties': {
                'title': {
                    'description': '',
                    'maxLength': 100,
                    'title': 'Title',
                    'type': 'string',
                },
                'start_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'Start Date',
                    'type': 'string',
                },
                'end_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'End Date',
                    'type': 'string',
                },
            },
            'required': ['title', 'start_date', 'end_date'],
            'title': 'Event3Schema',
            'type': 'object',
        }

    def test_schema_optional_fields(self):
        class Event4Schema(ModelSchema):
            class Config:
                model = Event
                include = '__all__'
                optional = '__all__'

        assert Event4Schema.model_json_schema() == {
            'properties': {
                'id': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Id',
                },
                'title': {
                    'anyOf': [{'type': 'string'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Title',
                },
                'category': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Category',
                },
                'start_date': {
                    'anyOf': [{'format': 'date', 'type': 'string'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Start Date',
                },
                'end_date': {
                    'anyOf': [{'format': 'date', 'type': 'string'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'End Date',
                },
            },
            'title': 'Event4Schema',
            'type': 'object',
        }

        class Event5Schema(ModelSchema):
            class Config:
                model = Event
                include = ['id', 'title', 'start_date']
                optional = [
                    'start_date',
                ]

        assert Event5Schema.model_json_schema() == {
            'properties': {
                'id': {'description': '', 'title': 'Id', 'type': 'integer'},
                'title': {
                    'description': '',
                    'maxLength': 100,
                    'title': 'Title',
                    'type': 'string',
                },
                'start_date': {
                    'anyOf': [{'format': 'date', 'type': 'string'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Start Date',
                },
            },
            'required': ['id', 'title'],
            'title': 'Event5Schema',
            'type': 'object',
        }

    def test_schema_custom_fields(self):
        class Event6Schema(ModelSchema):
            custom_field1: str
            custom_field2: int = 1
            custom_field3: str = ''
            __custom_field4 = []  # ignored by pydantic

            class Config:
                model = Event
                exclude = ['id', 'category']

        assert Event6Schema.model_json_schema() == {
            'properties': {
                'title': {
                    'description': '',
                    'maxLength': 100,
                    'title': 'Title',
                    'type': 'string',
                },
                'start_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'Start Date',
                    'type': 'string',
                },
                'end_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'End Date',
                    'type': 'string',
                },
                'custom_field1': {'title': 'Custom Field1', 'type': 'string'},
                'custom_field2': {
                    'default': 1,
                    'title': 'Custom Field2',
                    'type': 'integer',
                },
                'custom_field3': {
                    'default': '',
                    'title': 'Custom Field3',
                    'type': 'string',
                },
            },
            'required': ['title', 'start_date', 'end_date', 'custom_field1'],
            'title': 'Event6Schema',
            'type': 'object',
        }

    def test_invalid_fields_inputs(self):
        with pytest.raises(ConfigError):

            class Event1Schema(ModelSchema):
                class Config:
                    model = Event
                    include = ['xy', 'yz']

        with pytest.raises(ConfigError):

            class Event2Schema(ModelSchema):
                class Config:
                    model = Event
                    exclude = ['xy', 'yz']

        with pytest.raises(ConfigError):

            class Event3Schema(ModelSchema):
                class Config:
                    model = Event
                    optional = ['xy', 'yz']

    def test_factory_functions(self):
        event_schema = SchemaFactory.create_schema(model=Event, name='EventSchema')
        assert event_schema.model_json_schema() == {
            'properties': {
                'id': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Id',
                },
                'title': {
                    'description': '',
                    'maxLength': 100,
                    'title': 'Title',
                    'type': 'string',
                },
                'category': {
                    'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                    'default': None,
                    'description': '',
                    'title': 'Category',
                },
                'start_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'Start Date',
                    'type': 'string',
                },
                'end_date': {
                    'description': '',
                    'format': 'date',
                    'title': 'End Date',
                    'type': 'string',
                },
            },
            'required': ['title', 'start_date', 'end_date'],
            'title': 'EventSchema',
            'type': 'object',
        }

    def get_new_event(self, title):
        event = Event(title=title)
        event.save()
        return event

    @pytest.mark.django_db
    def test_getter_functions(self):
        class EventSchema(ModelSchema):
            class Config:
                model = Event
                include = ['title', 'category', 'id']

        event = self.get_new_event(title='PyConf')
        json_event = EventSchema.from_orm(event)

        assert json_event.model_dump() == {'id': 1, 'title': 'PyConf', 'category': None}
        json_event.title = 'PyConf Updated'

        json_event.apply_to_model(event)
        assert event.title == 'PyConf Updated'

    def test_abstract_model_schema_does_not_raise_exception_for_incomplete_configuration(
        self,
    ):
        with pytest.raises(Exception, match="Invalid Configuration. 'model' is required"):

            class AbstractModel(ModelSchema):
                class Config:
                    orm_mode = True

        class AbstractBaseModelSchema(ModelSchema):
            class Config:
                ninja_schema_abstract = True

    def test_model_validator_with_new_model_config(self):
        from pydantic import ConfigDict

        class EventWithNewModelConfig(ModelSchema):
            model_config = ConfigDict(
                model=Event,
                include=[
                    'title',
                    'start_date',
                ],
            )

            @pydantic.field_validator('title')
            def validate_title(cls, value):
                return f'{value} - value cleaned'

        event = EventWithNewModelConfig(start_date='2021-06-12', title='PyConf 2021')
        assert 'value cleaned' in event.title

    @pytest.mark.django_db
    def test_schema_with_mixin_generic_class(self):
        """
        Test that a schema with a generic mixin class works correctly.
        """

        class GenericMixin(t.Generic[T]):
            def save(self, instance: t.Optional[T] = None) -> T:
                """
                Save the model instance and return it.
                """
                if instance:
                    self.apply_to_model(instance, **self.model_dump())
                    instance.save()
                    return instance

                instance = self.Config.model(**self.model_dump())
                instance.save()
                return instance

        class BaseModelSchema(ModelSchema, GenericMixin[T]): ...

        class EventGenericSchema(BaseModelSchema[Event]):
            class Config:
                model = Event
                include = ('title',)

        event = EventGenericSchema(title='PyConf 2021')
        assert event.title == 'PyConf 2021'

        instance_event = event.save()
        assert isinstance(instance_event, Event)
        assert instance_event.title == 'PyConf 2021'
