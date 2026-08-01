from django.conf import settings


def configure_django() -> None:
    """Configure the minimal Django environment required by the examples."""
    if settings.configured:
        return

    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[],
        SECRET_KEY='django-modern-schemas-examples',
        USE_TZ=True,
    )

    import django

    django.setup()
