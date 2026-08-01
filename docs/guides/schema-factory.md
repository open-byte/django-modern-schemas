# SchemaFactory

Use `SchemaFactory` when the model shape is selected at runtime rather than
declared as a permanent class.

```python title="examples/schema_factory.py"
--8<-- "examples/schema_factory.py"
```

The factory returns a `ModelSchema` type. Validate and serialize it using the
same Pydantic v2 APIs as a class declared in source code.

`skip_registry=True` makes the example repeatable. Use the registry when a
stable configuration should reuse its generated schema; skip it when each call
must be isolated.