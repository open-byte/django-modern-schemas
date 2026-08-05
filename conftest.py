"""Root pytest configuration.

Django is configured here (rather than under ``tests/``) so that the same
settings back both the unit tests and the doctests embedded in ``docs/``.
Every example printed in the documentation is executed against this project.
"""

import django


def pytest_configure(config):
    from django.conf import settings

    if settings.configured:  # pragma: no cover - defensive, examples may configure first
        django.setup()
        return

    settings.configure(
        ALLOWED_HOSTS=['*'],
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls',
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ],
        MIDDLEWARE=(
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'examples',
            'tests',
        ),
        PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
        AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.ModelBackend',),
        LANGUAGE_CODE='en-us',
        TIME_ZONE='UTC',
    )

    django.setup()
