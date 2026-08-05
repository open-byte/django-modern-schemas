from django.contrib.auth.models import AbstractUser
from django.db import models

from ._django import configure_django

configure_django()


# --8<-- [start:speaker-model]
class Speaker(AbstractUser):
    """A model inheriting AbstractUser, whose get_full_name() comes from the base class."""

    # Distinct related_names: the defaults would clash with auth.User (fields.E304).
    groups = models.ManyToManyField('auth.Group', related_name='speaker_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='speaker_set', blank=True)

    class Meta:
        app_label = 'examples'


# --8<-- [end:speaker-model]


# --8<-- [start:category-model]
class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'examples'


# --8<-- [end:category-model]


# --8<-- [start:event-model]
class Event(models.Model):
    title = models.CharField(max_length=100)
    category = models.OneToOneField(Category, null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = 'examples'

    def display_title(self) -> str:
        return f'Event: {self.title}'


# --8<-- [end:event-model]


# --8<-- [start:speaker-profile]
class SpeakerProfile(models.Model):
    """Exercises every scalar field conversion documented in the field reference."""

    uuid = models.UUIDField()
    full_name = models.CharField(max_length=120)
    biography = models.TextField(blank=True)
    slug = models.SlugField()
    email = models.EmailField()
    website = models.URLField()
    talks_given = models.IntegerField(default=0)
    rating = models.FloatField(null=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(null=True)
    birth_date = models.DateField(null=True)
    preferred_slot = models.TimeField(null=True)
    session_length = models.DurationField(null=True)
    last_login_ip = models.GenericIPAddressField(null=True)
    metadata = models.JSONField(null=True)

    class Meta:
        app_label = 'examples'


# --8<-- [end:speaker-profile]


# --8<-- [start:question-model]
class Question(models.Model):
    text = models.CharField(max_length=200)
    category = models.ForeignKey(Category, related_name='questions', on_delete=models.CASCADE)

    class Meta:
        app_label = 'examples'


# --8<-- [end:question-model]


# --8<-- [start:student-choices]
class Student(models.Model):
    SEMESTER_CHOICES = (
        ('1', 'One'),
        ('2', 'Two'),
        ('3', 'Three'),
    )

    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES, default='1')

    class Meta:
        app_label = 'examples'


# --8<-- [end:student-choices]


# --8<-- [start:week-models]
class Day(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        app_label = 'examples'


class Week(models.Model):
    name = models.CharField(max_length=20)
    days = models.ManyToManyField(Day)

    class Meta:
        app_label = 'examples'


# --8<-- [end:week-models]
