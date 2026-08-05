# Source and MethodSource

`Source` and `MethodSource` are metadata you attach with `typing.Annotated`.
They tell the schema *where a field's value comes from* when it is not simply
the model attribute of the same name.

| Use | When the value is |
| --- | --- |
| `Source('category.name')` | At a dotted attribute path on the instance. |
| `Source('name')` | On the instance, but exposed under a different field name. |
| `MethodSource('display_title')` | The return value of a zero-argument method. |

Both are read-only: they say how to *read* a value, not where to store it.

## Flattening a relation into the response

The most common use. An API response should show the category's name, not its
id, without a nested object and without a second round-trip.

```python title="models.py"
--8<-- "examples/models.py:event-model"
```

```pycon
>>> class EventSchema(ModelSchema):
...     category_name: Annotated[str | None, Source('category.name')]
...     class Config:
...         model = models.Event
...         fields = ['id', 'title']
>>> category = models.Category.objects.create(name='Python')
>>> event = models.Event.objects.create(title='DjangoCon', category=category)
>>> EventSchema.model_validate(event).model_dump()
{'id': 1, 'title': 'DjangoCon', 'category_name': 'Python'}

```

Traversal stops at the first `None`, so an optional relation needs no guard in
your code:

```pycon
>>> EventSchema.model_validate(models.Event(id=2, title='Solo')).model_dump()
{'id': 2, 'title': 'Solo', 'category_name': None}

```

!!! tip "Annotate the field as optional when the path can be `None`"

    `Source` correctly resolves to `None`, but a field typed `str` will then
    reject it. Use `str | None` whenever any step of the path is nullable.

## Renaming a field

A single-segment path exposes a model attribute under a different name — useful
when your API vocabulary differs from your schema's.

```pycon
>>> class EventCardSchema(ModelSchema):
...     name: Annotated[str, Source('title')]
...     class Config:
...         model = models.Event
...         fields = ['id']
>>> EventCardSchema.model_validate(event).model_dump()
{'id': 1, 'name': 'DjangoCon'}

```

## Computed values with `MethodSource`

`MethodSource` calls a zero-argument method on the model. Method calls are never
implicit — a plain `Source('display_title')` would resolve to the bound method
object rather than its result.

```pycon
>>> class EventDetailSchema(ModelSchema):
...     display_title: Annotated[str, MethodSource('display_title')]
...     class Config:
...         model = models.Event
...         fields = ['id', 'title']
>>> EventDetailSchema.model_validate(event).model_dump()
{'id': 1, 'title': 'DjangoCon', 'display_title': 'Event: DjangoCon'}

```

This keeps presentation logic on the model, where the rest of your application
can use it too.

### Inherited methods work the same

The method only has to be reachable on the instance — where it is *defined* does
not matter. A model inheriting `AbstractUser` gets `get_full_name()` for free:

```python title="models.py"
--8<-- "examples/models.py:speaker-model"
```

```pycon
>>> class SpeakerSchema(ModelSchema):
...     full_name: Annotated[str, MethodSource('get_full_name')]
...     short_name: Annotated[str, MethodSource('get_short_name')]
...     class Config:
...         model = models.Speaker
...         fields = ['username', 'email']
>>> speaker = models.Speaker(username='ada', first_name='Ada', last_name='Lovelace', email='ada@example.com')
>>> SpeakerSchema.model_validate(speaker).model_dump()
{'username': 'ada', 'email': 'ada@example.com', 'full_name': 'Ada Lovelace', 'short_name': 'Ada'}

```

`get_full_name` is not defined on `Speaker` at all — it comes from the base
class, and `MethodSource` resolves it like any other attribute:

```pycon
>>> 'get_full_name' in vars(models.Speaker)
False
>>> hasattr(models.Speaker, 'get_full_name')
True

```

!!! tip "If a method is not found, check which model you are pointing at"

    `MethodSource` resolves against the model in `Config.model`. When two models
    in a project share a name — an app model and a test model, say —
    `hasattr(YourModel, 'the_method')` settles which one the schema is bound to
    faster than reading the error.

## Serializing a reverse collection

A reverse `ForeignKey` manager becomes a list of nested schemas — the natural
shape for "a category and its questions" in one response.

```python title="models.py"
--8<-- "examples/models.py:question-model"
```

