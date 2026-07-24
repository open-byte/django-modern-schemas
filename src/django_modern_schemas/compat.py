class MissingType(object):  # noqa: EXE002, UP004
    pass


try:
    # Postgres fields are only available in Django with psycopg2 installed
    # and we cannot have psycopg2 on PyPy
    from django.contrib.postgres.fields import (  # ty:ignore[unresolved-import]
        ArrayField,
        HStoreField,
        JSONField,
        RangeField,
    )
except ImportError:
    ArrayField, HStoreField, JSONField, RangeField = (MissingType,) * 4
