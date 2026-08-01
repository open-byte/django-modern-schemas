# Basic Schema

**Source:** [basic_schema.py](basic_schema.py)

Use `Schema` when a response is built from ordinary Python objects instead of a
Django model. The example serializes a member and its optional nested team with
`model_validate()` and `model_dump()`.

This is useful for DTOs, service-layer objects, or lightweight objects returned
by integrations. Pydantic field declarations, validators, and aliases remain
available because `Schema` extends `BaseModel`.

The source is executed by `test_basic_schema_example` in
[`tests/test_examples.py`](../tests/test_examples.py).