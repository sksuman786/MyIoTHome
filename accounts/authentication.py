"""
Custom authentication backends for API access.
"""

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.timezone import now
from accounts.models import APIKey, User
import binascii


class APIKeyAuthentication(TokenAuthentication):
    """
    Custom API Key authentication for device and external service access.
    """
    keyword = 'Bearer'
    model = APIKey

    def get_model(self):
        return self.model

    def authenticate(self, request):
        auth = request.META.get('HTTP_X_API_KEY', '').split()

        if not auth or auth[0].lower() != self.keyword.lower():
            return None

        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(msg)

        return self.authenticate_credentials(auth[1], request)

    def authenticate_credentials(self, key, request):
        model = self.get_model()
        try:
            api_key = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid API key.')

        if not api_key.is_valid():
            raise AuthenticationFailed('API key is not valid or has expired.')

        if not api_key.user.is_active:
            raise AuthenticationFailed('User inactive or deleted.')

        # Update last used
        api_key.last_used_at = now()
        api_key.last_used_ip = self.get_client_ip(request)
        api_key.save(update_fields=['last_used_at', 'last_used_ip'])

        return (api_key.user, api_key)

    def authenticate_header(self, request):
        return self.keyword

    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
