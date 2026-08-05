# Relations

A relation can be represented two ways: as the related object's **primary key**
(the default, `depth = 0`), or as a **nested schema** (`depth = 1` or more).

| Relation | `depth = 0` | `depth = 1` |
| --- | --- | --- |
| `ManyToManyField` | `list[int]` of primary keys | `list[NestedSchema]` |
| `ForeignKey` / `OneToOneField` | `int` primary key, aliased `<name>_id` | Nested schema, `None` when unset |
| Reverse `ForeignKey` | Not generated — use [`Source`](source.md#collections) | Not generated |

## Many-to-many

```python title="models.py"
--8<-- "examples/models.py:week-models"
```

At the default depth, the field is a list of primary keys:

```pycon
>>> class WeekSchema(ModelSchema):
...     class Config:
...         model = models.Week
>>> week = models.Week.objects.create(name='Week 1')
>>> monday = models.Day.objects.create(name='Monday')
>>> tuesday = models.Day.objects.create(name='Tuesday')
>>> week.days.add(monday, tuesday)
>>> WeekSchema.model_validate(week).model_dump()
{'id': 1, 'name': 'Week 1', 'days': [1, 2]}

```

The field accepts either primary keys or model instances on input, so you can
hand it whichever you have:

```pycon
>>> WeekSchema.model_validate({'name': 'Week 2', 'days': [monday, tuesday]}).days
[1, 2]
>>> WeekSchema.model_validate({'name': 'Week 2', 'days': [1, 2]}).days
[1, 2]

```

### Nesting with `depth`

```pycon
>>> class NestedWeekSchema(ModelSchema):
...     class Config:
...         model = models.Week
...         depth = 1
...         skip_registry = True
>>> week = models.Week.objects.prefetch_related('days').get(pk=week.pk)
>>> NestedWeekSchema.model_validate(week).model_dump()
{'id': 1, 'name': 'Week 1', 'days': [{'id': 1, 'name': 'Monday'}, {'id': 2, 'name': 'Tuesday'}]}

```

## Forward relations (`ForeignKey`, `OneToOneField`)

```python title="models.py"
--8<-- "examples/models.py:event-model"
```

### Nested — the recommended form

With `depth = 1`, the relation becomes a nested schema and `None` is handled:

```pycon
>>> class NestedEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         depth = 1
...         skip_registry = True
>>> category = models.Category.objects.create(name='Python')
>>> event = models.Event.objects.create(title='DjangoCon', category=category)
>>> NestedEventSchema.model_validate(event).model_dump()
{'id': 1, 'title': 'DjangoCon', 'category': {'id': 1, 'name': 'Python'}}
>>> NestedEventSchema.model_validate(models.Event.objects.create(title='Solo')).model_dump()
{'id': 2, 'title': 'Solo', 'category': None}

```

### Flat — the related primary key

At `depth = 0` a forward relation is represented by the related object's primary
key:

```pycon
>>> class FlatEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
>>> FlatEventSchema.model_validate(event).model_dump()
{'id': 1, 'title': 'DjangoCon', 'category': 1}

```

An unset relation resolves to `None`:

```pycon
>>> FlatEventSchema.model_validate(models.Event(id=3, title='Solo', category=None)).model_dump()
{'id': 3, 'title': 'Solo', 'category': None}

```

Either a primary key or the related instance is accepted on input, so you can
pass whichever you have:

```pycon
>>> FlatEventSchema.model_validate({'title': 'X', 'category': category.pk}).category
1
>>> FlatEventSchema.model_validate({'title': 'X', 'category': category}).category
1

```

The field carries Django's `_id` attribute name as its alias, which is what
`create()` and `update()` use to write the relation:

```pycon
>>> FlatEventSchema.model_fields['category'].alias
'category_id'

```

Ordinary output is unaffected — the field name stays `category`:

```pycon
>>> FlatEventSchema.model_validate(event).model_dump_json()
'{"id":1,"title":"DjangoCon","category":1}'
>>> list(FlatEventSchema.model_json_schema()['properties'])
['id', 'title', 'category']

```

## Reverse relations

Reverse relations are **never generated automatically** — a schema does not
silently acquire a field that triggers a query. Declare it with
[`Source`](source.md#collections):

```python title="models.py"
--8<-- "examples/models.py:question-model"
```

```pycon
>>> class QuestionSchema(ModelSchema):
...     class Config:
...         model = models.Question
...         fields = ['text']
>>> class CategorySchema(ModelSchema):
...     questions: Annotated[list[QuestionSchema], Source('questions')]
...     class Config:
...         model = models.Category
...         fields = ['name']
>>> _ = models.Question.objects.create(text='What is Django?', category=category)
>>> category = models.Category.objects.prefetch_related('questions').get(pk=category.pk)
>>> CategorySchema.model_validate(category).model_dump()
{'name': 'Python', 'questions': [{'text': 'What is Django?'}]}

```

A reverse **one-to-one** is a single object, so it is traversed like any other
attribute path:

```pycon
>>> class CategoryEventSchema(ModelSchema):
...     event_title: Annotated[str, Source('event.title')]
...     class Config:
...         model = models.Category
...         fields = ['name']
>>> category = models.Category.objects.select_related('event').get(pk=category.pk)
>>> CategoryEventSchema.model_validate(category).model_dump()
{'name': 'Python', 'event_title': 'DjangoCon'}

```

## Query planning is yours

The library never modifies your queryset. A schema that reaches across a
relation will happily run one query per instance if you let it.

With the relation prefetched, serialization runs **no** extra queries:

```pycon
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> category = models.Category.objects.prefetch_related('questions').get(pk=category.pk)
>>> with CaptureQueriesContext(connection) as queries:
...     data = CategorySchema.model_validate(category).model_dump()
>>> len(queries)
0

```

Without it, the same schema issues a query while serializing:

```pycon
>>> category = models.Category.objects.get(pk=category.pk)
>>> with CaptureQueriesContext(connection) as queries:
...     data = CategorySchema.model_validate(category).model_dump()
>>> len(queries)
1

```

| Relation in the schema | Load it with |
| --- | --- |
| Forward `ForeignKey` / `OneToOneField` | `select_related('category')` |
| Reverse one-to-one | `select_related('event')` |
| Reverse `ForeignKey` collection | `prefetch_related('questions')` |
| `ManyToManyField` | `prefetch_related('days')` |

!!! tip "Measure it"

    `CaptureQueriesContext`, as used above, is the most direct way to assert in
    your own tests that a serializer did not fall into N+1.

## Related guides

- [ModelSchema → depth](model-schema.md#depth-nesting-related-schemas)
- [Source and MethodSource](source.md) — reverse collections and attribute paths
- [Field reference](../reference/fields.md) — relation field conversions
