# Getting Started

## Requirements

- Python 3.10 or newer
- Django 3.2 or newer
- Pydantic 2.13.4 or newer

## Install

=== "uv"

    ```bash
    uv add django-modern-schemas
    ```

=== "pip"

    ```bash
    pip install django-modern-schemas
    ```

## Define a ModelSchema

Import `ModelSchema`, declare the Django model, and choose the fields exposed by
the boundary. Use `fields`, not `include`.

```python title="examples/model_schema.py"
--8<-- "examples/model_schema.py"
```

Validate ORM objects with `model_validate()` and serialize them with
`model_dump()`:

```python
data = EventSummarySchema.model_validate(event).model_dump()
```

Replace the relative import from `examples.models` in the example with the model
from your Django application.

## Next Steps

- Learn how to select, exclude, and nest fields in the
  [ModelSchema guide](guides/model-schema.md).
- Use [Source and MethodSource](guides/source.md) for derived read-only output
  fields.
- Generate schemas dynamically with [SchemaFactory](guides/schema-factory.md).