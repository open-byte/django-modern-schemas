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
DOCS_DIRECTORY = Path(__file__).parent.parent / 'docs'
WORKFLOWS_DIRECTORY = Path(__file__).parent.parent / '.github' / 'workflows'
TUTORIAL_SOURCES = {
    'basic_schema': 'basic_schema.md',
    'model_schema': 'model_schema.md',
    'schema_factory': 'schema_factory.md',
    'choices': 'choices.md',
    'source': 'source.md',
    'relations': 'relations.md',
    'persistence': 'persistence.md',
}
MATERIAL_GUIDES = {
    'basic_schema': 'guides/basic-schema.md',
    'model_schema': 'guides/model-schema.md',
    'schema_factory': 'guides/schema-factory.md',
    'choices': 'guides/choices.md',
    'source': 'guides/source.md',
    'relations': 'guides/relations.md',
    'persistence': 'guides/persistence.md',
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

    assert '](examples/README.md)' in project_readme
    assert '](docs/index.md)' in project_readme


@pytest.mark.parametrize(('example_name', 'guide_name'), MATERIAL_GUIDES.items())
def test_material_guide_embeds_its_tested_example(example_name: str, guide_name: str):
    guide = (DOCS_DIRECTORY / guide_name).read_text()

    assert f'--8<-- "examples/{example_name}.py"' in guide


def test_material_credits_recognize_open_byte_and_original_creator():
    credits = (DOCS_DIRECTORY / 'project' / 'credits.md').read_text()

    assert 'Open Byte' in credits
    assert 'Tochukwu (@eadwinCode)' in credits
    assert 'Ninja Schema' in credits


def test_overview_introduces_the_core_apis_and_boundaries():
    overview = (DOCS_DIRECTORY / 'overview.md').read_text()
    navigation = (DOCS_DIRECTORY.parent / 'mkdocs.yml').read_text()

    for api in ('`Schema`', '`ModelSchema`', '`SchemaFactory`', '`Source`', '`MethodSource`'):
        assert api in overview

    assert 'Nested writes are application-specific' in overview
    assert 'select_related()' in overview
    assert '- Overview: overview.md' in navigation


def test_github_pages_deployment_is_documented_and_configured():
    workflow = (WORKFLOWS_DIRECTORY / 'deploy-docs.yml').read_text()
    publishing_guide = (DOCS_DIRECTORY / 'project' / 'publishing.md').read_text()

    assert 'actions/upload-pages-artifact@v3' in workflow
    assert 'actions/deploy-pages@v4' in workflow
    assert 'mkdocs build --strict' in workflow
    assert 'GitHub Actions' in publishing_guide
    assert 'Settings' in publishing_guide


def test_choices_material_guide_embeds_the_django_model_definition():
    guide = (DOCS_DIRECTORY / 'guides' / 'choices.md').read_text()
    models = (EXAMPLES_DIRECTORY / 'models.py').read_text()

    assert '--8<-- "examples/models.py:student-choices"' in guide
    assert '# --8<-- [start:student-choices]' in models
    assert 'choices=SEMESTER_CHOICES' in models


def test_persistence_guides_explain_nested_model_customization():
    material_guide = (DOCS_DIRECTORY / 'guides' / 'persistence.md').read_text()
    example_guide = (EXAMPLES_DIRECTORY / 'persistence.md').read_text()

    for guide in (material_guide, example_guide):
        assert 'override' in guide
        assert '`create()`' in guide
        assert '`update()`' in guide
        assert 'NotImplementedError' in guide
