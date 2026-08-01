# Persistence

`ModelSchema` can validate input before creating or updating an existing Django
model instance.

```python title="examples/persistence.py"
--8<-- "examples/persistence.py"
```

The example keeps the operation explicit:

- `create_event()` validates input and calls `create()`.
- `rename_event()` validates input and calls `update(instance)`.

!!! tip "Keep write schemas narrow"

    Include only fields that can be written directly to the Django model.
    `Source` and `MethodSource` fields are output-only and are never persisted.

!!! warning "Nested models require custom persistence"

    The built-in `create()` and `update()` operations only handle direct model
    fields. When a write schema contains nested Pydantic models, override both
    `create()` and `update()` in the schema and explicitly create or update the
    related Django objects. The default operations intentionally raise
    `NotImplementedError` for nested models.