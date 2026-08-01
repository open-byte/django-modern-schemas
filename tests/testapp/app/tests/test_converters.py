import json
from unittest.mock import Mock

import pytest
from app.models import Week
from django.db import models
from django.db.models import Manager
from pydantic import ValidationError

from django_modern_schemas import ModelSchema


def test_inheritance():
    class ParentModel(models.Model):
        parent_field = models.CharField()

        class Meta:
            app_label = 'tests'

    class ChildModel(ParentModel):
        child_field = models.CharField()

        class Meta:
            app_label = 'tests'

    class ChildSchema(ModelSchema):
        class Config:
            model = ChildModel

    assert ChildSchema.model_json_schema() == {
        'properties': {
            'id': {'description': '', 'title': 'Id', 'type': 'integer'},
            'parent_field': {
                'description': '',
                'title': 'Parent Field',
                'type': 'string',
            },
            'parentmodel_ptr': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'description': '',
                'title': 'Parentmodel Ptr',
            },
            'child_field': {
                'description': '',
                'title': 'Child Field',
                'type': 'string',
            },
        },
        'required': ['id', 'parent_field', 'child_field'],
        'title': 'ChildSchema',
        'type': 'object',
    }


def test_all_fields():

    class AllFields(models.Model):
        bigintegerfield = models.BigIntegerField()
        binaryfield = models.BinaryField()
        booleanfield = models.BooleanField()
        charfield = models.CharField()
        commaseparatedintegerfield = models.CommaSeparatedIntegerField()
        datefield = models.DateField()
        datetimefield = models.DateTimeField()
        decimalfield = models.DecimalField()
        durationfield = models.DurationField()
        emailfield = models.EmailField()
        filefield = models.FileField()
        filepathfield = models.FilePathField()
        floatfield = models.FloatField()
        genericipaddressfield = models.GenericIPAddressField()
        ipaddressfield = models.IPAddressField()
        imagefield = models.ImageField()
        integerfield = models.IntegerField()
        nullbooleanfield = models.NullBooleanField()
        positiveintegerfield = models.PositiveIntegerField()
        positivesmallintegerfield = models.PositiveSmallIntegerField()
        slugfield = models.SlugField()
        smallintegerfield = models.SmallIntegerField()
        textfield = models.TextField()
        timefield = models.TimeField()
        urlfield = models.URLField()
        uuidfield = models.UUIDField()

        class Meta:
            app_label = 'tests'

    class AllFieldsSchema(ModelSchema):
        class Config:
            model = AllFields

    assert AllFieldsSchema.model_json_schema() == {
        'properties': {
            'id': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'description': '',
                'title': 'Id',
            },
            'bigintegerfield': {
                'description': '',
                'title': 'Bigintegerfield',
                'type': 'integer',
            },
            'binaryfield': {
                'description': '',
                'format': 'binary',
                'title': 'Binaryfield',
                'type': 'string',
            },
            'booleanfield': {
                'description': '',
                'title': 'Booleanfield',
                'type': 'boolean',
            },
            'charfield': {'description': '', 'title': 'Charfield', 'type': 'string'},
            'commaseparatedintegerfield': {
                'description': '',
                'title': 'Commaseparatedintegerfield',
                'type': 'string',
            },
            'datefield': {
                'description': '',
                'format': 'date',
                'title': 'Datefield',
                'type': 'string',
            },
            'datetimefield': {
                'description': '',
                'format': 'date-time',
                'title': 'Datetimefield',
                'type': 'string',
            },
            'decimalfield': {
                'anyOf': [{'type': 'number'}, {'pattern': '^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$', 'type': 'string'}],
                'description': '',
                'title': 'Decimalfield',
            },
            'durationfield': {
                'description': '',
                'format': 'duration',
                'title': 'Durationfield',
                'type': 'string',
            },
            'emailfield': {
                'description': '',
                'format': 'email',
                'title': 'Emailfield',
                'type': 'string',
            },
            'filefield': {'description': '', 'title': 'Filefield', 'type': 'string'},
            'filepathfield': {
                'description': '',
                'title': 'Filepathfield',
                'type': 'string',
            },
            'floatfield': {'description': '', 'title': 'Floatfield', 'type': 'number'},
            'genericipaddressfield': {
                'description': '',
                'format': 'ipvanyaddress',
                'title': 'Genericipaddressfield',
                'type': 'string',
            },
            'ipaddressfield': {
                'description': '',
                'format': 'ipvanyaddress',
                'title': 'Ipaddressfield',
                'type': 'string',
            },
            'imagefield': {'description': '', 'title': 'Imagefield', 'type': 'string'},
            'integerfield': {
                'description': '',
                'title': 'Integerfield',
                'type': 'integer',
            },
            'nullbooleanfield': {
                'description': '',
                'title': 'Nullbooleanfield',
                'type': 'boolean',
            },
            'positiveintegerfield': {
                'description': '',
                'title': 'Positiveintegerfield',
                'type': 'integer',
            },
            'positivesmallintegerfield': {
                'description': '',
                'title': 'Positivesmallintegerfield',
                'type': 'integer',
            },
            'slugfield': {'description': '', 'title': 'Slugfield', 'type': 'string'},
            'smallintegerfield': {
                'description': '',
                'title': 'Smallintegerfield',
                'type': 'integer',
            },
            'textfield': {'description': '', 'title': 'Textfield', 'type': 'string'},
            'timefield': {
                'description': '',
                'format': 'time',
                'title': 'Timefield',
                'type': 'string',
            },
            'urlfield': {
                'description': '',
                'format': 'uri',
                'minLength': 1,
                'title': 'Urlfield',
                'type': 'string',
            },
            'uuidfield': {
                'description': '',
                'format': 'uuid',
                'title': 'Uuidfield',
                'type': 'string',
            },
        },
        'required': [
            'bigintegerfield',
            'binaryfield',
            'booleanfield',
            'charfield',
            'commaseparatedintegerfield',
            'datefield',
            'datetimefield',
            'decimalfield',
            'durationfield',
            'emailfield',
            'filefield',
            'filepathfield',
            'floatfield',
            'genericipaddressfield',
            'ipaddressfield',
            'imagefield',
            'integerfield',
            'nullbooleanfield',
            'positiveintegerfield',
            'positivesmallintegerfield',
            'slugfield',
            'smallintegerfield',
            'textfield',
            'timefield',
            'urlfield',
            'uuidfield',
        ],
        'title': 'AllFieldsSchema',
        'type': 'object',
    }


