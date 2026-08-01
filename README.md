# Django Modern Schemas

`django-modern-schemas` generates Pydantic schemas from Django ORM models. It
reuses model types, constraints, defaults, choices, and supported relationships
to reduce duplication between the data and validation/serialization layers. The
library exposes `ModelSchema`, `Schema`, and `SchemaFactory` to define or
generate these schemas.

## Version

The project starts at version `0.0.1`.

## Requirements

- Python 3.10 or newer
- Django 3.2 or newer
- Pydantic 2.13.4 or newer

## Schema configuration

- `model`: the Django model used to build the schema.
- `fields`: fields exposed by the generated schema.
- `exclude`: fields to omit from the generated schema.
- `optional`: fields that should be optional.
- `depth`: the nesting depth for supported related models.

## Tutorials

- [Examples index](examples/README.md): tested Python examples and their documentation.
- [Basic Schema](examples/basic_schema.md): serialize ordinary Python objects.
- [ModelSchema](examples/model_schema.md): generate schemas from Django models.
- [SchemaFactory](examples/schema_factory.md): create a schema at runtime.
- [Django Choices](examples/choices.md): validate Django choices with Pydantic.
- [Source](examples/source.md): expose values from attributes, relations, and model methods.
- [Relations](examples/relations.md): serialize standard Django relation fields.
- [Persistence](examples/persistence.md): create and update Django models from validated input.

## Credits and acknowledgements

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