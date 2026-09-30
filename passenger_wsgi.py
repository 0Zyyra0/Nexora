"""
Entry point cPanel's "Setup Python App" (Phusion Passenger) looks for.

Passenger imports this file and expects a module-level `application`
callable. We point it at the real Django WSGI app, and also wrap it
with WhiteNoise so uploaded media files (/media/...) are served
directly by Python — no extra Apache/.htaccess configuration needed.

Static files (/static/...) are already handled by the WhiteNoise
*middleware* configured in config/settings.py — that's unrelated to
this file and keeps working regardless.
"""

import os
import sys

# Make sure the project directory (this file's folder) is importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from config.wsgi import application as django_application  # noqa: E402

application = django_application

try:
    from whitenoise import WhiteNoise

    from django.conf import settings

    application = WhiteNoise(
        django_application,
        root=str(settings.MEDIA_ROOT),
        prefix=settings.MEDIA_URL,
    )
except Exception:
    # If WhiteNoise isn't installed yet (e.g. before `pip install -r
    # requirements.txt` has been run), fall back to the plain Django
    # app so the site still boots — media files just won't be served
    # until the package is installed and the app is restarted.
    application = django_application
