#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snorkelforecast.snorkelforecast.settings")
    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        # Avoid inotify watch-limit crashes in local/container dev environments.
        os.environ.setdefault("WATCHFILES_FORCE_POLLING", "true")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
