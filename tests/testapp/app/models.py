from django.contrib.auth.models import AbstractUser
from django.db import models

SEMESTER_CHOICES = (
    ('1', 'One'),
    ('2', 'Two'),
    ('3', 'Three'),
)


class TestAbstractModel(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True

    def get_name(self) -> str:
        return self.name


class TestConcreteModel(TestAbstractModel):
    description = models.TextField()

    class Meta:
        app_label = 'app'


class Student(models.Model):
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES, default='1')

    class Meta:
        app_label = 'app'


class StudentEmail(models.Model):
    email = models.EmailField(null=False, blank=False)

    class Meta:
        app_label = 'app'


class Category(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        app_label = 'app'


class Event(models.Model):
    title = models.CharField(max_length=100)
    category = models.OneToOneField(Category, null=True, blank=True, on_delete=models.SET_NULL)
    start_date = models.DateField(auto_now=True)
    end_date = models.DateField(auto_now_add=True)

    class Meta:
        app_label = 'app'

    def __str__(self):
        return self.title

    def get_some_thing(self) -> str:
        return 'Hello World'


class Client(models.Model):
    key = models.CharField(max_length=20, unique=True)

    class Meta:
        app_label = 'app'


class Day(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        app_label = 'app'


class Week(models.Model):
    name = models.CharField(max_length=20, unique=True)
    days = models.ManyToManyField(Day)

    class Meta:
        app_label = 'app'
