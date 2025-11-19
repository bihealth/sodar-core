"""Admin settings for the tokens app"""

from django.contrib import admin

from tokens.models import SODARAuthToken

admin.site.register(SODARAuthToken)
