from datetime import date
from typing import Annotated

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from pydantic import ValidationError
from tests.models import Category as DjangoCategory
from tests.models import Day as DjangoDay
from tests.models import Event as DjangoEvent
from tests.models import Person as DjangoPerson
from tests.models import Question as DjangoQuestion
from tests.models import Week as DjangoWeek

from django_modern_schemas import MethodSource, ModelSchema, Source


def test_source_normalizes_and_splits_a_path():
    source = Source(' category.name ')

    assert source.path == 'category.name'
    assert source.parts == ('category', 'name')


@pytest.mark.parametrize(
    'path',
    ['', '   ', '.category', 'category.', 'category..name', 'category.questions[0].name', 'category.name()'],
)
def test_source_rejects_invalid_paths(path: str):
    with pytest.raises(ValueError, match='Source path'):
        Source(path)


def test_model_schema_resolves_source_from_a_one_to_one_relation():
    class EventSchema(ModelSchema):
        category_name: Annotated[str | None, Source('category.name')]
        some_thing: Annotated[str, MethodSource('get_some_thing')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=DjangoCategory(name='Python'))
    schema = EventSchema.model_validate(event)

    assert schema.category_name == 'Python'
    assert schema.some_thing == 'Hello World'


def test_model_schema_returns_none_for_a_none_source_intermediate_attribute():
    class EventSchema(ModelSchema):
        category_name: Annotated[str | None, Source('category.name')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=None)

    assert EventSchema.model_validate(event).category_name is None


def test_model_schema_raises_a_descriptive_error_for_a_missing_source_attribute():
    class EventSchema(ModelSchema):
        unknown: Annotated[str, Source('unknown')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=None)

    with pytest.raises(ValidationError, match="attribute 'unknown' was not found"):
        EventSchema.model_validate(event)


