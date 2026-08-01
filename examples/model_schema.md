# ModelSchema

**Source:** [model_schema.py](model_schema.py)

`ModelSchema` generates Pydantic fields from Django model metadata. The example
contains four schemas over the same `Event` model:

- `EventSummarySchema` uses `fields` to expose only `title`.
- `EventPatchSchema` makes the selected field optional.
- `EventWithoutCategorySchema` removes a model field with `exclude`.
- `EventWithCategorySchema` uses `depth=1` to include a related model schema.

Validate ORM instances with `model_validate(instance)` and serialize them with
`model_dump()`. Declared schema fields are retained even when they are not part
of `Config.fields`.

The source is executed by `test_model_schema_example` in
[`tests/test_examples.py`](../tests/test_examples.py).