# Overview

This page explains what each public API is for, how a schema is built, and —
just as importantly — what the library will not do for you.

## The public API

| Object | Use it when |
| --- | --- |
| [`Schema`](guides/basic-schema.md) | You want a plain Pydantic model that reads attributes off arbitrary objects. No Django model involved. |
| [`ModelSchema`](guides/model-schema.md) | You want fields generated from a Django model. This is the main entry point. |
| [`SchemaFactory`](guides/schema-factory.md) | You need a schema built at runtime, when the field list is not known at import time. |
| [`Source`](guides/source.md) | A field's value lives at a dotted attribute path, or under a different name. |
| [`MethodSource`](guides/source.md) | A field's value comes from calling a zero-argument model method. |
| [`SourceResolver`](guides/source.md#resolving-without-a-schema) | You want to resolve a path against an object without building a schema. |
| [`SourceResolutionError`](reference/errors.md) | You are catching a failed `Source` resolution. |

All of them are importable from the package root:

```pycon
>>> from django_modern_schemas import (
...     MethodSource,
...     ModelSchema,
...     Schema,
...     SchemaFactory,
...     Source,
...     SourceResolutionError,
...     SourceResolver,
... )

```

## How a schema is built

When you declare a `ModelSchema` subclass, the work happens at **class creation
time**, in the metaclass — not on every validation. In order:

1. `Config.model` is read. Without it, a `ConfigError` is raised.
2. The model's concrete fields are collected. Reverse relations
   (`ManyToOneRel`, `ManyToManyRel`) are skipped unless named explicitly.
3. `fields` / `exclude` narrow that set. Setting both is a `ConfigError`.
4. Each remaining Django field is converted to a `(python_type, FieldInfo)` pair
   carrying type, default, title, description and `max_length`.
5. Fields listed in `optional` — plus the primary key — are made non-required.
6. Any annotation you declared by hand on the class wins over the generated one.

That last step is what makes `Source` work: your annotation replaces the
generated field entirely.

```pycon
>>> class HandWrittenEventSchema(ModelSchema):
...     title: str  # overrides the generated CharField mapping
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> HandWrittenEventSchema.model_fields['title'].metadata
[]

```

Compare with the generated version, which carries the Django metadata:

```pycon
>>> class GeneratedEventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> GeneratedEventSchema.model_fields['title'].metadata
[MaxLen(max_length=100)]

```

## Reading Django instances

`ModelSchema` and `Schema` both set `from_attributes=True`, and validation runs
through an internal `DjangoGetter`. So `model_validate()` accepts a Django
instance, a mapping, or any object with the right attributes:

```pycon
>>> class CategorySchema(ModelSchema):
...     class Config:
...         model = models.Category
...         fields = ['name']
>>> CategorySchema.model_validate(models.Category(name='Python')).name
'Python'
>>> CategorySchema.model_validate({'name': 'Python'}).name
'Python'

```

## Boundaries

These are deliberate design decisions, not gaps to work around.

!!! warning "The library does not plan queries"

    Nothing here inspects your querysets or adds `select_related()` /
    `prefetch_related()` on your behalf. If a schema reaches across a relation,
    you are responsible for loading it efficiently — otherwise you get one query
    per instance. See [Relations → Query planning is yours](guides/relations.md#query-planning-is-yours).

!!! warning "Nested writes are application-specific"

    `create()` and `update()` write flat fields. A schema containing a nested
    schema raises `NotImplementedError` rather than guessing the order of
    writes, how to match existing children, or what to do with orphans. Override
    the method to express your own rule — see
    [Persistence → Nested models](guides/persistence.md#nested-models).

!!! warning "`Source` is read-only"

    `Source` and `MethodSource` fields are excluded from `create()` and
    `update()`. They describe how to read a value, not where to store it.

## Typical flow

1. Define a `ModelSchema` and select the fields exposed at your boundary.
2. Call `model_validate()` with a request mapping or a Django instance.
3. Use `model_dump()` for output, or `model_json_schema()` for an API contract.
4. For flat fields, use `create()` or `update(instance)` when the schema
   represents a write.

## Relationship to Ninja Schema

The conversion layer began from Ninja Schema's approach to turning Django fields
into Pydantic types. The differences that matter in use:

- Configuration is a nested `Config` class, validated eagerly at class creation.
- `Source` / `MethodSource` are first-class metadata, resolved by a dedicated
  `SourceResolver` with explicit rules about collections.
- Persistence helpers (`create()`, `update()`, `save()`) ship with the schema.

Full attribution is on the [Credits](project/credits.md) page.
