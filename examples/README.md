# Examples

Each example has a Python source file that is exercised by
[`tests/test_examples.py`](../tests/test_examples.py). The Python files are the
source of truth for snippets used in documentation, so they can be copied into
an application without duplicating stale code blocks across guides.

## Example Plan

1. [Basic Schema](basic_schema.md) shows Pydantic serialization of ordinary
   attribute-based objects through `Schema`.
2. [ModelSchema](model_schema.md) covers generated model fields and the
   `fields`, `exclude`, `optional`, and `depth` configuration options.
3. [SchemaFactory](schema_factory.md) creates a schema dynamically at runtime.
4. [Choices](choices.md) maps Django `choices` to Pydantic validation.
5. [Source](source.md) reads nested attributes, explicit model methods, and
   prefetched reverse `ForeignKey` collections.
6. [Relations](relations.md) serializes standard Django relation fields,
   including nested `ManyToMany` values.
7. [Persistence](persistence.md) creates and updates Django model instances
   from validated schema input.

## Running The Examples

Run the example suite from the repository root:

```bash
PYTHONPATH="$PWD/tests/testapp" uv run --group tests pytest tests/test_examples.py
```

The example models use a small in-memory Django configuration so they can be
tested in this repository. In an application, replace the imports from
`examples.models` with models from the application's Django app.