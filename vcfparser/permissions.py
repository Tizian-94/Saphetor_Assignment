import secrets

from django.conf import settings
from rest_framework.permissions import BasePermission

class BearerSecretPermission(BasePermission):
    # requires "Authorization: <API_SECRET>" header on the request, header value is compared to "settings.API_SECRET"
    message = "Invalid or missing Authorization header"

    def has_permission(self, request, view):
        expected = getattr(settings, 'API_SECRET', '') or ''

        # prevent unset / empty api secret from granting access
        if not expected:
            return False
        
        provided = request.headers.get('Authorization','') or ''

        #compare digest nonASCII input bugfix prevent error 500
        try:
            return secrets.compare_digest(provided, expected)
        except TypeError:
            return False