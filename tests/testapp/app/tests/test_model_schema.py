import json
import typing as t

import pydantic
import pytest
from django.db.models import Model as DjangoModel
from tests.models import Category, Day, Event, Week

from django_modern_schemas import MethodSource, ModelSchema, SchemaFactory
from django_modern_schemas.errors import ConfigError

T = t.TypeVar('T', bound=DjangoModel)


class TestModelSchema:
    def test_schema_includes_method_source_field(self):
        class EventMethodSourceSchema(ModelSchema):
            display_title: t.Annotated[str, MethodSource('display_title')]

            class Config:
                model = Event
                fields = ['title']

        assert list(EventMethodSourceSchema.model_fields) == ['title', 'display_title']
        assert EventMethodSourceSchema.model_fields['display_title'].metadata == [MethodSource('display_title')]
        assert EventMethodSourceSchema.model_json_schema()['properties']['display_title'] == {
            'title': 'Display Title',
            'type': 'string',
        }

    def test_schema_fields(self):
        class EventSchema(ModelSchema):
            class Config:
                model = Event
                fields = '__all__'

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
                fields = ['title', 'start_date', 'end_date']

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
                fields = '__all__'
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
                fields = '__all__'
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
                fields = ['id', 'title', 'start_date']
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
                    fields = ['xy', 'yz']

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

        event_fields_schema = SchemaFactory.create_schema(
            model=Event,
            name='EventFieldsSchema',
            fields=['title'],
            skip_registry=True,
        )
        assert event_fields_schema is not None
        assert list(event_fields_schema.model_fields) == ['title']

    def get_new_event(self, title):
        event = Event(title=title)
        event.save()
        return event

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
                fields=[
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
    def test_save_data(self):
        class EventSchema(ModelSchema[Event]):
            class Config:
                model = Event
                fields = ['title']

        event_schema = EventSchema.model_validate({'title': 'Test Event'})

        saved_event = event_schema.save()
        assert isinstance(saved_event, Event)
        assert saved_event.title == 'Test Event'

        updated_event_schema = EventSchema.model_validate(saved_event)
        updated_event_schema.title = 'Updated Test Event'
        updated_event = updated_event_schema.save()
        assert updated_event.title == 'Updated Test Event'

    @pytest.mark.django_db
    def test_save_data_with_fk(self):
        class EventSchema(ModelSchema[Event]):
            class Config:
                model = Event
                fields = ['title', 'category']

        category = EventSchema.Config.model._meta.get_field('category').related_model.objects.create(
            name='Test Category', start_date='2021-06-12', end_date='2021-06-13'
        )

        event_schema = EventSchema.model_validate({'title': 'Test Event', 'category': category.id})

        saved_event = event_schema.save()
        assert isinstance(saved_event, Event)
        assert saved_event.title == 'Test Event'
        assert saved_event.category == category

    @pytest.mark.django_db
    def test_dump_returns_the_related_pk_after_saving_a_category(self):
        class EventSchema(ModelSchema[Event]):
            class Config:
                model = Event
                fields = ['title', 'category']

        category = Category.objects.create(name='Test Category', start_date='2021-06-12', end_date='2021-06-13')

        event_schema = EventSchema.model_validate({'title': 'Test Event', 'category': category.id})
        saved_event = event_schema.save()

        assert saved_event.category_id == category.id
        assert Event.objects.get(pk=saved_event.pk).category_id == category.id

        dumped = event_schema.model_dump()
        assert dumped['category'] == category.id

        # The ORM is written through the `_id` attribute name, not the field name.
        assert event_schema.model_dump(by_alias=True)['category'] == category.id
        assert json.loads(event_schema.model_dump_json())['category'] == category.id

    @pytest.mark.django_db
    def test_create_assigns_a_foreign_key_given_its_pk(self):
        class EventSchema(ModelSchema[Event]):
            class Config:
                model = Event
                fields = ['title', 'category']

        category = Category.objects.create(name='Python', start_date='2021-06-12', end_date='2021-06-13')

        created = EventSchema.model_validate({'title': 'DjangoCon', 'category': category.id}).create()

        assert created.category_id == category.id

    @pytest.mark.django_db
    def test_update_reassigns_a_foreign_key_given_its_pk(self):
        class EventSchema(ModelSchema[Event]):
            class Config:
                model = Event
                fields = ['title', 'category']

        first = Category.objects.create(name='Python', start_date='2021-06-12', end_date='2021-06-13')
        second = Category.objects.create(name='Rust', start_date='2021-06-12', end_date='2021-06-13')
        event = Event.objects.create(title='DjangoCon', category=first)

        EventSchema.model_validate({'title': 'RustConf', 'category': second.id}).update(event)

        refreshed = Event.objects.get(pk=event.pk)
        assert refreshed.title == 'RustConf'
        assert refreshed.category_id == second.id

    @pytest.mark.django_db
    def test_create_assigns_many_to_many_after_the_instance_exists(self):
        class WeekSchema(ModelSchema[Week]):
            class Config:
                model = Week
                fields = ['name', 'days']

        monday = Day.objects.create(name='Monday')
        tuesday = Day.objects.create(name='Tuesday')

        week = WeekSchema.model_validate({'name': 'Week 1', 'days': [monday.id, tuesday.id]}).create()

        assert sorted(day.id for day in week.days.all()) == sorted([monday.id, tuesday.id])

    @pytest.mark.django_db
    def test_update_replaces_many_to_many_values(self):
        class WeekSchema(ModelSchema[Week]):
            class Config:
                model = Week
                fields = ['name', 'days']

        monday = Day.objects.create(name='Monday')
        tuesday = Day.objects.create(name='Tuesday')
        week = Week.objects.create(name='Week 1')
        week.days.add(monday)

        WeekSchema.model_validate({'name': 'Week 1', 'days': [tuesday.id]}).update(week)

        assert [day.id for day in Week.objects.get(pk=week.pk).days.all()] == [tuesday.id]
