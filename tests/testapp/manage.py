#!/usr/bin/env python
"""Administrative entry point for the isolated Django test project."""

import os
import sys


def main() -> None:
    """Run Django management commands for the test application."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            'Django is required to run the isolated test application.'
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
