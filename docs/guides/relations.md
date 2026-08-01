# Relations

Standard Django relations are supported as `ModelSchema` fields. Set `depth` to
generate nested schemas instead of serializing relation primary keys.

```python title="examples/relations.py"
--8<-- "examples/relations.py"
```

The example serializes a `Week` and its `ManyToMany` `Day` values. Prepare ORM
queries before serialization:

```python
week = Week.objects.prefetch_related("days").get(pk=week_id)
data = WeekSchema.model_validate(week).model_dump()
```

Query planning remains the application's responsibility. Use `select_related()`
for singular relationships and `prefetch_related()` for collections.