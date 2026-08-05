# ModelSchema Configuration

Every option accepted by a `ModelSchema`'s nested `Config` class.

| Option | Type | Default | Required |
| --- | --- | --- | --- |
| [`model`](#model) | Django model class | — | **Yes** |
| [`fields`](#fields) | `list[str]` or `'__all__'` | `'__all__'` | No |
| [`exclude`](#exclude) | `list[str]` | `()` | No |
| [`optional`](#optional) | `list[str]` or `'__all__'` | `()` | No |
| [`depth`](#depth) | `int` | `0` | No |
| [`registry`](#registry) | `SchemaRegister` | global registry | No |
| [`skip_registry`](#skip_registry) | `bool` | `False` | No |

Unrecognised keys are forwarded to Pydantic as model config — see
[Pydantic options](#pydantic-options).

## `model`

The Django model to generate fields from. Validated when the class is created:

```pycon
>>> class NoModelSchema(ModelSchema):
...     class Config:
...         fields = ['title']
Traceback (most recent call last):
    ...
django_modern_schemas.errors.ConfigError: Invalid Configuration. 'model' is required

```

## `fields`

An allow-list of model field names. `'__all__'` — the default — means every
concrete field.

```pycon
>>> class EventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> list(EventSchema.model_fields)
['title']

```

Unknown names raise `ConfigError`. Cannot be combined with `exclude`.

!!! warning "It is `fields`, not `include`"

    `include` is not recognised and is silently ignored, producing a schema with
    every field.

## `exclude`

A deny-list of model field names.

```pycon
>>> class EventWithoutCategorySchema(ModelSchema):
...     class Config:
...         model = models.Event
...         exclude = ['category']
>>> list(EventWithoutCategorySchema.model_fields)
['id', 'title']

```

Setting both `fields` and `exclude` raises:

```pycon
>>> class BothSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
...         exclude = ['category']
Traceback (most recent call last):
    ...
django_modern_schemas.errors.ConfigError: Only one of 'fields' or 'exclude' should be set in configuration.

```

## `optional`

Field names that become non-required with a default of `None`. Accepts
`'__all__'`.

```pycon
>>> class EventPatchSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
...         optional = ['title']
>>> EventPatchSchema.model_fields['title'].is_required()
False

```

The primary key is added to this set automatically unless it is named in
`fields` — see [the pk rule](../guides/model-schema.md#the-primary-key-rule).

## `depth`

How many levels of relations to expand into nested schemas. `0` represents a
relation by primary key; `1` and above generate nested schemas through
[`SchemaFactory`](../guides/schema-factory.md).

```pycon
>>> class NestedEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         depth = 1
...         skip_registry = True
>>> sorted(NestedEventSchema.model_json_schema()['$defs'])
['Category']

```

!!! danger "`depth` changes the schema, never the queryset"

    Pair it with `select_related()` / `prefetch_related()` — see
    [Relations](../guides/relations.md#query-planning-is-yours).

## `registry`

The `SchemaRegister` used to look up and store generated nested schemas.
Defaults to the process-wide registry. Supply your own to isolate a group of
schemas from the global one.

## `skip_registry`

When `True`, the schema is neither looked up in nor added to the registry. Use
it for one-off shapes, and whenever you generate more than one schema for the
same model.

```pycon
>>> class FirstDaySchema(ModelSchema):
...     class Config:
...         model = models.Day
...         fields = ['name']
...         skip_registry = True
>>> class SecondDaySchema(ModelSchema):
...     class Config:
...         model = models.Day
...         fields = ['id']
...         skip_registry = True
>>> list(FirstDaySchema.model_fields), list(SecondDaySchema.model_fields)
(['name'], ['id'])

```

## Pydantic options

Any other key is passed through to Pydantic's model config:

```pycon
>>> class StrictEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
...         extra = 'forbid'
...         str_strip_whitespace = True
>>> StrictEventSchema.model_config['extra']
'forbid'
>>> StrictEventSchema.model_config['str_strip_whitespace']
True

```

`from_attributes` is enabled by the base class and does not need to be set.

## Using `model_config` instead

A `model_config` dict is accepted in place of a `Config` class:

```pycon
>>> class DictConfigSchema(ModelSchema):
...     model_config = {'model': models.Event, 'fields': ['title']}
>>> list(DictConfigSchema.model_fields)
['title']

```

The `Config` class is the documented form; `model_config` exists for
programmatic construction.

## Related pages

- [ModelSchema guide](../guides/model-schema.md) — each option in context
- [Field reference](fields.md) — how a Django field becomes an annotation
- [SchemaFactory](../guides/schema-factory.md) — the runtime equivalent
