from typing import TypeVar

from django.db.models import Model as DjangoModel
from pydantic import BaseModel

from .mixins import SchemaBaseMixins

T = TypeVar('T', bound=DjangoModel)


class Schema(SchemaBaseMixins, BaseModel):
    # pyrefly: ignore [bad-override]
    model_config = {'from_attributes': True}
