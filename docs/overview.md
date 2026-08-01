# Overview

Django Modern Schemas connects Django ORM models with Pydantic v2. Django stays
the source of model and relation metadata; Pydantic provides validation,
serialization, and JSON Schema at the boundary of an application.

```text
Django model
    -> ModelSchema
    -> Pydantic validation, serialization, and JSON Schema
```

## What It Solves

A Django model already describes important data constraints: field types,
defaults, nullable values, choices, and relationships. Re-declaring those rules
in a separate Pydantic model is repetitive and can drift over time.

`ModelSchema` reads the Django model metadata and produces a Pydantic model that
can validate input mappings or serialize ORM instances through
`model_validate()`.

## Core Building Blocks

| API | Use it when |
| --- | --- |
| `Schema` | You need to serialize ordinary attribute-based Python objects. |
| `ModelSchema` | You want a Pydantic schema generated from a Django model. |
| `SchemaFactory` | The selected fields or configuration are only known at runtime. |
| `Source` | A response field should read from a different Django attribute path. |
| `MethodSource` | A response field should call an explicit zero-argument model method. |

## Typical Flow

1. Define a `ModelSchema` and select the fields exposed at the boundary.
2. Call `model_validate()` with a request mapping or Django instance.
3. Use `model_dump()` for output, or inspect `model_json_schema()` for an API
   contract.
4. For direct model fields, use `create()` or `update(instance)` when the
   schema represents a write operation.

## Boundaries and Responsibilities

!!! info "Query loading remains explicit"

    Django Modern Schemas does not decide when to load relations. Use
    `select_related()` and `prefetch_related()` in the calling queryset to
    control query count and avoid N+1 behavior.

!!! warning "Nested writes are application-specific"

    The built-in `create()` and `update()` methods handle direct model fields.
    When a write schema contains nested Pydantic models, override `create()`
    and `update()` to create or update the related Django objects explicitly.

!!! tip "Source fields are output-only"

    `Source` and `MethodSource` are designed for reading values from an object.
    They are excluded from default persistence operations.

## Next Steps

- Start with [Getting Started](getting-started.md) for a minimal schema.
- Read [ModelSchema](guides/model-schema.md) to control generated fields.
- Use [Source and MethodSource](guides/source.md) for derived response fields.
- Browse the [tested example guides](guides/basic-schema.md) for complete
    Python files rendered directly in the documentation.