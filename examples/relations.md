# Relations

**Source:** [relations.py](relations.py)

`ModelSchema` supports Django relationships as regular model fields. The example
uses `depth=1` so `WeekSchema` serializes each `Day` in its `ManyToManyField` as
a nested schema instead of a primary-key value.

Load relationships deliberately before serialization. For a queryset, use
`prefetch_related('days')` to avoid an additional query for each parent object.

This differs from `Source`: `Source` intentionally does not support a
`ManyToMany` path. It is designed for direct attributes and a terminal reverse
`ForeignKey` collection only.

The source is executed by `test_relations_example` in
[`tests/test_examples.py`](../tests/test_examples.py).