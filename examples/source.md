# Source Tutorial

`Source` exposes a value from a Django object under a different schema field
name. Declare it with `typing.Annotated`; Pydantic keeps the metadata and
`django-modern-schemas` resolves it when validating an object.

## One-to-one attributes

Given these models:

```python
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)


class Event(models.Model):
    title = models.CharField(max_length=100)
    category = models.OneToOneField(
        Category,
        null=True,
        on_delete=models.SET_NULL,
    )
```

Expose the category name without creating a nested schema:

```python
from typing import Annotated

from django_modern_schemas import ModelSchema, Source


class EventSchema(ModelSchema):
    category_name: Annotated[str | None, Source('category.name')]

    class Config:
        model = Event
        fields = ['title']
```

```python
event = Event(title='DjangoCon', category=Category(name='Python'))
schema = EventSchema.model_validate(event)

assert schema.category_name == 'Python'
```

If `event.category` is `None`, the resolver returns `None`. Make the schema
field optional when that is a valid result.

## Model methods

Use `MethodSource` for a zero-argument method. Methods are never called
implicitly by `Source`.

```python
from typing import Annotated

from django_modern_schemas import MethodSource, ModelSchema


class EventSchema(ModelSchema):
    display_title: Annotated[str, MethodSource('get_display_title')]

    class Config:
        model = Event
        fields = ['title']
```

`get_display_title` must be defined on `Event`, be callable, and accept no
arguments. Otherwise validation reports a source resolution error.

## Reverse ForeignKey collections

A reverse `ForeignKey` is allowed only as the final path segment. It is exposed
as a list and should be prefetched by the caller.

```python
class Question(models.Model):
    text = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        related_name='questions',
        on_delete=models.CASCADE,
    )
```

```python
from typing import Annotated

from django_modern_schemas import ModelSchema, Source


class QuestionSchema(ModelSchema):
    class Config:
        model = Question
        fields = ['text']


class CategorySchema(ModelSchema):
    questions: Annotated[list[QuestionSchema], Source('questions')]

    class Config:
        model = Category
        fields = ['name']


category = Category.objects.prefetch_related('questions').get(pk=category_id)
schema = CategorySchema.model_validate(category)
```

The library does not add `select_related()` or `prefetch_related()` calls. Query
planning remains the caller's responsibility.

## Supported paths and limits

`Source` paths are dotted Python attribute names. This first version supports:

- Direct and nested singular attributes, including forward and reverse
  `OneToOneField` relations.
- A reverse `ForeignKey` manager only as the final segment.
- Explicit zero-argument model methods through `MethodSource`.

These paths are intentionally unsupported:

```python
Source('questions.text')       # Cannot traverse a reverse ForeignKey collection.
Source('questions[0].text')    # Index syntax is not supported.
Source('get_display_title()')  # Use MethodSource instead.
Source('tags')                 # ManyToMany relations are not supported yet.
```

`Source` and `MethodSource` are read-only metadata. Their fields are excluded
from `ModelSchema.create()` and `ModelSchema.update()`.