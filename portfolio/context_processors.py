from .models import Profile


def profile(request):
    """Make the (singleton) Profile available in every template as `profile`."""
    return {'profile': Profile.objects.first()}
