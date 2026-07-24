from pydantic import BaseModel

from .mixins import SchemaMixins


class Schema(SchemaMixins, BaseModel):
    model_config = {'from_attributes': True}