def test_model_schema_resolves_source_from_a_nested_mapping():
    class EventSchema(ModelSchema):
        category_name: Annotated[str, Source('category.name')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    schema = EventSchema.model_validate({'title': 'DjangoCon', 'category': {'name': 'Python'}})

    assert schema.category_name == 'Python'


def test_model_schema_prefers_an_explicit_mapping_value_over_source_resolution():
    class EventSchema(ModelSchema):
        category_name: Annotated[str, Source('category.name')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    schema = EventSchema.model_validate({'title': 'DjangoCon', 'category_name': 'Provided value'})

    assert schema.category_name == 'Provided value'


def test_model_schema_resolves_an_explicit_model_method():
    class EventSchema(ModelSchema):
        display_title: Annotated[str, MethodSource('display_title')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=None)

    assert EventSchema.model_validate(event).display_title == 'Event: DjangoCon'


def test_model_schema_resolves_a_method_inherited_from_abstract_user():
    class PersonSchema(ModelSchema):
        full_name: Annotated[str, MethodSource('get_full_name')]

        class Config:
            model = DjangoPerson
            fields = ['username']

    person = DjangoPerson(username='ada', first_name='Ada', last_name='Lovelace')

    assert PersonSchema.model_validate(person).full_name == 'Ada Lovelace'


def test_model_schema_resolves_an_inherited_method_that_returns_an_empty_value():
    class PersonSchema(ModelSchema):
        full_name: Annotated[str, MethodSource('get_full_name')]

        class Config:
            model = DjangoPerson
            fields = ['username']

    person = DjangoPerson(username='ada')

    assert PersonSchema.model_validate(person).full_name == ''


def test_model_schema_resolves_a_source_path_through_a_relation_to_an_abstract_user_field():
    class PersonSchema(ModelSchema):
        short_name: Annotated[str, MethodSource('get_short_name')]
        email_domain: Annotated[str, Source('email')]

        class Config:
            model = DjangoPerson
            fields = ['username']

    person = DjangoPerson(username='ada', first_name='Ada', email='ada@example.com')
    schema = PersonSchema.model_validate(person)

    assert schema.short_name == 'Ada'
    assert schema.email_domain == 'ada@example.com'


def test_model_schema_rejects_a_method_source_on_a_non_callable_attribute():
    class EventSchema(ModelSchema):
        bad_method: Annotated[str, MethodSource('title')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=None)

    with pytest.raises(ValidationError, match="method 'title' is not callable"):
        EventSchema.model_validate(event)


def test_model_schema_rejects_a_method_source_that_requires_arguments():
    class EventSchema(ModelSchema):
        formatted_title: Annotated[str, MethodSource('format_title')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=None)

    with pytest.raises(ValidationError, match='methods cannot require arguments'):
        EventSchema.model_validate(event)


@pytest.mark.django_db
def test_model_schema_resolves_a_reverse_one_to_one_relation():
    category = DjangoCategory.objects.create(name='Python', start_date=date.today(), end_date=date.today())
    DjangoEvent.objects.create(title='DjangoCon', category=category)
    category = DjangoCategory.objects.select_related('event').get(pk=category.pk)

    class CategorySchema(ModelSchema):
        event_title: Annotated[str, Source('event.title')]

        class Config:
            model = DjangoCategory
            fields = ['name']

    assert CategorySchema.model_validate(category).event_title == 'DjangoCon'


@pytest.mark.django_db
def test_model_schema_resolves_a_terminal_reverse_foreign_key_as_a_list():
    category = DjangoCategory.objects.create(name='Python', start_date=date.today(), end_date=date.today())
    DjangoQuestion.objects.create(text='What is Django?', category=category)
    DjangoQuestion.objects.create(text='What is Pydantic?', category=category)
    category = DjangoCategory.objects.prefetch_related('questions').get(pk=category.pk)

    class QuestionSchema(ModelSchema):
        class Config:
            model = DjangoQuestion
            fields = ['text']

    class CategorySchema(ModelSchema):
        questions: Annotated[list[QuestionSchema], Source('questions')]

        class Config:
            model = DjangoCategory
            fields = ['name']

    with CaptureQueriesContext(connection) as queries:
        schema = CategorySchema.model_validate(category)

    assert not queries
    assert [question.model_dump()['text'] for question in schema.questions] == [
        'What is Django?',
        'What is Pydantic?',
    ]


@pytest.mark.django_db
def test_model_schema_rejects_traversing_a_reverse_foreign_key_collection():
    category = DjangoCategory.objects.create(name='Python', start_date=date.today(), end_date=date.today())
    DjangoQuestion.objects.create(text='What is Django?', category=category)

    class CategorySchema(ModelSchema):
        question_text: Annotated[str, Source('questions.text')]

        class Config:
            model = DjangoCategory
            fields = ['name']

    with pytest.raises(ValidationError, match='resolves to a collection'):
        CategorySchema.model_validate(category)


@pytest.mark.django_db
def test_model_schema_rejects_a_many_to_many_source():
    day = DjangoDay.objects.create(name='Monday')
    week = DjangoWeek.objects.create(name='Week 1')
    week.days.add(day)

    class DaySchema(ModelSchema):
        class Config:
            model = DjangoDay
            fields = ['name']

    class WeekSchema(ModelSchema):
        days: Annotated[list[DaySchema], Source('days')]

        class Config:
            model = DjangoWeek
            fields = ['name']

    with pytest.raises(ValidationError, match='only supports reverse ForeignKey collections'):
        WeekSchema.model_validate(week)


@pytest.mark.django_db
def test_model_schema_does_not_persist_source_fields():
    class EventSchema(ModelSchema):
        category_name: Annotated[str, Source('category.name')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = EventSchema.model_validate({'title': 'DjangoCon', 'category_name': 'Python'}).create()

    assert event.title == 'DjangoCon'


@pytest.mark.django_db
def test_model_schema_does_not_update_a_source_field_that_matches_a_model_attribute():
    category = DjangoCategory.objects.create(name='Python', start_date=date.today(), end_date=date.today())
    event = DjangoEvent.objects.create(title='DjangoCon', category=category)

    class EventSchema(ModelSchema):
        title: Annotated[str, Source('category.name')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    schema = EventSchema.model_validate(event)
    schema.update(event)
    event.refresh_from_db()

    assert schema.title == 'Python'
    assert event.title == 'DjangoCon'
