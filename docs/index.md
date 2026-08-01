# Django Modern Schemas

**Django Modern Schemas** is an [Open Byte](https://github.com/open-byte)
project that turns Django ORM metadata into Pydantic v2 schemas for validation,
serialization, and JSON Schema generation.

[Get started](getting-started.md){ .md-button .md-button--primary }
[Read the overview](overview.md){ .md-button }
[Browse guides](guides/basic-schema.md){ .md-button }

## Django Models, Typed Boundaries

Use Django models as the source of ORM metadata and Pydantic as the boundary for
validated input, serialized output, and JSON Schema.

```text
Django model -> ModelSchema -> Pydantic validation and serialization
```

## A First Schema

`Schema` can serialize ordinary attribute-based objects, not only Django models.
The code below is rendered directly from a tested Python example in this
repository.

```python title="examples/basic_schema.py"
--8<-- "examples/basic_schema.py"
```

!!! tip "Examples stay executable"

	Every guide includes a Python file from `examples/`. The example test suite
	executes those files, and the docs build fails when an included file is
	missing.