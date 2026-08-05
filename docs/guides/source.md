# Source and MethodSource

`Source` and `MethodSource` are metadata you attach with `typing.Annotated`.
They tell the schema *where a field's value comes from* when it is not simply
the model attribute of the same name.

| Use | When the value is |
| --- | --- |
| `Source('category.name')` | At a dotted attribute path on the instance. |
| `Source('name')` | On the instance, but exposed under a different field name. |
| `MethodSource('display_title')` | The return value of a zero-argument method. |

Both are **read-only**. See [Source fields are never written](#source-fields-are-never-written).

## `Source` — reading an attribute path

```python title="models.py"
--8<-- "examples/models.py:event-model"
```

Declare the field with the type you want, annotated with the path:

```pycon
>>> class EventSchema(ModelSchema):
...     category_name: Annotated[str | None, Source('category.name')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> event = models.Event(title='DjangoCon', category=models.Category(name='Python'))
>>> EventSchema.model_validate(event).model_dump()
{'title': 'DjangoCon', 'category_name': 'Python'}

```

### `None` anywhere on the path yields `None`

Traversal stops at the first `None` instead of raising `AttributeError`, so an
optional relation needs no guard:

```pycon
>>> EventSchema.model_validate(models.Event(title='DjangoCon', category=None)).category_name is None
True

```

Annotate the field as optional when the path can produce `None` — otherwise
Pydantic rejects the `None` that `Source` correctly resolved.

### Mappings work too

The same path resolves against dictionaries, which is convenient in tests and
for data that has not been through the ORM:

```pycon
>>> EventSchema.model_validate({'title': 'DjangoCon', 'category': {'name': 'Python'}}).category_name
'Python'

```

### An explicit value wins

If the input already contains the schema field name, that value is used and the
path is never resolved:

```pycon
>>> EventSchema.model_validate({'title': 'DjangoCon', 'category_name': 'Provided'}).category_name
'Provided'

```

### Missing attributes are reported with the path

```pycon
>>> class BadSourceSchema(ModelSchema):
...     missing: Annotated[str, Source('nope')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> try:
...     BadSourceSchema.model_validate(models.Event(title='DjangoCon'))
... except Exception as error:
...     print(error.errors()[0]['msg'])
Error extracting attribute: SourceResolutionError: Unable to resolve 'nope': attribute 'nope' was not found on Event.

```

## `MethodSource` — calling a model method

`MethodSource` invokes a zero-argument method. Method calls are never implicit:
a plain `Source('display_title')` would resolve to the bound method object, not
its result.

```pycon
>>> class EventMethodSchema(ModelSchema):
...     display_title: Annotated[str, MethodSource('display_title')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> EventMethodSchema.model_validate(models.Event(title='DjangoCon')).model_dump()
{'title': 'DjangoCon', 'display_title': 'Event: DjangoCon'}

```

### Inherited methods resolve normally

The method only has to be reachable on the instance — where it is *defined* does
not matter. This model inherits `get_full_name()` from `AbstractUser`:

```python title="models.py"
--8<-- "examples/models.py:speaker-model"
```

```pycon
>>> class SpeakerSchema(ModelSchema):
...     full_name: Annotated[str, MethodSource('get_full_name')]
...     class Config:
...         model = models.Speaker
...         fields = ['username']
>>> speaker = models.Speaker(username='ada', first_name='Ada', last_name='Lovelace')
>>> SpeakerSchema.model_validate(speaker).model_dump()
{'username': 'ada', 'full_name': 'Ada Lovelace'}

```

The method is not defined on `Speaker` at all:

```pycon
>>> 'get_full_name' in vars(models.Speaker)
False
>>> hasattr(models.Speaker, 'get_full_name')
True

```

!!! warning "Check which class you are pointing at"

    `MethodSource` resolves against the model in `Config.model`. If two models
    in a project share a name — an app model and a test model, say — a missing
    method produces the same message in both cases:

    ```text
    SourceResolutionError: Unable to resolve 'get_full_name':
    attribute 'get_full_name' was not found on Speaker.
    ```

    Confirm the method exists on the class actually in use before assuming the
    metadata is at fault. `hasattr(YourModel, 'the_method')` settles it.

### The attribute must be callable

```pycon
>>> class NotCallableSchema(ModelSchema):
...     value: Annotated[str, MethodSource('title')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> try:
...     NotCallableSchema.model_validate(models.Event(title='DjangoCon'))
... except Exception as error:
...     print(error.errors()[0]['msg'])
Error extracting attribute: SourceResolutionError: Unable to resolve method 'title': method 'title' is not callable.

```

### The method must take no arguments

```pycon
>>> class Greeter:
...     name = 'ada'
...     def greet(self, greeting):
...         return f'{greeting}, {self.name}'
>>> SourceResolver().resolve(Greeter(), MethodSource('greet'))
Traceback (most recent call last):
    ...
django_modern_schemas.metadata.exceptions.SourceResolutionError: Unable to resolve method 'greet': methods cannot require arguments.

```

## Path rules

A `Source` path is a dotted chain of Python identifiers, validated when the
metadata object is constructed — so a bad path fails at import time, not on the
first request:

```pycon
>>> Source('  category.name  ').path      # surrounding whitespace is stripped
'category.name'
>>> Source('category.name').parts
('category', 'name')

```

These are rejected:

```pycon
>>> Source('')
Traceback (most recent call last):
    ...
ValueError: Source path cannot be empty.
>>> Source('category..name')
Traceback (most recent call last):
    ...
ValueError: Invalid Source path 'category..name'. Source paths must contain valid Python attributes.
>>> Source('display_title()')
Traceback (most recent call last):
    ...
ValueError: Invalid Source path 'display_title()'. Source paths must contain valid Python attributes.
>>> Source('questions[0].text')
Traceback (most recent call last):
    ...
ValueError: Invalid Source path 'questions[0].text'. Source paths must contain valid Python attributes.

```

| Not supported | Use instead |
| --- | --- |
| `Source('display_title()')` | `MethodSource('display_title')` |
| `Source('questions[0].text')` | Resolve the collection, then index in your own code |
| `Source('questions.text')` | A nested schema over the collection |

## Collections

A reverse `ForeignKey` manager may appear **only as the last segment** of a path,
and is serialized through a nested schema.

```python title="models.py"
--8<-- "examples/models.py:question-model"
```

```pycon
>>> class QuestionSchema(ModelSchema):
...     class Config:
...         model = models.Question
...         fields = ['text']
>>> class CategoryQuestionsSchema(ModelSchema):
...     questions: Annotated[list[QuestionSchema], Source('questions')]
...     class Config:
...         model = models.Category
...         fields = ['name']

```

With the relation prefetched, serializing runs no further queries:

```pycon
>>> category = models.Category.objects.create(name='Python')
>>> _ = models.Question.objects.create(text='What is Django?', category=category)
>>> _ = models.Question.objects.create(text='What is Pydantic?', category=category)
>>> category = models.Category.objects.prefetch_related('questions').get(pk=category.pk)
>>> CategoryQuestionsSchema.model_validate(category).model_dump()
{'name': 'Python', 'questions': [{'text': 'What is Django?'}, {'text': 'What is Pydantic?'}]}

```

### Traversing *through* a collection is refused

`questions.text` is ambiguous — there are many questions — so it is rejected
rather than guessed:

```pycon
>>> class TraverseSchema(ModelSchema):
...     question_text: Annotated[str, Source('questions.text')]
...     class Config:
...         model = models.Category
...         fields = ['name']
>>> try:
...     TraverseSchema.model_validate(category)
... except Exception as error:
...     print(error.errors()[0]['msg'])
Error extracting attribute: SourceResolutionError: Unable to resolve 'questions.text': attribute 'questions' resolves to a collection that cannot be traversed.

```

### `ManyToMany` is not a `Source`

Only reverse `ForeignKey` collections are supported:

```python title="models.py"
--8<-- "examples/models.py:week-models"
```

```pycon
>>> class DaySchema(ModelSchema):
...     class Config:
...         model = models.Day
...         fields = ['name']
>>> class WeekSourceSchema(ModelSchema):
...     days: Annotated[list[DaySchema], Source('days')]
...     class Config:
...         model = models.Week
...         fields = ['name']
>>> week = models.Week.objects.create(name='Week 1')
>>> week.days.add(models.Day.objects.create(name='Monday'))
>>> try:
...     WeekSourceSchema.model_validate(week)
... except Exception as error:
...     print(error.errors()[0]['msg'])
Error extracting attribute: SourceResolutionError: Unable to resolve 'days': Source only supports reverse ForeignKey collections.

```

`ManyToMany` fields still serialize as ordinary generated fields — see
[Relations](relations.md#many-to-many).

## Source fields are never written

`create()` and `update()` skip every `Source` and `MethodSource` field, because
those say how to *read* a value, not where to store it.

```pycon
>>> class EventWriteSchema(ModelSchema):
...     category_name: Annotated[str, Source('category.name')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> created = EventWriteSchema.model_validate({'title': 'DjangoCon', 'category_name': 'Python'}).create()
>>> created.title
'DjangoCon'
>>> created.category is None
True

```

This holds even when the `Source` field shadows a real model attribute — the
schema value is read from the path, and the model attribute is left alone:

```pycon
>>> class ShadowSchema(ModelSchema):
...     title: Annotated[str, Source('category.name')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> event = models.Event.objects.create(title='DjangoCon', category=category)
>>> schema = ShadowSchema.model_validate(event)
>>> schema.title                                   # read from category.name
'Python'
>>> _ = schema.update(event)
>>> models.Event.objects.get(pk=event.pk).title    # left untouched
'DjangoCon'

```

## Resolving without a schema

`SourceResolver` applies the same rules outside a schema, which is useful in
tests and ad-hoc code:

```pycon
>>> resolver = SourceResolver()
>>> event = models.Event(title='DjangoCon', category=models.Category(name='Python'))
>>> resolver.resolve(event, Source('category.name'))
'Python'
>>> resolver.resolve({'category': {'name': 'Python'}}, Source('category.name'))
'Python'
>>> resolver.resolve(models.Event(title='DjangoCon'), MethodSource('display_title'))
'Event: DjangoCon'

```

Failures raise `SourceResolutionError` directly, rather than wrapped in a
Pydantic `ValidationError`:

```pycon
>>> resolver.resolve(event, Source('missing'))
Traceback (most recent call last):
    ...
django_modern_schemas.metadata.exceptions.SourceResolutionError: Unable to resolve 'missing': attribute 'missing' was not found on Event.

```

## Performance note

Every path is resolved on **every** validation, for every field on the schema.
Two `model_validate()` calls on the same instance do all the work twice:

```pycon
>>> first = EventSchema.model_validate(event)    # resolves category.name
>>> second = EventSchema.model_validate(event)   # resolves it again

```

Validate once and read the fields off the result, rather than re-validating per
field.

## Related guides

- [Relations](relations.md) — generated relation fields and nesting
- [Persistence](persistence.md) — what `create()` and `update()` write
- [Errors](../reference/errors.md) — `SourceResolutionError` in full
