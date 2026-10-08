from django import template

from ..site_texts import fetch_all, resolve

register = template.Library()


@register.simple_tag(takes_context=True)
def sitetext(context, key, **params):
    """Editable site text:  {% sitetext 'home.hero_title' %}

    Placeholders are filled from keyword arguments:
        {% sitetext 'blog_list.search_results' keyword=keyword count=n %}
    Never raises: if the database is unavailable (or the key is unknown) the
    built-in default is used, so even the error pages keep working.
    """
    request = context.get('request')
    texts = getattr(request, '_site_texts', None)
    if texts is None:
        texts = fetch_all()
        if request is not None:
            request._site_texts = texts
    return resolve(texts, key, params)
