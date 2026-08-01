# ModelSchema Configuration

Configure a schema through its `Config` class or `model_config`. The model is
required for concrete `ModelSchema` classes.

| Option | Purpose |
| --- | --- |
| `model` | Django model used to generate fields. |
| `fields` | Explicit list of model fields to expose, or `"__all__"`. |
| `exclude` | Model fields to leave out; cannot be combined with `fields`. |
| `optional` | Fields that should accept omitted values, or `"__all__"`. |
| `depth` | Relation nesting depth. |
| `registry` | Schema registry used for related/generated schemas. |
| `skip_registry` | Avoid registry reuse for an isolated generated schema. |

## Example

```python
class EventSummarySchema(ModelSchema):
    class Config:
        model = Event
        fields = ["title"]
```

For a request shape, make only the intended fields optional:

```python
class EventPatchSchema(ModelSchema):
    class Config:
        model = Event
        fields = ["title"]
        optional = ["title"]
```

See the tested [ModelSchema guide](../guides/model-schema.md) for executable
examples.