```pycon
>>> class QuestionSchema(ModelSchema):
...     class Config:
...         model = models.Question
...         fields = ['id', 'text']
>>> class CategoryDetailSchema(ModelSchema):
...     questions: Annotated[list[QuestionSchema], Source('questions')]
...     class Config:
...         model = models.Category
...         fields = ['id', 'name']
>>> _ = models.Question.objects.create(text='What is Django?', category=category)
>>> _ = models.Question.objects.create(text='What is Pydantic?', category=category)
>>> category = models.Category.objects.prefetch_related('questions').get(pk=category.pk)
>>> print(json.dumps(CategoryDetailSchema.model_validate(category).model_dump(), indent=2))
{
  "id": 1,
  "name": "Python",
  "questions": [
    {
      "id": 1,
      "text": "What is Django?"
    },
    {
      "id": 2,
      "text": "What is Pydantic?"
    }
  ]
}

```

With the relation prefetched, serializing runs no additional queries:

```pycon
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> with CaptureQueriesContext(connection) as queries:
...     data = CategoryDetailSchema.model_validate(category).model_dump()
>>> len(queries)
0

```

## Accepting input as well

A `Source` field is filled from the input when the input already contains it,
which lets one schema serve reads and writes:

```pycon
>>> EventSchema.model_validate({'id': 9, 'title': 'PyCon', 'category_name': 'Python'}).model_dump()
{'id': 9, 'title': 'PyCon', 'category_name': 'Python'}

```

Paths also resolve against plain dictionaries, which keeps tests and non-ORM
data working with the same schema:

```pycon
>>> EventSchema.model_validate({'id': 9, 'title': 'PyCon', 'category': {'name': 'Python'}}).category_name
'Python'

```

## Source fields are never written

`create()` and `update()` skip every `Source` and `MethodSource` field, so a
read-only presentation field cannot accidentally reach the database:

```pycon
>>> class EventCreateSchema(ModelSchema):
...     category_name: Annotated[str, Source('category.name')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> created = EventCreateSchema.model_validate({'title': 'RustConf', 'category_name': 'Rust'}).create()
>>> created.title
'RustConf'
>>> created.category is None
True

```

This holds even when the field shadows a real model attribute — the value is
read from the path, and the column is left alone:

```pycon
>>> class ShadowSchema(ModelSchema):
...     title: Annotated[str, Source('category.name')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> schema = ShadowSchema.model_validate(event)
>>> schema.title                                   # read from category.name
'Python'
>>> _ = schema.update(event)
>>> models.Event.objects.get(pk=event.pk).title    # column untouched
'DjangoCon'

```

## Resolving without a schema

`SourceResolver` applies the same rules outside a schema — handy in a service
layer or a management command where a full schema would be overkill:

```pycon
>>> resolver = SourceResolver()
>>> resolver.resolve(event, Source('category.name'))
'Python'
>>> resolver.resolve(event, MethodSource('display_title'))
'Event: DjangoCon'
>>> resolver.resolve({'category': {'name': 'Python'}}, Source('category.name'))
'Python'

```

## What a path may contain

A path is a dotted chain of Python identifiers, validated when the metadata is
constructed — so a malformed path fails at import time rather than on the first
request.

```pycon
>>> Source('  category.name  ').path      # surrounding whitespace is stripped
'category.name'
>>> Source('category.name').parts
('category', 'name')

```

| Not supported | Use instead |
| --- | --- |
| `Source('display_title()')` | `MethodSource('display_title')` |
| `Source('questions[0].text')` | Resolve the collection, then index in your own code |
| `Source('questions.text')` | A nested schema over the collection, as [above](#serializing-a-reverse-collection) |
| `Source('tags')` for a `ManyToMany` | A generated field — see [Relations](relations.md#many-to-many) |

A reverse `ForeignKey` collection is supported only as the **last** segment of a
path; traversing *through* a collection is ambiguous and is refused rather than
guessed. `MethodSource` requires the attribute to be callable and to take no
arguments.

The exact messages for each of these are listed in the
[errors reference](../reference/errors.md#sourceresolutionerror).

## Related guides

- [Relations](relations.md) — generated relation fields and nesting
- [Persistence](persistence.md) — what `create()` and `update()` write
- [Errors](../reference/errors.md) — `SourceResolutionError` in full
