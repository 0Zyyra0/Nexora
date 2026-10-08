from .models import Profile
from .site_texts import get_text


def profile(request):
    """Make the (singleton) Profile available in every template as `profile`,
    plus `brand_name` (the owner's name, or an editable fallback)."""
    profile = Profile.objects.first()
    name = profile.name if profile and profile.name else get_text('site.name')
    return {'profile': profile, 'brand_name': name}
