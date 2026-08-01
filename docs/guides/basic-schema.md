# Basic Schema

Use `Schema` when data comes from an ordinary Python object rather than directly
from a Django model. It retains Pydantic validation while reading attribute-based
objects through `model_validate()`.

```python title="examples/basic_schema.py"
--8<-- "examples/basic_schema.py"
```

`MemberSchema` demonstrates a nested object and an optional relation. This is a
good fit for service-layer DTOs, integration results, or presentation objects
that do not need Django model introspection.

!!! note "Pydantic APIs remain available"

    `Schema` is a Pydantic model. Use validators, aliases, `model_dump()`, and
    JSON Schema exactly as you would with Pydantic v2.