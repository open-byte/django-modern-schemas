# Persistence

**Source:** [persistence.py](persistence.py)

`ModelSchema` can create or update a Django model after Pydantic has validated
the input. The example uses `EventWriteSchema` and two explicit operations:

- `create_event()` validates a title and calls `create()`.
- `rename_event()` validates a title and calls `update(instance)`.

Keep input schemas focused on fields that can be written directly to the model.
Fields declared with `Source` or `MethodSource` are output-only and are excluded
from create and update operations.

The source is executed by `test_persistence_example` in
[`tests/test_examples.py`](../tests/test_examples.py).