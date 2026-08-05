# Django Choices

A field declared with `choices` becomes a generated Python `Enum`, so the
allowed values are enforced during validation and published in the JSON Schema.

## The model

The `choices` declaration stays where it belongs — on the Django model:

```python title="models.py"
--8<-- "examples/models.py:student-choices"
```

## The generated field

```pycon
>>> class StudentSchema(ModelSchema):
...     class Config:
...         model = models.Student
...         fields = ['semester']
>>> StudentSchema.model_fields['semester'].annotation
<enum 'SemesterEnum'>

```

The enum is named after the field and built from the `choices` pairs. Its
*members* come from the display labels, and its *values* from the stored values:

```pycon
>>> enum = StudentSchema.model_fields['semester'].annotation
>>> [(member.name, member.value) for member in enum]
[('One', '1'), ('Two', '2'), ('Three', '3')]

```

The enum subclasses the type of the stored value, so it compares equal to a
plain string:

```pycon
>>> issubclass(enum, str)
True
>>> enum.One == '1'
True

```

## Validation

A configured value is accepted, whichever form you pass:

```pycon
>>> StudentSchema.model_validate({'semester': '1'}).semester
<SemesterEnum.One: '1'>
>>> StudentSchema.model_validate({'semester': enum.Two}).semester
<SemesterEnum.Two: '2'>

```

Anything else is rejected:

```pycon
>>> StudentSchema.model_validate({'semester': '9'})
Traceback (most recent call last):
    ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for StudentSchema...

```

The error names the permitted values, which makes it directly usable in an API
response:

```pycon
>>> try:
...     StudentSchema.model_validate({'semester': '9'})
... except Exception as error:
...     print(error.errors()[0]['msg'])
Input should be '1', '2' or '3'

```

## Serialization

`model_dump()` returns the enum member, and JSON mode returns the stored value:

```pycon
>>> StudentSchema.model_validate({'semester': '1'}).model_dump()
{'semester': <SemesterEnum.One: '1'>}
>>> StudentSchema.model_validate({'semester': '1'}).model_dump_json()
'{"semester":"1"}'

```

!!! tip "Use `mode='json'` for API responses"

    `model_dump()` keeps the rich enum member, which is convenient in Python but
    is not JSON-serializable by `json.dumps`. Ask for JSON mode when you are
    about to serialize:

    ```pycon
    >>> StudentSchema.model_validate({'semester': '1'}).model_dump(mode='json')
    {'semester': '1'}

    ```

## The default carries across

`default='1'` on the Django field becomes the schema default, so the field is
not required:

```pycon
>>> StudentSchema.model_fields['semester'].is_required()
False
>>> StudentSchema.model_validate({}).model_dump(mode='json')
{'semester': '1'}

```

## JSON Schema

The permitted values are published, so generated API documentation stays in step
with the model:

```pycon
>>> print(json.dumps(StudentSchema.model_json_schema()['$defs'], indent=2))
{
  "SemesterEnum": {
    "enum": [
      "1",
      "2",
      "3"
    ],
    "title": "SemesterEnum",
    "type": "string"
  }
}

```

## Reading from an instance

Choices behave the same when the input is a Django object:

```pycon
>>> StudentSchema.model_validate(models.Student(semester='2')).model_dump(mode='json')
{'semester': '2'}

```

!!! warning "Values already in the database are still validated"

    A row holding a value that is no longer in `choices` — after the list was
    edited, say — fails validation on read. Widen the schema field by
    [overriding it](model-schema.md#overriding-a-generated-field) if you need to
    read legacy rows.

## Related guides

- [Field reference](../reference/fields.md) — the full conversion table
- [ModelSchema](model-schema.md) — overriding a generated field
