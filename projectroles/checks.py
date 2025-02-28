"""Django checks for the projectroles app"""

from django.conf import settings
from django.core.checks import Error, Warning, register

from projectroles import app_settings
from projectroles.plugins import get_active_plugins


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
E001_MSG = (
    'Repeated app setting definition names found in plugins. Review your '
    'plugins and ensure each app setting name is used only once within the '
    'same plugin. Affected plugin(s): {plugin_names}'
)


@register()
def check_auth_methods(app_configs, **kwargs):
    """
    Check for enabled authentication schemes. Raise error if no users other than
    superusers are able to log in with the current settings).
    """
    if not any([getattr(settings, a, False) for a in W001_SETTINGS]):
        return [W001]
    return []


@register()
def check_app_setting_defs(app_configs, **kwargs):
    """
    Check provided plugin app setting definitions to ensure the name of each
    definition is unique within its app plugin.
    """
    err_plugins = []
    for p in get_active_plugins():
        s_defs = p.app_settings
        if isinstance(s_defs, list):
            s_names = [d.name for d in s_defs]
            if len(set(s_names)) != len(s_names) and p.name not in err_plugins:
                err_plugins.append(p.name)
    if err_plugins:
        return [
            Error(
                E001_MSG.format(plugin_names=', '.join(err_plugins)),
                obj=app_settings,
                id='projectroles.E001',
            )
        ]
    return []
