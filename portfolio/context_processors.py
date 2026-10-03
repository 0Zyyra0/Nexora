from .models import Profile, SiteSettings


def profile(request):
    """Make the (singleton) Profile available in every template as `profile`."""
    return {'profile': Profile.objects.first()}


def site_settings(request):
    """Make the editable page text available in every template as `site_settings`."""
    return {'site_settings': SiteSettings.load()}
