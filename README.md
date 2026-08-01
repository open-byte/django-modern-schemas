# Django Modern Schemas

`django-modern-schemas` generates Pydantic schemas from Django ORM models. It
reuses model types, constraints, defaults, choices, and supported relationships
to reduce duplication between the data and validation/serialization layers. The
library exposes `ModelSchema`, `Schema`, and `SchemaFactory` to define or
generate these schemas. It is maintained by
[Open Byte](https://github.com/open-byte).

## Version

The project starts at version `0.0.1`.

## Requirements

- Python 3.10 or newer
- Django 3.2 or newer
- Pydantic 2.13.4 or newer

## Documentation

The documentation site is built with
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). Its source
lives in [docs](docs/index.md) and renders the tested Python examples directly.

```bash
uv sync --group docs
uv run --group docs mkdocs serve
```

- [Getting Started](docs/getting-started.md)
- [Overview](docs/overview.md)
- [ModelSchema Guide](docs/guides/model-schema.md)
- [Source and MethodSource Guide](docs/guides/source.md)
- [Configuration Reference](docs/reference/configuration.md)
- [Credits and Stewardship](docs/project/credits.md)
- [Publishing Documentation](docs/project/publishing.md)

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