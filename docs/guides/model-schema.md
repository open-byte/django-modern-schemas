# ModelSchema

`ModelSchema` inspects Django fields and builds a Pydantic model. The example
uses one `Event` model to show the main configuration patterns.

```python title="examples/model_schema.py"
--8<-- "examples/model_schema.py"
```

## Choosing a Shape

| Schema | Intent |
| --- | --- |
| `EventSummarySchema` | Expose a small response shape with `fields`. |
| `EventPatchSchema` | Make selected fields optional for patch-like input. |
| `EventWithoutCategorySchema` | Start from the model and remove a field with `exclude`. |
| `EventWithCategorySchema` | Use `depth=1` to nest a related schema. |

!!! warning "Use one selection strategy"

    `fields` and `exclude` are mutually exclusive. A schema should make its
    boundary explicit rather than mixing inclusion and exclusion rules.

See the [configuration reference](../reference/configuration.md) for the full
set of options.