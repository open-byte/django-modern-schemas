# Django Choices

Django `choices` become constrained Pydantic values, so request validation and
generated JSON Schema reflect the model's allowed values.

## Django Model

The `choices` declaration remains on the Django model. `ModelSchema` reads that
metadata when it generates the Pydantic field.

```python title="examples/models.py"
--8<-- "examples/models.py:student-choices"
```

## Generated Schema

```python title="examples/choices.py"
--8<-- "examples/choices.py"
```

The example accepts the configured semester values and raises a Pydantic
validation error for an unknown value. This behavior works for input mappings
and ORM instances passed to `model_validate()`.