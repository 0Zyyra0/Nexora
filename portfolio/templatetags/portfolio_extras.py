from django import template

register = template.Library()

# The theme's CSS only ships badge colors for these specific class names,
# so we map our Post.Category values onto the closest matching color.
_BADGE_CLASS_MAP = {
    'design': 'bg-design',
    'graphic': 'bg-graphic',
    'marketing': 'bg-advertising',
    'finance': 'bg-finance',
    'music': 'bg-music',
    'education': 'bg-education',
}


@register.filter
def category_badge_class(category_value):
    return _BADGE_CLASS_MAP.get(category_value, 'bg-design')
