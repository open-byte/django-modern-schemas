# Django Choices

**Source:** [choices.py](choices.py)

`ModelSchema` converts Django `choices` into a Pydantic-compatible constrained
value. `StudentSchema` in the example accepts the configured semester values and
rejects values outside that set.

Use `model_validate()` for request data or `model_validate(instance)` for an ORM
instance. The generated JSON Schema exposes the allowed values for downstream
OpenAPI tooling.

The source is executed by `test_choices_example` in
[`tests/test_examples.py`](../tests/test_examples.py).