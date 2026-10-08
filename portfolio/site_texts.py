"""Runtime helpers for the editable site texts (see models.SiteText).

DEFAULTS (in site_text_defaults.py) holds the built-in wording; the database
row with the same key, when present, always wins. Nothing here may raise: a
broken database must never take the error pages down with it.
"""

from .site_text_defaults import DEFAULTS


class _SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def fetch_all():
    """{key: value} for every row; {} if the table is unavailable."""
    from .models import SiteText

    try:
        return dict(SiteText.objects.values_list('key', 'value'))
    except Exception:
        return {}


def resolve(texts, key, params=None):
    value = texts.get(key)
    if value is None:
        value = DEFAULTS[key][0] if key in DEFAULTS else key
    if params:
        params = dict(params)
        count = params.get('count')
        if isinstance(count, int) and 's' not in params:
            params['s'] = '' if count == 1 else 's'  # "1 post" / "2 posts"
        try:
            value = value.format_map(_SafeDict(params))
        except (ValueError, IndexError, KeyError):
            pass  # malformed braces typed in the admin: show the text as-is
    return value


def get_text(key, **params):
    """Single lookup for Python code (e.g. flash messages in views)."""
    from .models import SiteText

    value = None
    try:
        value = SiteText.objects.filter(key=key).values_list('value', flat=True).first()
    except Exception:
        pass
    return resolve({key: value} if value is not None else {}, key, params)


def ensure_defaults():
    """Create the admin rows for any built-in text that has none yet."""
    from .models import SiteText

    existing = set(SiteText.objects.values_list('key', flat=True))
    missing = [
        SiteText(key=key, value=value, group=group)
        for key, (value, group) in DEFAULTS.items()
        if key not in existing
    ]
    if missing:
        SiteText.objects.bulk_create(missing, ignore_conflicts=True)
    return len(missing)
