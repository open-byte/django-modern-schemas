# SchemaFactory

**Source:** [schema_factory.py](schema_factory.py)

Use `SchemaFactory.create_schema()` when the selected model fields are known at
runtime. The example creates `EventTitleSchema` with only `title`, then uses the
generated type with `model_validate()`.

`skip_registry=True` keeps the example isolated. Omit it when a schema should
be reused through the registry; use it when each call needs a configuration
that must not share cached state.

The source is executed by `test_schema_factory_example` in
[`tests/test_examples.py`](../tests/test_examples.py).