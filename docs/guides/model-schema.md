# ModelSchema

`ModelSchema` generates Pydantic fields from a Django model. This guide covers
every `Config` option and the rules that decide what a generated field looks
like.

The models used throughout:

```python title="models.py"
--8<-- "examples/models.py:category-model"

--8<-- "examples/models.py:event-model"
```

## Declaring a schema

`Config.model` is the only required option. With nothing else set, every
concrete field on the model is generated:

```pycon
>>> class EventSchema(ModelSchema):
...     class Config:
...         model = models.Event
>>> list(EventSchema.model_fields)
['id', 'title', 'category']

```

Reverse relations are not included by default — `Category.questions` does not
appear on a `Category` schema unless you declare it yourself with
[`Source`](source.md):

```pycon
>>> class CategorySchema(ModelSchema):
...     class Config:
...         model = models.Category
>>> list(CategorySchema.model_fields)
['id', 'name']

```

## Selecting fields

### `fields`

An allow-list. Only the named fields are generated.

```pycon
>>> class EventTitleSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> list(EventTitleSchema.model_fields)
['title']

```

!!! warning "The option is `fields`, not `include`"

    Earlier revisions of this project used `include`. That name is no longer
    recognised — it would be silently ignored, and you would get every field.

### `exclude`

A deny-list. Everything except the named fields is generated.

```pycon
>>> class EventWithoutCategorySchema(ModelSchema):
...     class Config:
...         model = models.Event
...         exclude = ['category']
>>> list(EventWithoutCategorySchema.model_fields)
['id', 'title']

```

### They are mutually exclusive

Setting both is a configuration error, raised when the class is created:

```pycon
>>> class BrokenSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
...         exclude = ['category']
Traceback (most recent call last):
    ...
django_modern_schemas.errors.ConfigError: Only one of 'fields' or 'exclude' should be set in configuration.

```

### Unknown names are rejected

Typos fail loudly instead of producing a schema that is quietly missing a field:

```pycon
>>> class TypoSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['titel']
Traceback (most recent call last):
    ...
django_modern_schemas.errors.ConfigError: Field(s) {'titel'} are not in model.

```

A missing `model` is caught the same way:

```pycon
>>> class NoModelSchema(ModelSchema):
...     class Config:
...         fields = ['title']
Traceback (most recent call last):
    ...
django_modern_schemas.errors.ConfigError: Invalid Configuration. 'model' is required

```

## `optional` — relaxing required fields

`optional` makes generated fields non-required with a default of `None`. This is
how you build a PATCH schema without duplicating the field list.

```pycon
>>> class EventPatchSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
...         optional = ['title']
>>> EventPatchSchema.model_fields['title'].is_required()
False
>>> EventPatchSchema.model_validate({}).model_dump()
{'title': None}

```

Pass `'__all__'` to relax every field at once:

```pycon
>>> class EventAllOptionalSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         optional = '__all__'
>>> {name: info.is_required() for name, info in EventAllOptionalSchema.model_fields.items()}
{'id': False, 'title': False, 'category': False}

```

Like `fields`, unknown names are rejected:

```pycon
>>> class BadOptionalSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         optional = ['nope']
Traceback (most recent call last):
    ...
django_modern_schemas.errors.ConfigError: Field(s) {'nope'} are not in model.

```

## The primary key rule

The primary key is made optional automatically, so one schema can serve both
input (no pk yet) and output (pk present).

```pycon
>>> class DefaultPkSchema(ModelSchema):
...     class Config:
...         model = models.Event
>>> DefaultPkSchema.model_fields['id'].is_required()
False

```

That automatic relaxation is skipped when you name the pk yourself. Listing `id`
in `fields` reads as a deliberate request for it, so it stays required:

```pycon
>>> class ExplicitPkSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['id', 'title']
>>> ExplicitPkSchema.model_fields['id'].is_required()
True

```

If you want it listed *and* optional, say so:

```pycon
>>> class ExplicitOptionalPkSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['id', 'title']
...         optional = ['id']
>>> ExplicitOptionalPkSchema.model_fields['id'].is_required()
False

```

