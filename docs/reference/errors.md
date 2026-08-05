# Errors

The three exception types this library raises, when each appears, and how to
handle it.

| Exception | Raised at | Import from |
| --- | --- | --- |
| [`ConfigError`](#configerror) | Class creation | `django_modern_schemas.errors` |
| [`SourceResolutionError`](#sourceresolutionerror) | Validation | `django_modern_schemas` |
| [`NotImplementedError`](#notimplementederror) | `create()` / `update()` | builtin |

Pydantic's own `ValidationError` is raised for ordinary validation failures and
is documented [in the Pydantic docs](https://docs.pydantic.dev/latest/errors/validation_errors/).

## `ConfigError`

A misconfigured `Config`. Raised **when the class is created**, so it surfaces at
import time rather than on the first request.

```pycon
>>> from django_modern_schemas.errors import ConfigError

```

| Message | Cause |
| --- | --- |
| `Invalid Configuration. 'model' is required` | No `model` in `Config` |
| `Only one of 'fields' or 'exclude' should be set in configuration.` | Both set on a `ModelSchema` |
| `Only one of 'fields' or 'exclude' should be set.` | Both passed to `SchemaFactory.create_schema()` |
| `Field(s) {...} are not in model.` | A name in `fields`, `exclude` or `optional` is not a model field |
| `... (Is `Config.model` a valid Django model class?)` | `model` is not a Django model |

```pycon
>>> try:
...     class TypoSchema(ModelSchema):
...         class Config:
...             model = models.Event
...             fields = ['titel']
... except ConfigError as error:
...     print(error)
Field(s) {'titel'} are not in model.

```

Because these fire at import time, a broken schema cannot reach production
behind an untested code path.

## `SourceResolutionError`

A [`Source` or `MethodSource`](../guides/source.md) that could not be resolved.

```pycon
>>> from django_modern_schemas import SourceResolutionError

```

| Message | Cause |
| --- | --- |
| `Unable to resolve '<path>': attribute '<name>' was not found on <Type>.` | The attribute does not exist |
| `Unable to resolve '<path>': key '<name>' was not found.` | Mapping input is missing the key |
| `Unable to resolve '<path>': attribute '<name>' resolves to a collection that cannot be traversed.` | A collection appears mid-path |
| `Unable to resolve '<path>': Source only supports reverse ForeignKey collections.` | The collection is a `ManyToMany` |
| `Unable to resolve method '<name>': method '<name>' is not callable.` | `MethodSource` points at a non-callable |
| `Unable to resolve method '<name>': methods cannot require arguments.` | The method requires arguments |

### Where it surfaces

Through a schema, it is wrapped by Pydantic as a `get_attribute_error`:

```pycon
>>> class BadSchema(ModelSchema):
...     missing: Annotated[str, Source('nope')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> try:
...     BadSchema.model_validate(models.Event(title='DjangoCon'))
... except Exception as error:
...     print(type(error).__name__)
...     print(error.errors()[0]['type'])
...     print(error.errors()[0]['msg'])
ValidationError
get_attribute_error
Error extracting attribute: SourceResolutionError: Unable to resolve 'nope': attribute 'nope' was not found on Event.

```

Through [`SourceResolver`](../guides/source.md#resolving-without-a-schema), it is
raised directly:

```pycon
>>> try:
...     SourceResolver().resolve(models.Event(title='DjangoCon'), Source('nope'))
... except SourceResolutionError as error:
...     print(error)
Unable to resolve 'nope': attribute 'nope' was not found on Event.

```

!!! tip "Read the type name in the message"

    The message ends with the class the attribute was looked for on
    (`... was not found on Event.`). When two models in a project share a name,
    that is the fastest way to tell which one the schema is actually bound to.

## `NotImplementedError`

Raised by `create()` and `update()` when the schema contains a nested Pydantic
model, because nested writes are application-specific.

| Message | Method |
| --- | --- |
| `Creating models with child Pydantic models is not supported yet. Please override the `create` method in your schema.` | `create()` |
| `Updating models with child Pydantic models is not supported yet. Please override the `update` method in your schema.` | `update()` |

Resolve it by overriding the method — see
[Persistence → Nested models](../guides/persistence.md#nested-models).

## `TypeError` from `create()`

Not a library exception, but worth knowing: when the model rejects the data,
`create()` re-raises the original error as a `TypeError` naming the model.

```text
TypeError: Error creating Event instance: <original error>.
Ensure that all fields in the schema match the model's fields.
```

The original exception is available as `__cause__`:

```pycon
>>> class ExtraFieldSchema(ModelSchema):
...     not_a_model_field: str = 'x'
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> try:
...     ExtraFieldSchema.model_validate({'title': 'DjangoCon'}).create()
... except TypeError as error:
...     print(type(error.__cause__).__name__)
TypeError

```

## Handling them in a view

```python title="views.py"
import json

from django.http import HttpRequest, JsonResponse
from pydantic import ValidationError

from django_modern_schemas import SourceResolutionError

from .schemas import EventSchema


def create_event(request: HttpRequest) -> JsonResponse:
    try:
        schema = EventSchema.model_validate(json.loads(request.body))
    except ValidationError as error:
        # Client error: the payload did not satisfy the schema.
        return JsonResponse({'errors': error.errors()}, status=400)

    try:
        event = schema.create()
    except TypeError:
        # Server error: the schema and the model disagree.
        raise

    return JsonResponse({'id': event.pk}, status=201)
```

`ConfigError` and `SourceResolutionError` generally indicate a programming error
rather than bad input — let them surface rather than catching them per request.

## Related pages

- [Source and MethodSource](../guides/source.md) — resolution rules
- [ModelSchema configuration](configuration.md) — what is validated
- [Persistence](../guides/persistence.md) — nested-write overrides
