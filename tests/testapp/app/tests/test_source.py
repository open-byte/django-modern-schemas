from datetime import date
from typing import Annotated

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from pydantic import ValidationError
from tests.models import Category as DjangoCategory
from tests.models import Day as DjangoDay
from tests.models import Event as DjangoEvent
from tests.models import Question as DjangoQuestion
from tests.models import Week as DjangoWeek

from django_modern_schemas import MethodSource, ModelSchema, Source, SourceResolutionError, SourceResolver


class Category:
    def __init__(self, name: str | None) -> None:
        self.name = name


class Event:
    def __init__(self, title: str, category: Category | None) -> None:
        self.title = title
        self.category = category

    def display_title(self) -> str:
        return self.title.upper()

    def format_title(self, prefix: str) -> str:
        return f'{prefix}: {self.title}'


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


def test_resolver_reads_a_nested_attribute():
    event = Event(title='DjangoCon', category=Category(name='Python'))

    assert SourceResolver().resolve(event, Source('category.name')) == 'Python'


def test_resolver_reads_a_nested_mapping():
    data = {'category': {'name': 'Python'}}

    assert SourceResolver().resolve(data, Source('category.name')) == 'Python'


def test_resolver_returns_none_for_a_none_intermediate_attribute():
    event = Event(title='DjangoCon', category=None)

    assert SourceResolver().resolve(event, Source('category.name')) is None


def test_resolver_raises_a_descriptive_error_for_a_missing_attribute():
    event = Event(title='DjangoCon', category=None)

    with pytest.raises(SourceResolutionError, match="attribute 'unknown' was not found"):
        SourceResolver().resolve(event, Source('unknown'))


def test_resolver_invokes_an_explicit_model_method():
    event = Event(title='DjangoCon', category=None)

    assert SourceResolver().resolve(event, MethodSource('display_title')) == 'DJANGOCON'


def test_method_source_rejects_a_non_callable_attribute():
    event = Event(title='DjangoCon', category=None)

    with pytest.raises(SourceResolutionError, match="method 'title' is not callable"):
        SourceResolver().resolve(event, MethodSource('title'))


def test_method_source_rejects_a_method_that_requires_arguments():
    event = Event(title='DjangoCon', category=None)

    with pytest.raises(SourceResolutionError, match='methods cannot require arguments'):
        SourceResolver().resolve(event, MethodSource('format_title'))


def test_model_schema_resolves_source_from_a_one_to_one_relation():
    class EventSchema(ModelSchema):
        category_name: Annotated[str | None, Source('category.name')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=DjangoCategory(name='Python'))

    assert EventSchema.model_validate(event).category_name == 'Python'


def test_model_schema_returns_none_for_a_none_source_intermediate_attribute():
    class EventSchema(ModelSchema):
        category_name: Annotated[str | None, Source('category.name')]

        class Config:
            model = DjangoEvent
            fields = ['title']

    event = DjangoEvent(title='DjangoCon', category=None)

    assert EventSchema.model_validate(event).category_name is None


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
