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

## `ModelSchema[Model]` — typing the persistence methods

`ModelSchema` is generic in its Django model. Naming the model as a type
parameter changes nothing at runtime — `Config.model` is still what builds the
fields — but it tells the type checker what `create()`, `update()`, and `save()`
give back:

```pycon
>>> class TypedEventSchema(ModelSchema[models.Event]):
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> list(TypedEventSchema.model_fields)
['title']
>>> type(TypedEventSchema.model_validate({'title': 'DjangoCon'}).create()).__name__
'Event'

```

The parameter and `Config.model` name the same model, and that repetition is the
price of the two audiences: the `Config` is read by the metaclass at class
creation, the parameter by a checker that never runs your code.

| Declaration | `schema.create()` is typed as |
| --- | --- |
| `class S(ModelSchema[Event])` | `Event` |
| `class S(ModelSchema)` | unknown — the checker cannot help you |

So with the parameter, an attribute the model does not have is a reported error
rather than an `AttributeError` in production:

```python title="schemas.py"
class TypedEventSchema(ModelSchema[Event]):
    class Config:
        model = Event
        fields = ['title']


event = TypedEventSchema.model_validate(payload).create()
event.title       # ok — Event.title
event.titel       # error[unresolved-attribute]: Object of type `Event` has no attribute `titel`
```

Without the parameter both lines type-check, and only the second one crashes.

!!! tip "Worth it wherever you write"

    A schema used only for serialization never calls `create()` or `save()`, so
    the parameter buys it nothing. Add it on the schemas that persist — that is
    where an untyped return value spreads through the rest of a view.

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

### Picking one

Use `fields` when the response shape is small and deliberate, and `exclude` when
you want everything the model gains over time except a few columns. They cannot
be combined — a schema states its boundary one way or the other.

!!! tip "Configuration is checked when the class is created"

    Setting both options, naming a field that does not exist, or omitting
    `model` raises `ConfigError` at import time rather than on the first
    request, so a mistake cannot reach production behind an untested path. The
    exact messages are in the [errors reference](../reference/errors.md#configerror).

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

This pairs with `update(partial=True)` for a PATCH endpoint, where absent keys
must be left alone rather than overwritten — see
[Persistence → Partial updates](persistence.md#partial-updates).

Like `fields`, unknown names raise `ConfigError` when the class is created.

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
primary key, and carries Django's `_id` attribute name as its alias:

```pycon
>>> class FlatEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
>>> event = models.Event(id=1, title='DjangoCon', category=models.Category(id=2, name='Python'))
>>> FlatEventSchema.model_validate(event).model_dump()
{'id': 1, 'title': 'DjangoCon', 'category': 2}
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
