"""SODAR constants definition and helper functions"""

# Global SODAR constants
SODAR_CONSTANTS = {
    # Project roles
    'PROJECT_ROLE_OWNER': 'project owner',
    'PROJECT_ROLE_DELEGATE': 'project delegate',
    'PROJECT_ROLE_CONTRIBUTOR': 'project contributor',
    'PROJECT_ROLE_GUEST': 'project guest',
    'PROJECT_ROLE_FINDER': 'project finder',
    # Project types
    'PROJECT_TYPE_CATEGORY': 'CATEGORY',
    'PROJECT_TYPE_PROJECT': 'PROJECT',
    # App Settings
    'APP_SETTING_SCOPE_PROJECT': 'PROJECT',
    'APP_SETTING_SCOPE_USER': 'USER',
    'APP_SETTING_SCOPE_PROJECT_USER': 'PROJECT_USER',
    'APP_SETTING_SCOPE_SITE': 'SITE',
    'APP_SETTING_TYPE_BOOLEAN': 'BOOLEAN',
    'APP_SETTING_TYPE_INTEGER': 'INTEGER',
    'APP_SETTING_TYPE_JSON': 'JSON',
    'APP_SETTING_TYPE_STRING': 'STRING',
    # RemoteSite mode
    'SITE_MODE_SOURCE': 'SOURCE',
    'SITE_MODE_TARGET': 'TARGET',
    'SITE_MODE_PEER': 'PEER',
    # RemoteProject access types
    'REMOTE_LEVEL_NONE': 'NONE',
    'REMOTE_LEVEL_REVOKED': 'REVOKED',
    'REMOTE_LEVEL_VIEW_AVAIL': 'VIEW_AVAIL',
    'REMOTE_LEVEL_READ_INFO': 'READ_INFO',
    'REMOTE_LEVEL_READ_ROLES': 'READ_ROLES',
    # RemoteSite modes
    'SITE_MODES': ['SOURCE', 'TARGET', 'PEER'],
    # RemoteProject access type legend
    'REMOTE_ACCESS_LEVELS': {
        'NONE': 'No access',
        'REVOKED': 'Revoked access',
        'VIEW_AVAIL': 'View availability',
        'READ_INFO': 'Read information',
        'READ_ROLES': 'Read members',
    },
    # Display names
    'DISPLAY_NAMES': {
        'CATEGORY': {'default': 'category', 'plural': 'categories'},
        'PROJECT': {'default': 'project', 'plural': 'projects'},
    },
    # User types
    'AUTH_TYPE_LOCAL': 'LOCAL',
    'AUTH_TYPE_LDAP': 'LDAP',
    'AUTH_TYPE_OIDC': 'OIDC',
    # System user group
    'SYSTEM_USER_GROUP': 'system',
    'OIDC_USER_GROUP': 'oidc',
    # Project modification
    'PROJECT_ACTION_CREATE': 'CREATE',
    'PROJECT_ACTION_UPDATE': 'UPDATE',
}


def get_sodar_constants(default=False):
    """
    Return SODAR_CONSTANTS from settings if present, else from default
    definition.
    """
    if not default:
        from django.conf import settings

        if hasattr(settings, 'SODAR_CONSTANTS'):
            return settings.SODAR_CONSTANTS
    return SODAR_CONSTANTS
