# SchemaFactory

`SchemaFactory.create_schema()` builds a `ModelSchema` at runtime. Use it when
the shape is decided by data rather than written in a class body — a
`?fields=` query parameter, a permission-dependent projection, an admin tool.

For a shape you know at import time, declare a
[`ModelSchema`](model-schema.md) — it is clearer and type-checkable.

## Building a schema

```pycon
>>> EventTitleSchema = SchemaFactory.create_schema(
...     models.Event,
...     name='EventTitleSchema',
...     fields=['title'],
...     skip_registry=True,
... )
>>> EventTitleSchema.__name__
'EventTitleSchema'
>>> list(EventTitleSchema.model_fields)
['title']

```

The result is an ordinary `ModelSchema` subclass:

```pycon
>>> issubclass(EventTitleSchema, ModelSchema)
True
>>> EventTitleSchema.model_validate(models.Event(title='DjangoCon')).model_dump()
{'title': 'DjangoCon'}

```

## Parameters

| Parameter | Type | Default | Purpose |
| --- | --- | --- | --- |
| `model` | Django model | — | **Required**, positional. |
| `name` | `str` | model class name | Name of the generated class. |
| `fields` | `list[str]` | all fields | Allow-list. |
| `exclude` | `list[str]` | `None` | Deny-list. |
| `optional_fields` | `list[str]` or `'__all__'` | `None` | Fields made non-required. |
| `depth` | `int` | `0` | Relation nesting depth. |
| `skip_registry` | `bool` | `False` | Do not cache or reuse from the registry. |
| `registry` | `SchemaRegister` | global registry | Registry to use. |

Note the name difference: the factory argument is `optional_fields`, while the
`Config` option is `optional`.

```pycon
>>> PatchSchema = SchemaFactory.create_schema(
...     models.Event,
...     name='EventPatchSchema',
...     fields=['title'],
...     optional_fields=['title'],
...     skip_registry=True,
... )
>>> PatchSchema.model_fields['title'].is_required()
False

```

`fields` and `exclude` are mutually exclusive here too:

```pycon
>>> SchemaFactory.create_schema(
...     models.Event, fields=['title'], exclude=['category'], skip_registry=True
... )
Traceback (most recent call last):
    ...
django_modern_schemas.errors.ConfigError: Only one of 'fields' or 'exclude' should be set.

```

## The registry

Generated schemas are cached **per model** in a global registry. That is what
lets nested schemas resolve when you use `depth`, but it has a consequence worth
understanding.

The first call for a model registers a schema:

```pycon
>>> first = SchemaFactory.create_schema(models.Day, name='DayNameSchema', fields=['name'])
>>> list(first.model_fields)
['name']

```

A later call for the **same model returns the cached schema**, and the arguments
you passed are ignored:

```pycon
>>> second = SchemaFactory.create_schema(models.Day, name='DayIdSchema', fields=['id'])
>>> second is first
True
>>> list(second.model_fields)
['name']

```

!!! danger "Pass `skip_registry=True` for one-off shapes"

    Building schemas per request without `skip_registry=True` means the first
    shape ever requested is the shape everyone gets — a bug that surfaces only
    under a particular request order.

    ```pycon
    >>> third = SchemaFactory.create_schema(
    ...     models.Day, name='DayIdSchema', fields=['id'], skip_registry=True
    ... )
    >>> third is first
    False
    >>> list(third.model_fields)
    ['id']

    ```

`skip_registry=True` both skips the cache lookup and avoids registering the
result, so the schema stays private to the caller.

## A runtime projection

Putting it together — a schema chosen by request input, with the field list
checked against an allow-list first:

```python title="views.py"
from django.http import HttpRequest, JsonResponse

from django_modern_schemas import SchemaFactory

from .models import Event

ALLOWED_FIELDS = {'id', 'title'}


def list_events(request: HttpRequest) -> JsonResponse:
    requested = set(request.GET.get('fields', '').split(',')) & ALLOWED_FIELDS
    schema = SchemaFactory.create_schema(
        Event,
        name='EventProjection',
        fields=sorted(requested) or ['id', 'title'],
        skip_registry=True,  # per-request shape, never cached
    )
    results = [schema.model_validate(event).model_dump() for event in Event.objects.all()]
    return JsonResponse({'results': results})
```

!!! warning "Validate the field list yourself"

    An unknown field name raises `ConfigError` at build time. Intersecting with
    an allow-list, as above, keeps user input from turning into a 500 — and stops
    a client projecting columns you did not mean to expose.

    ```pycon
    >>> SchemaFactory.create_schema(models.Event, fields=['password'], skip_registry=True)
    Traceback (most recent call last):
        ...
    django_modern_schemas.errors.ConfigError: Field(s) {'password'} are not in model.

    ```

## Related guides

- [ModelSchema](model-schema.md) — the declarative equivalent
- [Relations](relations.md) — what `depth` does
