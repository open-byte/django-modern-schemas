# Source

**Source:** [source.py](source.py)

`Source` exposes a value from an attribute path under a different schema field
name. `MethodSource` explicitly invokes a zero-argument model method. The
example contains both forms:

- `EventSourceSchema` reads `category.name` and `display_title()`.
- `CategoryQuestionsSchema` exposes a prefetched reverse `ForeignKey` manager
  as a list of schemas.
- `resolve_category_name()` and `resolve_mapping_category_name()` demonstrate
  `SourceResolver` for object and mapping input when a full schema is not
  needed.

When an intermediate attribute is `None`, `Source` returns `None`. Reverse
`ForeignKey` collections are only supported as the final path segment and must
be loaded by the caller with `prefetch_related()`. The library does not plan
queries automatically.

These paths remain unsupported:

```python
Source('questions.text')       # Cannot traverse a reverse ForeignKey collection.
Source('questions[0].text')    # Index syntax is not supported.
Source('display_title()')      # Use MethodSource instead.
Source('tags')                 # ManyToMany paths are not supported.
```

Regular `ModelSchema` fields can still serialize `ManyToMany` values; see the
[relations example](relations.md).

`Source` and `MethodSource` are read-only metadata. Their fields are excluded
from `ModelSchema.create()` and `ModelSchema.update()`.

The source is executed by `test_source_example` and
`test_source_collection_example` in
[`tests/test_examples.py`](../tests/test_examples.py).