def test_bigautofield():
    # Primary keys are optional when fields = __all__.
    class ModelBigAuto(models.Model):
        bigautofiled = models.BigAutoField(primary_key=True)

        class Meta:
            app_label = 'tests'

    class ModelBigAutoSchema(ModelSchema):
        class Config:
            model = ModelBigAuto

    assert ModelBigAutoSchema.model_json_schema() == {
        'properties': {
            'bigautofiled': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'description': '',
                'title': 'Bigautofiled',
            }
        },
        'title': 'ModelBigAutoSchema',
        'type': 'object',
    }


def test_django_31_fields():
    class ModelNewFields(models.Model):
        jsonfield = models.JSONField()
        positivebigintegerfield = models.PositiveBigIntegerField()

        class Meta:
            app_label = 'tests'

    class ModelNewFieldsSchema(ModelSchema):
        class Config:
            model = ModelNewFields

    assert ModelNewFieldsSchema.model_json_schema() == {
        'properties': {
            'id': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'description': '',
                'title': 'Id',
            },
            'jsonfield': {
                'contentMediaType': 'application/json',
                'contentSchema': {},
                'description': '',
                'title': 'Jsonfield',
                'type': 'string',
            },
            'positivebigintegerfield': {
                'description': '',
                'title': 'Positivebigintegerfield',
                'type': 'integer',
            },
        },
        'required': ['jsonfield', 'positivebigintegerfield'],
        'title': 'ModelNewFieldsSchema',
        'type': 'object',
    }

    with pytest.raises(ValidationError):
        ModelNewFieldsSchema(id=1, jsonfield={'any': 'data'}, positivebigintegerfield=1)

    obj = ModelNewFieldsSchema(id=1, jsonfield=json.dumps({'any': 'data'}), positivebigintegerfield=1)
    assert obj.model_dump() == {
        'id': 1,
        'jsonfield': {'any': 'data'},
        'positivebigintegerfield': 1,
    }


