# middleware.py
from django.conf import settings
from django.db import connections

class DynamicDBCredentialsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # For admin users, use root credentials
            if request.user.email in settings.ADMIN_EMAILS:
                self._set_db_credentials(
                    settings.MYSQL_ADMIN_USER,
                    settings.MYSQL_ADMIN_PASSWORD
                )
            # For regular users with MySQL accounts
            elif hasattr(request.user, 'is_db_user_created') and request.user.is_db_user_created:
                self._set_db_credentials(
                    request.user.sanitize_mysql_username(request.user.username),
                    request.user.mysql_password
                )
        
        response = self.get_response(request)
        return response

    def _set_db_credentials(self, user, password):
        """Update database connection settings"""
        connections['default'].settings_dict['USER'] = user
        connections['default'].settings_dict['PASSWORD'] = password