| `Config` | `id` required? |
| --- | --- |
| neither `fields` nor `exclude` | No — relaxed automatically |
| `exclude = [...]`, pk not excluded | No — relaxed automatically |
| `fields = ['id', ...]` | **Yes** — you asked for it |
| `fields = ['id', ...]` + `optional = ['id']` | No |
| `optional = '__all__'` | No |

## `depth` — nesting related schemas

At the default `depth = 0`, a relation is represented by the related object's
primary key, exposed under Django's `_id` attribute name:

```pycon
>>> class FlatEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
>>> FlatEventSchema.model_fields['category'].annotation
typing.Optional[int]
>>> FlatEventSchema.model_fields['category'].alias
'category_id'

```

With `depth = 1`, the relation becomes a generated nested schema instead:

```pycon
>>> class NestedEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         depth = 1
...         skip_registry = True
>>> sorted(NestedEventSchema.model_json_schema()['$defs'])
['Category']

```

Serializing then produces a nested object:

```pycon
>>> event = models.Event(id=1, title='DjangoCon', category=models.Category(id=2, name='Python'))
>>> NestedEventSchema.model_validate(event).model_dump()
{'id': 1, 'title': 'DjangoCon', 'category': {'id': 2, 'name': 'Python'}}

```

!!! danger "`depth` multiplies queries"

    Each nested level is another relation to traverse. `depth` changes the shape
    of the schema, never the queryset — pair it with `select_related()` or
    `prefetch_related()`. See [Relations](relations.md#query-planning-is-yours).

!!! note "`depth` and the schema registry"

    Nested schemas are built through [`SchemaFactory`](schema-factory.md), which
    caches one schema per model in a global registry. `skip_registry = True`
    keeps a schema out of that cache — useful when you generate several
    differently-shaped schemas for the same model, as this page does.

## Overriding a generated field

Any annotation you write by hand replaces the generated field. Use it to
tighten a type, add a validator, or change a default.

```pycon
>>> from pydantic import Field
>>> class ShortTitleSchema(ModelSchema):
...     title: str = Field(max_length=10)
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> ShortTitleSchema.model_fields['title'].metadata
[MaxLen(max_length=10)]

```

The Django-derived `max_length=100` is gone, because the field is no longer
generated — you now own it.

## Adding non-model fields

Annotations that do not correspond to a model field are kept as ordinary
Pydantic fields:

```pycon
>>> class AnnotatedEventSchema(ModelSchema):
...     computed_label: str = 'default label'
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> list(AnnotatedEventSchema.model_fields)
['title', 'computed_label']
>>> AnnotatedEventSchema.model_validate({'title': 'DjangoCon'}).computed_label
'default label'

```

To populate such a field from the instance, use [`Source` or
`MethodSource`](source.md).

## Pydantic options in the same `Config`

Keys that are not `ModelSchema` options are passed through to Pydantic, so
standard model config lives alongside `model` and `fields`:

```pycon
>>> class StrictEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
...         extra = 'forbid'
>>> StrictEventSchema.model_config['extra']
'forbid'

```

## Option summary

| Option | Type | Default | Purpose |
| --- | --- | --- | --- |
| `model` | Django model class | — | **Required.** The model to generate from. |
| `fields` | `list[str]` | all fields | Allow-list of model fields. |
| `exclude` | `list[str]` | `()` | Deny-list of model fields. |
| `optional` | `list[str]` or `'__all__'` | `()` | Make fields non-required, defaulting to `None`. |
| `depth` | `int` | `0` | Levels of relations expanded into nested schemas. |
| `skip_registry` | `bool` | `False` | Do not cache this schema in the global registry. |
| `registry` | `SchemaRegister` | global registry | Registry used for nested schema lookup. |

The same options with their underlying behaviour are in the
[configuration reference](../reference/configuration.md).

## Related guides

- [Field reference](../reference/fields.md) — what each Django field becomes
- [Relations](relations.md) — foreign keys, many-to-many and nesting
- [Source and MethodSource](source.md) — renamed and computed fields
- [Persistence](persistence.md) — writing validated data back
