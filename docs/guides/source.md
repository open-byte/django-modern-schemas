# Source and MethodSource

Use `Source` to expose an attribute under a different schema field name. Use
`MethodSource` when a value must come from an explicit zero-argument model
method.

```python title="examples/source.py"
--8<-- "examples/source.py"
```

`EventSourceSchema` exposes `category.name` as `category_name` and calls
`display_title()` only because it is declared with `MethodSource`.

## Relation Rules

- Singular forward and reverse attributes can be traversed with dotted paths.
- `None` at any intermediate point resolves to `None`.
- A reverse `ForeignKey` collection is supported only as the final path segment.
- Load reverse collections deliberately with `prefetch_related()`.

!!! warning "Collections are not path traversal"

    `Source("questions.text")`, indexed paths, and `ManyToMany` source paths
    are intentionally unsupported. Use a nested schema for regular relation
    serialization instead.

Source-derived fields are read-only and are excluded from `create()` and
`update()` operations.