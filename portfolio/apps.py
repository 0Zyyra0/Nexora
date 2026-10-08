import logging

from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger('portfolio')


def _seed_site_texts(sender, **kwargs):
    """After every `migrate`, make sure each built-in text has an admin row."""
    from .site_texts import ensure_defaults

    try:
        ensure_defaults()
    except Exception:  # never let seeding break a migrate
        logger.exception('Could not seed site texts')


class PortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portfolio'
    verbose_name = 'Portfolio'

    def ready(self):
        post_migrate.connect(_seed_site_texts, sender=self)