def test_relational():
    class Related(models.Model):
        charfield = models.CharField()

        class Meta:
            app_label = 'tests'

    class TestModel(models.Model):
        manytomanyfield = models.ManyToManyField(Related)
        onetoonefield = models.OneToOneField(Related, on_delete=models.CASCADE)
        foreignkey = models.ForeignKey(Related, on_delete=models.SET_NULL, null=True)

        class Meta:
            app_label = 'tests'

    class TestSchema(ModelSchema):
        class Config:
            model = TestModel

    assert TestSchema.model_json_schema() == {
        'properties': {
            'id': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'description': '',
                'title': 'Id',
            },
            'onetoonefield': {
                'description': '',
                'title': 'Onetoonefield',
                'type': 'integer',
            },
            'foreignkey': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'description': '',
                'title': 'Foreignkey',
            },
            'manytomanyfield': {
                'description': '',
                'items': {'type': 'integer'},
                'title': 'Manytomanyfield',
                'type': 'array',
            },
        },
        'required': ['onetoonefield', 'manytomanyfield'],
        'title': 'TestSchema',
        'type': 'object',
    }


def test_default():
    class MyModel(models.Model):
        default_static = models.CharField(default='hello')
        default_dynamic = models.CharField(default=lambda: 'world')

        class Meta:
            app_label = 'tests'

    class MyModelSchema(ModelSchema):
        class Config:
            model = MyModel

    assert MyModelSchema.model_json_schema() == {
        'properties': {
            'id': {
                'anyOf': [{'type': 'integer'}, {'type': 'null'}],
                'default': None,
                'description': '',
                'title': 'Id',
            },
            'default_static': {
                'default': 'hello',
                'description': '',
                'title': 'Default Static',
                'type': 'string',
            },
            'default_dynamic': {
                'description': '',
                'title': 'Default Dynamic',
                'type': 'string',
            },
        },
        'title': 'MyModelSchema',
        'type': 'object',
    }


def test_manytomany():
    class Foo(models.Model):
        f = models.CharField()

        class Meta:
            app_label = 'tests'

    class Bar(models.Model):
        m2m = models.ManyToManyField(Foo, blank=True)

        class Meta:
            app_label = 'tests'

    class BarSchema(ModelSchema):
        class Config:
            model = Bar

    # mocking database data:

    foo = Mock()
    foo.pk = 1
    foo.f = 'test'

    m2m = Mock(spec=Manager)
    m2m.all = lambda: [foo]

    bar = Mock()
    bar.id = 1
    bar.m2m = m2m

    data = BarSchema.from_orm(bar).model_dump()

    assert data == {'id': 1, 'm2m': [1]}


def test_manytomany_validation():
    bar = Mock()
    bar.pk = '555555s'

    foo = Mock()
    foo.pk = 1

    class WeekSchema(ModelSchema):
        class Config:
            model = Week

    with pytest.raises(Exception, match='Invalid type'):
        WeekSchema(name='FirstWeek', days=['1', '2'])

    with pytest.raises(Exception, match='Invalid type'):
        WeekSchema(name='FirstWeek', days=[bar, bar])

    schema = WeekSchema(name='FirstWeek', days=[foo, foo])
    assert schema.model_dump() == {'id': None, 'name': 'FirstWeek', 'days': [1, 1]}
