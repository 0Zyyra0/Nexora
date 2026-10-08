"""
Entry point for cPanel's "Setup Python App" (Phusion Passenger).

Passenger imports this file and uses the module-level `application`.

This host has no Terminal/SSH, so there is no way to run
`python manage.py migrate` by hand after uploading new code. Instead, pending
migrations are applied automatically each time the app starts (a no-op when the
database is already up to date). A failure is logged to logs/django-errors.log
and never stops the site from starting.

Set DJANGO_AUTO_MIGRATE=False in Setup Python App -> Environment variables to
turn this off.
"""

import logging
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application  # noqa: E402  (also runs django.setup())

logger = logging.getLogger("portfolio")


def _auto_migrate():
    if os.environ.get("DJANGO_AUTO_MIGRATE", "True").lower() != "true":
        return

    from django.core.management import call_command

    try:
        import fcntl  # POSIX only; Passenger on the host is Linux
    except ImportError:
        fcntl = None

    lock_path = BASE_DIR / "logs" / ".migrate.lock"
    try:
        lock_path.parent.mkdir(exist_ok=True)
        lock_file = open(lock_path, "w")
    except OSError:
        lock_file = None

    try:
        # Passenger may start several workers at once: take turns so two of
        # them never run the same migration simultaneously.
        if lock_file and fcntl:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
        call_command("migrate", interactive=False, verbosity=0)
    except Exception:
        logger.exception("Automatic migrate failed - the site will keep running")
    finally:
        if lock_file:
            lock_file.close()


_auto_migrate()
