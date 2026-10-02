from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """
    Authenticate using the email address instead of the `username` field.

    The site's own login form labels the field "Email" and POSTs it as
    `username` (that's just AuthenticationForm's field name — it doesn't
    mean the value has to BE a username). This backend is what makes that
    value actually resolve to the right account: it looks the user up by
    `email` instead of by `username`.

    Registered alongside the stock ModelBackend (see AUTHENTICATION_BACKENDS
    in settings.py), so:
      - the member-facing login (this site) authenticates by email, and
      - the Django admin login (which asks for an actual username) keeps
        working exactly as before, via ModelBackend.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = username or kwargs.get('email')
        if identifier is None or password is None:
            return None

        try:
            user = User.objects.get(email__iexact=identifier.strip())
        except User.DoesNotExist:
            # Run the hasher anyway so failed logins for a non-existent
            # email take the same amount of time as a wrong password for
            # a real one (mirrors ModelBackend's own behaviour).
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Shouldn't happen once emails are enforced unique (see the
            # unique index added in migration 0003) — but never 500 here.
            user = User.objects.filter(email__iexact=identifier.strip()).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
