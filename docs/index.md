# Django Modern Schemas

Declarative [Pydantic v2](https://docs.pydantic.dev/latest/) schemas generated from Django models.

Django Modern Schemas reads a model's field definitions — types, `null`, `blank`,
`default`, `choices`, `max_length` — and builds a real Pydantic model from them.
You get validation, serialization and JSON Schema without restating the field
definitions you already wrote in `models.py`.

[Get started](getting-started.md){ .md-button .md-button--primary }
[Read the overview](overview.md){ .md-button }

!!! info "Every example on this site is executed"

    Code blocks written as a console transcript (`>>>`) are run by the test suite
    on every commit, and the output shown is the output the library produced.
    See [How these docs are tested](project/testing.md).

## Installation

```bash
pip install django-modern-schemas
```

Requires Python 3.10+, Django 3.2+ and Pydantic 2.13+. Nothing needs to be added
to `INSTALLED_APPS` — the library is imported, not installed as an app.

## A first schema

Given an ordinary Django model:

```python title="models.py"
--8<-- "examples/models.py:event-model"
```

Declare a schema that names the model in a nested `Config` class:

```pycon
>>> class EventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['id', 'title']

```

The result is a Pydantic model. It validates a Django instance directly:

```pycon
>>> event = models.Event(id=1, title='DjangoCon')
>>> EventSchema.model_validate(event).model_dump()
{'id': 1, 'title': 'DjangoCon'}

```

It rejects input the database would reject:

```pycon
>>> EventSchema.model_validate({'id': 'not-an-integer', 'title': 'DjangoCon'})
Traceback (most recent call last):
    ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for EventSchema...

```

And it describes itself as JSON Schema:

```pycon
>>> print(json.dumps(EventSchema.model_json_schema()['properties']['title'], indent=2))
{
  "description": "",
  "maxLength": 100,
  "title": "Title",
  "type": "string"
}

```

`max_length=100` on the Django field became `maxLength: 100` in the JSON Schema.
Constraints are carried across rather than re-declared.

## What you get

<div class="dms-grid" markdown>

<div class="dms-card" markdown>
### Generated fields
Django field types, `null`/`blank`, defaults and `choices` become Pydantic
annotations. See the [field reference](reference/fields.md).
</div>

<div class="dms-card" markdown>
### Explicit relations
Relations serialize as primary keys by default, or as nested schemas when you
ask for them with `depth`. See [Relations](guides/relations.md).
</div>

<div class="dms-card" markdown>
### Renamed and computed values
`Source` reads a dotted attribute path; `MethodSource` calls a model method.
See [Source and MethodSource](guides/source.md).
</div>

<div class="dms-card" markdown>
### Persistence
`create()`, `update()` and `save()` write validated data back through the ORM.
See [Persistence](guides/persistence.md).
</div>

</div>

## Where to go next

| If you want to | Read |
| --- | --- |
| Understand the pieces and their boundaries | [Overview](overview.md) |
| Follow a worked tutorial from an empty app | [Getting Started](getting-started.md) |
| Configure `fields`, `exclude`, `optional`, `depth` | [ModelSchema](guides/model-schema.md) |
| Look up how a Django field is converted | [Field reference](reference/fields.md) |
| Build schemas at runtime | [SchemaFactory](guides/schema-factory.md) |

## Scope

This library builds schemas from models and writes flat data back. It
deliberately does not plan queries for you, and it does not perform nested
writes. Those boundaries are stated in full under
[Overview → Boundaries](overview.md#boundaries).

## Credits

Django Modern Schemas is maintained by [Open Byte](https://github.com/open-byte).
It builds on the design of Ninja Schema by Tochukwu (@eadwinCode) — see
[Credits and Stewardship](project/credits.md).
