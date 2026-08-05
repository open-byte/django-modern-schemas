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

Declare the `_id` attribute explicitly and set it by primary key:

```pycon
>>> class EventWithCategorySchema(ModelSchema):
...     category_id: int | None = None
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> category = models.Category.objects.create(name='Python')
>>> created = EventWithCategorySchema.model_validate(
...     {'title': 'PyCon', 'category_id': category.pk}
... ).create()
>>> created.category_id == category.pk
True

```

!!! bug "The generated relation field cannot be written by primary key"

    A `ForeignKey` generated at `depth = 0` carries `category_id` as its alias,
    but the alias is not applied when the schema is dumped, so `create()` passes
    `category=1` to the manager and Django refuses it:

    ```pycon
    >>> class GeneratedFkSchema(ModelSchema):
    ...     class Config:
    ...         model = models.Event
    >>> GeneratedFkSchema.model_validate({'title': 'PyCon', 'category': category.pk}).create()
    Traceback (most recent call last):
        ...
    TypeError: Error creating Event instance: Cannot assign "1": "Event.category" must be a "Category" instance....

    ```

    This is the write-side counterpart of the read-side limitation described in
    [Relations → Forward relations at depth 0](relations.md#forward-relations-at-depth-0).
    Declare `category_id` yourself, as above, until it is addressed.

### Errors are wrapped

If the model rejects the data, the underlying exception is re-raised as a
`TypeError` naming the model:

```pycon
>>> class MismatchedSchema(ModelSchema):
...     not_a_model_field: str = 'x'
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> MismatchedSchema.model_validate({'title': 'DjangoCon'}).create()
Traceback (most recent call last):
    ...
TypeError: Error creating Event instance: ...

```

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

A schema containing a nested schema raises rather than guessing how to write it:

```pycon
>>> class CategorySchema(ModelSchema):
...     class Config:
...         model = models.Category
...         fields = ['name']
>>> class EventNestedWriteSchema(ModelSchema):
...     category: CategorySchema
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> EventNestedWriteSchema.model_validate(
...     {'title': 'DjangoCon', 'category': {'name': 'Python'}}
... ).create()
Traceback (most recent call last):
    ...
NotImplementedError: Creating models with child Pydantic models is not supported yet. Please override the `create` method in your schema.

```

This is deliberate. The library cannot know whether the nested object should be
created or looked up, in what order writes must happen, or what to do with
children that disappeared. Express your rule by overriding the method:

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

`update()` raises the same way, with a message naming `update`:

```pycon
>>> event = models.Event.objects.create(title='DjangoCon')
>>> EventNestedWriteSchema.model_validate(
...     {'title': 'DjangoCon', 'category': {'name': 'Python'}}
... ).update(event)
Traceback (most recent call last):
    ...
NotImplementedError: Updating models with child Pydantic models is not supported yet. Please override the `update` method in your schema.

```

## Validation happens before the database

Because persistence runs on an already-validated schema, invalid data never
reaches the ORM:

```pycon
>>> EventSchema.model_validate({'title': 'x' * 500})
Traceback (most recent call last):
    ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for EventSchema...

```

SQLite would have accepted that string; the schema did not.

## Related guides

- [ModelSchema → optional](model-schema.md#optional-relaxing-required-fields) — building PATCH schemas
- [Source and MethodSource](source.md) — read-only fields
- [Relations](relations.md) — writing foreign keys
