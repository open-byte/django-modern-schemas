from django.db import models

SEMESTER_CHOICES = (
    ('1', 'One'),
    ('2', 'Two'),
    ('3', 'Three'),
)


class Student(models.Model):
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES, default='1')


class StudentEmail(models.Model):
    email = models.EmailField(null=False, blank=False)


class Category(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()


class Event(models.Model):
    title = models.CharField(max_length=100)
    category = models.OneToOneField(Category, null=True, blank=True, on_delete=models.SET_NULL)
    start_date = models.DateField(auto_now=True)
    end_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    def display_title(self) -> str:
        return f'Event: {self.title}'


class Question(models.Model):
    text = models.CharField(max_length=100)
    category = models.ForeignKey(Category, related_name='questions', on_delete=models.CASCADE)


class Client(models.Model):
    key = models.CharField(max_length=20, unique=True)


class Day(models.Model):
    name = models.CharField(max_length=20, unique=True)


class Week(models.Model):
    name = models.CharField(max_length=20, unique=True)
    days = models.ManyToManyField(Day)
