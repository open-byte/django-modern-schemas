from django.db import models

from ._django import configure_django

configure_django()


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'examples'


class Event(models.Model):
    title = models.CharField(max_length=100)
    category = models.OneToOneField(Category, null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = 'examples'

    def display_title(self) -> str:
        return f'Event: {self.title}'


class Question(models.Model):
    text = models.CharField(max_length=200)
    category = models.ForeignKey(Category, related_name='questions', on_delete=models.CASCADE)

    class Meta:
        app_label = 'examples'


class Student(models.Model):
    SEMESTER_CHOICES = (
        ('1', 'One'),
        ('2', 'Two'),
        ('3', 'Three'),
    )

    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES, default='1')

    class Meta:
        app_label = 'examples'


class Day(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = 'examples'


class Week(models.Model):
    name = models.CharField(max_length=20)
    days = models.ManyToManyField(Day)

    class Meta:
        app_label = 'examples'
