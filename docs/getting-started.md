# Getting Started

A worked tutorial: from a Django model to a validated, serialized, documented
boundary. Every transcript below is executed by the test suite.

## Install

=== "uv"

    ```bash
    uv add django-modern-schemas
    ```

=== "pip"

    ```bash
    pip install django-modern-schemas
    ```

| Requirement | Version |
| --- | --- |
| Python | 3.10 or newer |
| Django | 3.2 or newer |
| Pydantic | 2.13 or newer |

Install the Pydantic extras that match the Django fields you use:

```bash
pip install "pydantic[email]"     # EmailField -> EmailStr
pip install "pydantic[timezone]"  # timezone-aware datetimes
```

You do **not** add anything to `INSTALLED_APPS`. Schemas are ordinary Python
classes.

## The models used in this tutorial

```python title="models.py"
--8<-- "examples/models.py:category-model"

--8<-- "examples/models.py:event-model"
```

## Step 1 — Declare a schema

A `ModelSchema` names its Django model in a nested `Config` class. Here we
expose everything except the relation, which the [Relations](guides/relations.md)
guide covers separately.

```pycon
>>> class EventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         exclude = ['category']

```

The generated Pydantic fields:

```pycon
>>> list(EventSchema.model_fields)
['id', 'title']

```

`title` is required, and `id` is not:

```pycon
>>> EventSchema.model_fields['title'].is_required()
True
>>> EventSchema.model_fields['id'].is_required()
False

```

!!! note "Why the primary key is optional here"

    A schema that you use for both input and output cannot demand a pk that does
    not exist yet, so the pk is made optional automatically — **unless you name
    it in `fields` yourself**, which reads as a deliberate request for it:

    ```pycon
    >>> class ExplicitPkSchema(ModelSchema):
    ...     class Config:
    ...         model = models.Event
    ...         fields = ['id', 'title']
    >>> ExplicitPkSchema.model_fields['id'].is_required()
    True

    ```

    The full rule is in
    [ModelSchema → The primary key rule](guides/model-schema.md#the-primary-key-rule).

## Step 2 — Validate incoming data

```pycon
>>> schema = EventSchema.model_validate({'title': 'DjangoCon'})
>>> schema.title
'DjangoCon'
>>> schema.id is None
True

```

Constraints come from the Django field, so a payload that would not fit the
column is caught before any SQL runs. `ValidationError.errors()` is already in
the shape of a JSON error response:

```pycon
>>> from pydantic import ValidationError
>>> try:
...     EventSchema.model_validate({'title': 'x' * 200})
... except ValidationError as error:
...     print(error.errors()[0]['type'], error.errors()[0]['ctx'])
string_too_long {'max_length': 100}

```

The rule that fired is `max_length=100`, which the schema never restated.

## Step 3 — Serialize a model instance

The same schema reads a Django instance, because `from_attributes` is enabled:

```pycon
>>> event = models.Event(id=7, title='DjangoCon')
>>> EventSchema.model_validate(event).model_dump()
{'id': 7, 'title': 'DjangoCon'}

```

For a JSON response, use Pydantic's JSON mode:

```pycon
>>> EventSchema.model_validate(event).model_dump_json()
'{"id":7,"title":"DjangoCon"}'

```

## Step 4 — Persist validated data

`create()` writes the flat fields through the model's default manager:

```pycon
>>> created = EventSchema.model_validate({'title': 'PyCon'}).create()
>>> created.pk is not None
True
>>> created.title
'PyCon'

```

`update()` writes onto an existing instance and saves it:

```pycon
>>> _ = EventSchema.model_validate({'title': 'PyCon US'}).update(created)
>>> models.Event.objects.get(pk=created.pk).title
'PyCon US'

```

See [Persistence](guides/persistence.md) for partial updates, `save()`, and the
rules around nested schemas.

## Step 5 — Publish the contract

`model_json_schema()` returns a JSON Schema you can hand to OpenAPI tooling:

```pycon
>>> print(json.dumps(EventSchema.model_json_schema(), indent=2))
{
  "properties": {
    "id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "",
      "title": "Id"
    },
    "title": {
      "description": "",
      "maxLength": 100,
      "title": "Title",
      "type": "string"
    }
  },
  "required": [
    "title"
  ],
  "title": "EventSchema",
  "type": "object"
}

```

## Using it in a Django view

Schemas are plain Pydantic models, so they drop into any view layer:

```python title="views.py"
import json

from django.http import HttpRequest, JsonResponse
from pydantic import ValidationError

from .models import Event
from .schemas import EventSchema


def create_event(request: HttpRequest) -> JsonResponse:
    try:
        schema = EventSchema.model_validate(json.loads(request.body))
    except ValidationError as error:
        return JsonResponse({'errors': error.errors()}, status=400)

    event = schema.create()
    return JsonResponse(EventSchema.model_validate(event).model_dump(), status=201)


def list_events(request: HttpRequest) -> JsonResponse:
    events = [EventSchema.model_validate(event).model_dump() for event in Event.objects.all()]
    return JsonResponse({'results': events})
```

## Next steps

- [ModelSchema](guides/model-schema.md) — `fields`, `exclude`, `optional`, `depth`
- [Field reference](reference/fields.md) — what each Django field becomes
- [Source and MethodSource](guides/source.md) — renamed and computed fields
- [Relations](guides/relations.md) — foreign keys, many-to-many, nesting
