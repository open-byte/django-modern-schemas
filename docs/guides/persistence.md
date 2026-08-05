# Persistence

A validated schema can write itself back through the ORM with three methods:

| Method | Effect |
| --- | --- |
| `create()` | Creates a new row via the model's default manager. |
| `update(instance, partial=False)` | Assigns fields onto an existing instance and saves it. |
| `save(instance=None, partial=None)` | Creates or updates, depending on what it is given. |

```python title="models.py"
--8<-- "examples/models.py:event-model"
```

## `create()`

`create()` takes the validated data and calls `Model._default_manager.create()`:

```pycon
>>> class EventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         exclude = ['category']
>>> event = EventSchema.model_validate({'title': 'DjangoCon'}).create()
>>> event.pk is not None
True
>>> event.title
'DjangoCon'

```

The return value is a real Django instance, so it is immediately usable:

```pycon
>>> models.Event.objects.filter(title='DjangoCon').count()
1

```

### Writing a foreign key

Set the relation by primary key. The schema dumps with `by_alias=True`, so the
value reaches the manager as Django's `category_id`:

```pycon
>>> class EventWithCategorySchema(ModelSchema):
...     class Config:
...         model = models.Event
>>> category = models.Category.objects.create(name='Python')
>>> created = EventWithCategorySchema.model_validate(
...     {'title': 'PyCon', 'category': category.pk}
... ).create()
>>> created.category_id == category.pk
True

```

`create()` detects that `category` is a relation and hands the ORM
`category_id`, which is the only form Django accepts for a primary key.

!!! note "`OneToOneField` is unique"

    `Event.category` is a `OneToOneField`, so a second `Event` pointing at the
    same `Category` raises an `IntegrityError` — that is Django enforcing the
    relation, not a schema problem.

### Writing a many-to-many

Many-to-many values cannot be passed to `create()` — the relation needs a saved
row to attach to — so they are applied right after the instance exists:

```python title="models.py"
--8<-- "examples/models.py:week-models"
```

```pycon
>>> class WeekSchema(ModelSchema):
...     class Config:
...         model = models.Week
...         fields = ['name', 'days']
>>> monday = models.Day.objects.create(name='Monday')
>>> tuesday = models.Day.objects.create(name='Tuesday')
>>> week = WeekSchema.model_validate({'name': 'Week 1', 'days': [monday.pk, tuesday.pk]}).create()
>>> [day.name for day in week.days.all()]
['Monday', 'Tuesday']

```

!!! tip "If a schema field is not a model field"

    A writable field that the model's manager does not accept raises a
    `TypeError` naming the model and suggesting the fix — make the field
    read-only, or override `create()`. See the
    [errors reference](../reference/errors.md).

## `update()`

`update()` assigns each dumped field onto the instance and saves it:

```pycon
>>> event = models.Event.objects.create(title='DjangoCon')
>>> updated = EventSchema.model_validate({'id': event.pk, 'title': 'PyCon'}).update(event)
>>> models.Event.objects.get(pk=event.pk).title
'PyCon'

```

The instance you passed in is the instance returned — it is mutated in place:

```pycon
>>> updated is event
True

```

### Partial updates

By default **every** field on the schema is written, including fields that fell
back to their default. Compare the two modes on a schema where `rating` was
never supplied:

```pycon
>>> class ProfilePatchSchema(ModelSchema):
...     class Config:
...         model = models.SpeakerProfile
...         fields = ['full_name', 'rating']
...         optional = ['full_name', 'rating']

```

=== "`partial=False` (default)"

    Unset fields are written, overwriting the stored value with the default:

    ```pycon
    >>> profile = models.SpeakerProfile.objects.create(uuid=uuid4(), full_name='Ada', rating=9.5)
    >>> _ = ProfilePatchSchema.model_validate({'full_name': 'Ada Lovelace'}).update(profile)
    >>> models.SpeakerProfile.objects.get(pk=profile.pk).rating is None
    True

    ```

=== "`partial=True`"

    Only fields explicitly present in the input are written:

    ```pycon
    >>> profile = models.SpeakerProfile.objects.create(uuid=uuid4(), full_name='Ada', rating=9.5)
    >>> _ = ProfilePatchSchema.model_validate({'full_name': 'Ada Lovelace'}).update(profile, partial=True)
    >>> refreshed = models.SpeakerProfile.objects.get(pk=profile.pk)
    >>> refreshed.full_name, refreshed.rating
    ('Ada Lovelace', 9.5)

    ```

!!! warning "Use `partial=True` for PATCH endpoints"

    With `partial=False`, a schema built from a sparse payload will blank out
    every column the client did not mention — and on a `NOT NULL` column that is
    an `IntegrityError` rather than a silent overwrite. `partial=True` uses
    `exclude_unset=True`, so absent keys stay absent.

## `save()`

`save()` picks the operation for you:

```pycon
>>> schema = EventSchema.model_validate({'title': 'New Event'})
>>> created = schema.save()             # no instance -> create
>>> created.pk is not None
True
>>> existing = models.Event.objects.create(title='Old title')
>>> _ = EventSchema.model_validate({'title': 'New title'}).save(existing)
>>> models.Event.objects.get(pk=existing.pk).title
'New title'

```

The resolution order is: an internal `_object` if one is set, then the
`instance` argument, then `create()`.

## Source fields are skipped

`Source` and `MethodSource` fields are read-only and never written — see
[Source fields are never written](source.md#source-fields-are-never-written).

```pycon
>>> class EventSourceSchema(ModelSchema):
...     category_name: Annotated[str, Source('category.name')]
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> created = EventSourceSchema.model_validate(
...     {'title': 'DjangoCon', 'category_name': 'Python'}
... ).create()
>>> created.title
'DjangoCon'
>>> created.category is None
True

```

## Nested models

A schema containing a nested schema does not write itself. The library cannot
know whether the nested object should be created or looked up, in what order the
writes must happen, or what to do with children that disappeared — so it raises
`NotImplementedError` and asks you to say. Express the rule by overriding the
method:

```python title="schemas.py"
class EventNestedWriteSchema(ModelSchema):
    category: CategorySchema

    class Config:
        model = Event
        fields = ['title']

    def create(self, *args, **kwargs):
        category, _ = Category.objects.get_or_create(name=self.category.name)
        return Event.objects.create(title=self.title, category=category)

    def update(self, instance, partial=False, **kwargs):
        category, _ = Category.objects.get_or_create(name=self.category.name)
        instance.title = self.title
        instance.category = category
        instance.save()
        return instance
```

Both `create()` and `update()` behave this way. If the nested object is only
ever read, mark it with [`Source`](source.md) instead and the problem disappears
— source fields are skipped on write.

## Validation happens before the database

Persistence runs on an already-validated schema, so constraints declared on the
Django field are enforced before any SQL is issued. `Event.title` is
`max_length=100`, and SQLite would happily have stored a longer string:

```pycon
>>> schema = EventSchema.model_validate({'title': 'DjangoCon'})
>>> schema.title
'DjangoCon'

```

A payload violating that limit never reaches `create()` — it is rejected by
`model_validate()` with a Pydantic `ValidationError`, which is the error you
return to the client as a 400.

## Related guides

- [ModelSchema → optional](model-schema.md#optional-relaxing-required-fields) — building PATCH schemas
- [Source and MethodSource](source.md) — read-only fields
- [Relations](relations.md) — writing foreign keys
