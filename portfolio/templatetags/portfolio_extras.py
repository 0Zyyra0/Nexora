from django import template

register = template.Library()

# The Linework theme ships exactly four chip colour variants (the base
# ".chip" plus chip-sun / chip-tom / chip-cob). We only have six Post
# categories, so a couple of them reuse a colour — that's fine, the
# label text is what actually distinguishes them.
_BADGE_CLASS_MAP = {
    'design': 'chip-sun',
    'graphic': 'chip-tom',
    'marketing': 'chip-cob',
    'finance': 'chip',
    'music': 'chip-sun',
    'education': 'chip-cob',
}


@register.filter
def category_badge_class(category_value):
    return _BADGE_CLASS_MAP.get(category_value, 'chip')
