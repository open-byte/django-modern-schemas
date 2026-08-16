# Basic Schema

`Schema` is a thin subclass of Pydantic's `BaseModel` with `from_attributes`
already enabled. Use it when there is **no Django model involved** — plain
objects, service results, dataclasses, third-party payloads.

For fields generated from a Django model, use
[`ModelSchema`](model-schema.md) instead.

## Reading attributes off any object

You declare the fields yourself; nothing is generated:

```pycon
>>> class TeamSchema(Schema):
...     name: str
>>> class MemberSchema(Schema):
...     name: str
...     team: TeamSchema | None = None

```

Any object with matching attributes validates:

```pycon
>>> class Team:
...     def __init__(self, name):
...         self.name = name
>>> class Member:
...     def __init__(self, name, team=None):
...         self.name = name
...         self.team = team
>>> MemberSchema.model_validate(Member('Ada', Team('Platform'))).model_dump()
{'name': 'Ada', 'team': {'name': 'Platform'}}

```

That is the one thing `Schema` adds over a bare `BaseModel`:

```pycon
>>> Schema.model_config['from_attributes']
True

```

Mappings work equally well:

```pycon
>>> MemberSchema.model_validate({'name': 'Ada', 'team': {'name': 'Platform'}}).model_dump()
{'name': 'Ada', 'team': {'name': 'Platform'}}

```

Missing optional values fall back to the declared default:

```pycon
>>> MemberSchema.model_validate(Member('Ada')).model_dump()
{'name': 'Ada', 'team': None}

```

## It is a normal Pydantic model

Validators, serializers and JSON Schema behave exactly as they do in Pydantic:

```pycon
>>> from pydantic import computed_field, field_validator
>>> class NormalisedTeamSchema(Schema):
...     name: str
...     @field_validator('name')
...     @classmethod
...     def normalise(cls, value):
...         return value.strip().title()
...     @computed_field
...     @property
...     def slug(self) -> str:
...         return self.name.lower().replace(' ', '-')
>>> NormalisedTeamSchema.model_validate({'name': '  platform team '}).model_dump()
{'name': 'Platform Team', 'slug': 'platform-team'}

```

## Nesting it inside a ModelSchema

A `Schema` is a good shape for a value that is not a model field — a computed
block, or an external payload:

```pycon
>>> class TitleInfoSchema(Schema):
...     label: str
>>> class EventInfoSchema(ModelSchema):
...     info: TitleInfoSchema
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> EventInfoSchema.model_validate(
...     {'title': 'DjangoCon', 'info': {'label': 'Event: DjangoCon'}}
... ).model_dump()
{'title': 'DjangoCon', 'info': {'label': 'Event: DjangoCon'}}

```

!!! warning "Nested schemas disable the built-in persistence"

    A schema containing another schema cannot be written by `create()` or
    `update()` — see [Persistence → Nested models](persistence.md#nested-models).

## When to use which

| | `Schema` | `ModelSchema` |
| --- | --- | --- |
| Fields | You declare them | Generated from the model |
| Requires `Config.model` | No | Yes |
| `create()` / `update()` | Not available | Available |
| `Source` / `MethodSource` | Resolved | Resolved, and read-only |

!!! tip "`Source` works here too"

    Both classes install the same getter, so an attribute path resolves on a
    plain `Schema` without any Django model in sight:

    ```pycon
    >>> class PlainSourceSchema(Schema):
    ...     category_name: Annotated[str, Source('category.name')]
    >>> PlainSourceSchema.model_validate({'category': {'name': 'Python'}}).category_name
    'Python'

    ```

    `MethodSource` likewise calls a method on any object:

    ```pycon
    >>> class Report:
    ...     def headline(self):
    ...         return 'Quarterly report'
    >>> class ReportSchema(Schema):
    ...     headline: Annotated[str, MethodSource('headline')]
    >>> ReportSchema.model_validate(Report()).headline
    'Quarterly report'

    ```

    What `Schema` does not give you is field generation or persistence.

## Related guides

- [ModelSchema](model-schema.md) — generating fields from a Django model
- [Source and MethodSource](source.md) — computed and renamed fields
