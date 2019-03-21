#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    sys.path.append(base_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_orm.configs")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
