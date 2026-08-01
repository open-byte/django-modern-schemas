from pathlib import Path

import pytest
from django.db import connection
from examples.basic_schema import Member, Team, serialize_member
from examples.choices import validate_semester
from examples.model_schema import (
    EventPatchSchema,
    EventSummarySchema,
    EventWithCategorySchema,
    EventWithoutCategorySchema,
    serialize_event,
)
from examples.models import Category, Day, Event, Question, Week
from examples.persistence import create_event, rename_event
from examples.relations import serialize_week
from examples.schema_factory import build_event_title_schema
from examples.schema_factory import serialize_event as serialize_factory_event
from examples.source import (
    resolve_category_name,
    resolve_mapping_category_name,
    serialize_category,
)
from examples.source import (
    serialize_event as serialize_source_event,
)
from pydantic import ValidationError

EXAMPLES_DIRECTORY = Path(__file__).parent.parent / 'examples'
TUTORIAL_SOURCES = {
    'basic_schema': 'basic_schema.md',
    'model_schema': 'model_schema.md',
    'schema_factory': 'schema_factory.md',
    'choices': 'choices.md',
    'source': 'source.md',
    'relations': 'relations.md',
    'persistence': 'persistence.md',
}


def test_basic_schema_example():
    member = Member(name='Ada', team=Team(name='Platform'))

    assert serialize_member(member) == {
        'name': 'Ada',
        'team': {'name': 'Platform'},
    }


def test_model_schema_example():
    event = Event(title='DjangoCon', category=Category(name='Python'))

    assert serialize_event(event) == {'title': 'DjangoCon'}
    assert list(EventSummarySchema.model_fields) == ['title']
    assert EventPatchSchema.model_fields['title'].is_required() is False
    assert 'category' not in EventWithoutCategorySchema.model_fields
    assert 'Category' in EventWithCategorySchema.model_json_schema()['$defs']


def test_schema_factory_example():
    schema = build_event_title_schema()
    event = Event(title='DjangoCon')

    assert list(schema.model_fields) == ['title']
    assert serialize_factory_event(event) == {'title': 'DjangoCon'}


def test_choices_example():
    assert validate_semester('1')['semester'] == '1'

    with pytest.raises(ValidationError):
        validate_semester('invalid')


def test_source_example():
    event = Event(title='DjangoCon', category=Category(name='Python'))

    assert resolve_category_name(event) == 'Python'
    assert resolve_mapping_category_name({'category': {'name': 'Python'}}) == 'Python'
    assert serialize_source_event(event) == {
        'title': 'DjangoCon',
        'category_name': 'Python',
        'display_title': 'Event: DjangoCon',
    }


@pytest.mark.django_db(transaction=True)
def test_source_collection_example():
    category = Category.objects.create(name='Python')
    Question.objects.create(text='What is Django?', category=category)
    Question.objects.create(text='What is Pydantic?', category=category)
    category = Category.objects.prefetch_related('questions').get(pk=category.pk)

    assert serialize_category(category) == {
        'name': 'Python',
        'questions': [
            {'text': 'What is Django?'},
            {'text': 'What is Pydantic?'},
        ],
    }


@pytest.mark.django_db(transaction=True)
def test_relations_example():
    monday = Day.objects.create(name='Monday')
    tuesday = Day.objects.create(name='Tuesday')
    week = Week.objects.create(name='Week 1')
    week.days.add(monday, tuesday)
    week = Week.objects.prefetch_related('days').get(pk=week.pk)

    data = serialize_week(week)

    assert data['name'] == 'Week 1'
    assert [day['name'] for day in data['days']] == ['Monday', 'Tuesday']


@pytest.mark.django_db(transaction=True)
def test_persistence_example():
    event = create_event('DjangoCon')
    updated_event = rename_event(event, 'PyCon')

    assert updated_event.pk == event.pk
    assert Event.objects.get(pk=event.pk).title == 'PyCon'


@pytest.mark.parametrize(('example_name', 'tutorial_name'), TUTORIAL_SOURCES.items())
def test_tutorial_links_to_its_example_source(example_name: str, tutorial_name: str):
    tutorial = (EXAMPLES_DIRECTORY / tutorial_name).read_text()

    assert f'[{example_name}.py]({example_name}.py)' in tutorial
    assert (EXAMPLES_DIRECTORY / f'{example_name}.py').is_file()


def test_example_indexes_link_to_every_tutorial():
    examples_index = (EXAMPLES_DIRECTORY / 'README.md').read_text()
    project_readme = (EXAMPLES_DIRECTORY.parent / 'README.md').read_text()

    for tutorial_name in TUTORIAL_SOURCES.values():
        assert f']({tutorial_name})' in examples_index
        assert f'](examples/{tutorial_name})' in project_readme
