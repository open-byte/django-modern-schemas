# How These Docs Are Tested

Every console transcript on this site is a test. If the library's behaviour
changes, the affected page fails in CI — documentation cannot silently drift.

## The mechanism

Pages are collected by pytest as doctests:

```toml title="pyproject.toml"
[tool.pytest.ini_options]
addopts = "--doctest-glob=*.md --doctest-continue-on-failure"
testpaths = ["tests", "docs"]
doctest_optionflags = ["NORMALIZE_WHITESPACE", "ELLIPSIS", "IGNORE_EXCEPTION_DETAIL"]
```

A block written like this:

````markdown
```pycon
>>> class EventSchema(ModelSchema):
...     class Config:
...         model = models.Event
...         fields = ['title']
>>> EventSchema.model_validate(models.Event(title='DjangoCon')).model_dump()
{'title': 'DjangoCon'}

```
````

…is executed, and the line after the prompt is compared against what the library
actually returned.

## What the examples run against

`docs/conftest.py` gives every page a database and a preloaded namespace, so the
pages stay readable without a setup block at the top of each one:

| Name | Value |
| --- | --- |
| `models` | `examples/models.py` — the models shown in the guides |
| `ModelSchema`, `Schema`, `SchemaFactory` | The public schema classes |
| `Source`, `MethodSource`, `SourceResolver`, `SourceResolutionError` | Source metadata API |
| `Annotated`, `json`, `uuid4` | Standard-library helpers |

The database is a real (in-memory) SQLite database provided by
`pytest-django`, rolled back between pages. Examples that call
`objects.create()` are doing real ORM work.

## Running them

```bash
# every page
uv run pytest docs/

# one page
uv run pytest docs/guides/source.md
```

A failure prints the expected and actual output side by side, pointing at the
line in the Markdown file:

```text
File "docs/guides/source.md", line 42, in source.md
Failed example:
    EventSchema.model_validate(event).model_dump()
Expected:
    {'title': 'DjangoCon', 'category_name': 'Django'}
Got:
    {'title': 'DjangoCon', 'category_name': 'Python'}
```

## Writing a new example

1. Use a ` ```pycon ` fence and `>>>` prompts.
2. **Leave a blank line before the closing fence.** doctest reads expected
   output until a blank line; without one it tries to match the ` ``` ` too.
3. Use names from the table above rather than adding imports, unless the import
   is itself the point of the example.
4. Prefer showing a real value over asserting `True`. `model_dump()` output is
   more useful to a reader than `assert x == y`.
5. Run the page. Do not hand-write the expected output — paste what the library
   produced, once you have confirmed it is correct.

For long output, `print(json.dumps(..., indent=2))` reads better than a raw
dict, and `NORMALIZE_WHITESPACE` keeps it robust.

### Exceptions

Show the traceback in doctest form:

````markdown
```pycon
>>> Source('')
Traceback (most recent call last):
    ...
ValueError: Source path cannot be empty.

```
````

When only part of a long message matters, end it with `...` — `ELLIPSIS` is
enabled.

## Snippets from real files

Model definitions are included from `examples/models.py` with
[pymdownx.snippets](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/),
so the models shown are the models the examples import:

````markdown
```python title="models.py"
--8<-- "examples/models.py:event-model"
```
````

The markers live in the Python file:

```python
# --8<-- [start:event-model]
class Event(models.Model):
    ...
# --8<-- [end:event-model]
```

`mkdocs build --strict` fails if a referenced snippet or marker is missing.

## In CI

The documentation build and the doctests both run on every push. A page whose
output no longer matches fails the build in the same way a unit test does.

## Related pages

- [Publishing Documentation](publishing.md) — how the site is deployed
- [Credits and Stewardship](credits.md)
