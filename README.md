# Django Modern Schemas

`django-modern-schemas` generates Pydantic schemas from Django ORM models. It
reuses model types, constraints, defaults, choices, and supported relationships
to reduce duplication between the data and validation/serialization layers. The
library exposes `ModelSchema`, `Schema`, and `SchemaFactory` to define or
generate these schemas. It is maintained by
[Open Byte](https://github.com/open-byte).

📚 **Full documentation: [open-byte.github.io/django-modern-schemas](https://open-byte.github.io/django-modern-schemas/)**

## Version

The project starts at version `0.0.1`.

## Requirements

- Python 3.10 or newer
- Django 3.2 or newer
- Pydantic 2.13.4 or newer

## Quick start

```bash
pip install django-modern-schemas
```

Nothing goes into `INSTALLED_APPS` — schemas are ordinary Python classes.

Start from a model you already have — `models.py`:

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)


class Article(models.Model):
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True, default='')
    views = models.PositiveIntegerField(default=0)
    published = models.BooleanField(default=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
```

Point a schema at it. The fields, their types, their constraints, and their
defaults are read from the model — you restate none of them in `schemas.py`:

```python
from django_modern_schemas import ModelSchema

from .models import Article


class ArticleSchema(ModelSchema[Article]):
    class Config:
        model = Article
```

`ModelSchema` is generic in its model. The parameter is free at runtime and
makes `create()`, `update()`, and `save()` typed as returning `Article`, so your
type checker follows the value all the way into the rest of the view.

```pycon
>>> list(ArticleSchema.model_fields)
['id', 'title', 'body', 'views', 'published', 'author']
```

### Validate input

`max_length=120` was declared once, on the column, and it is enforced before any
SQL runs. `ValidationError.errors()` is already shaped like a 400 response body:

```pycon
>>> ArticleSchema.model_validate({'title': 'x' * 200, 'author': 1})
Traceback (most recent call last):
    ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for ArticleSchema
title
  String should have at most 120 characters [type=string_too_long, ...]
```

### Write it to the database

```pycon
>>> author = Author.objects.create(name='Ada Lovelace')
>>> article = ArticleSchema.model_validate(
...     {'title': 'Schemas from models', 'body': 'One source of truth.', 'author': author.pk}
... ).create()
>>> article.pk is not None
True
```

### Serialize it back out

The same class reads a Django instance, so one schema covers both directions:

```pycon
>>> ArticleSchema.model_validate(article).model_dump()
{'id': 1, 'title': 'Schemas from models', 'body': 'One source of truth.', 'views': 0, 'published': False, 'author': 1}
>>> ArticleSchema.model_validate(article).model_dump_json()
'{"id":1,"title":"Schemas from models","body":"One source of truth.","views":0,"published":false,"author":1}'
```

### Round trip: read, edit, save

A schema validated from an instance stays bound to it, so `save()` updates that
row instead of inserting a new one — no bookkeeping on your side:

```pycon
>>> schema = ArticleSchema.model_validate(article)
>>> schema.title = 'Schemas from models, revisited'
>>> saved = schema.save()
>>> saved.pk == article.pk
True
>>> Article.objects.get(pk=article.pk).title
'Schemas from models, revisited'
>>> Article.objects.count()   # updated in place, not duplicated
1
```

### PATCH endpoints

Mark fields `optional` and update with `partial=True`, and keys the client never
sent are never written:

```python
class ArticlePatchSchema(ModelSchema[Article]):
    class Config:
        model = Article
        fields = ['title', 'published']
        optional = ['title', 'published']
```

```pycon
>>> Article.objects.filter(pk=article.pk).update(views=42)   # the article got some traffic
1
>>> article.refresh_from_db()
>>> ArticlePatchSchema.model_validate({'published': True}).update(article, partial=True).published
True
>>> Article.objects.get(pk=article.pk).views   # untouched by the patch
42
```

Without `partial=True` that same payload would write `views` back to its default
and undo the count.

### Publish the contract

`model_json_schema()` hands OpenAPI tooling a description generated from the
model, `maxLength` and defaults included:

```pycon
>>> ArticleSchema.model_json_schema()['required']
['title', 'author']
>>> ArticleSchema.model_json_schema()['properties']['title']['maxLength']
120
```

From here: [Getting Started](https://open-byte.github.io/django-modern-schemas/getting-started/)
walks the same ground in more detail, and
[Relations](https://open-byte.github.io/django-modern-schemas/guides/relations/)
covers foreign keys, many-to-many, and nesting with `depth`.

## Documentation

The documentation site is published at
[open-byte.github.io/django-modern-schemas](https://open-byte.github.io/django-modern-schemas/).
It is built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/),
its source lives in [docs](docs/index.md), and every Python example on it is
executed by the test suite — a drifting example fails the build.

```bash
uv sync --group docs
uv run --group docs mkdocs serve
```

- [Getting Started](https://open-byte.github.io/django-modern-schemas/getting-started/)
- [Overview](https://open-byte.github.io/django-modern-schemas/overview/)
- [ModelSchema Guide](https://open-byte.github.io/django-modern-schemas/guides/model-schema/)
- [Relations Guide](https://open-byte.github.io/django-modern-schemas/guides/relations/)
- [Persistence Guide](https://open-byte.github.io/django-modern-schemas/guides/persistence/)
- [Source and MethodSource Guide](https://open-byte.github.io/django-modern-schemas/guides/source/)
- [Configuration Reference](https://open-byte.github.io/django-modern-schemas/reference/configuration/)
- [Credits and Stewardship](https://open-byte.github.io/django-modern-schemas/project/credits/)
- [Publishing Documentation](https://open-byte.github.io/django-modern-schemas/project/publishing/)

## Schema configuration

- `model`: the Django model used to build the schema.
- `fields`: fields exposed by the generated schema.
- `exclude`: fields to omit from the generated schema.
- `optional`: fields that should be optional.
- `depth`: the nesting depth for supported related models.

## Tutorials

- [Examples index](examples/README.md): tested executable Python examples.

## Credits and acknowledgements

Django Modern Schemas is maintained by
[Open Byte](https://github.com/open-byte).

This project is a new evolution of [Ninja Schema](https://github.com/eadwinCode/ninja-schema)
and is developed with the original creator's permission.

Special thanks and full recognition go to
[Tochukwu (@eadwinCode)](https://github.com/eadwinCode), the creator of
[Ninja Schema](https://github.com/eadwinCode/ninja-schema) and
[Django Ninja Extra](https://github.com/eadwinCode/django-ninja-extra). Thank
you for the effort, design, and work invested in both libraries, and for
granting permission to modify and create this new implementation so that the
idea can continue. The original work is credited to him.

**Inspired by:** [Django Ninja](https://django-ninja.dev/) and [djantic](https://jordaneremieff.github.io/djantic/).