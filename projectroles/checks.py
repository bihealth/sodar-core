"""Django checks for the projectroles app"""

from django.conf import settings
from django.core.checks import Warning, register


# Local constants
W001_SETTINGS = [
    'ENABLE_LDAP',
    'ENABLE_OIDC',
    'PROJECTROLES_ALLOW_ANONYMOUS',
    'PROJECTROLES_ALLOW_LOCAL_USERS',
    'PROJECTROLES_KIOSK_MODE',
]
W001_MSG = (
    'No authentication methods enabled, only superusers can access the site. '
    'Set one or more of the following: {}'.format(', '.join(W001_SETTINGS))
)
W001 = Warning(W001_MSG, obj=settings, id='projectroles.W001')


@register()
def check_auth_methods(app_configs, **kwargs):
    """
    Check for enabled authentication schemes. Raise error if no users other than
    superusers are able to log in with the current settings).
    """
    ret = []
    if not any([getattr(settings, a, False) for a in W001_SETTINGS]):
        ret.append(W001)
    return ret
