from typing import TypeVar

from django.db.models import Model as DjangoModel
from pydantic import BaseModel

from .mixins import SchemaBaseMixins

T = TypeVar('T', bound=DjangoModel)


class Schema(SchemaBaseMixins, BaseModel):
    model_config = {'from_attributes': True}
