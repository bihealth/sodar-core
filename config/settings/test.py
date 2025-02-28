"""
Test settings

- Used to run tests fast on the continuous integration server and locally
"""

from .base import *  # noqa


# DEBUG
# ------------------------------------------------------------------------------
# Turn debug off so tests run faster
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = True

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# Note: This key only used for development and testing.
SECRET_KEY = env('DJANGO_SECRET_KEY', default='CHANGEME!!!')

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
ADMINS = [('Admin User', 'admin@example.com')]
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Set False to support parallel testing, see issue #1428
DATABASES['default']['ATOMIC_REQUESTS'] = False

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

# In-memory email backend stores messages in django.core.mail.outbox
# for unit testing purposes
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_SENDER = 'noreply@example.com'

# CACHING
# ------------------------------------------------------------------------------
# Speed advantages of in-memory caching without having to run Memcached
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': '',
    }
}

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# PASSWORD HASHING
# ------------------------------------------------------------------------------
# Use fast password hasher so tests run faster
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# TEMPLATE LOADERS
# ------------------------------------------------------------------------------
# Keep templates in memory so tests run faster
TEMPLATES[0]['OPTIONS']['loaders'] = [
    [
        'django.template.loaders.cached.Loader',
        [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ],
    ]
]

# Django REST framework
# ------------------------------------------------------------------------------

# Set pagination page size to 1 for easy testing
REST_FRAMEWORK['PAGE_SIZE'] = 1


# LDAP configuration
# ------------------------------------------------------------------------------

ENABLE_LDAP = False


# OpenID Connect (OIDC) configuration
# ------------------------------------------------------------------------------

ENABLE_OIDC = False


# Logging
# ------------------------------------------------------------------------------

LOGGING_LEVEL = env.str('LOGGING_LEVEL', 'CRITICAL')
LOGGING = set_logging(LOGGING_LEVEL)
LOGGING_DISABLE_CMD_OUTPUT = True


# Local App Settings
# ------------------------------------------------------------------------------


# Plugin settings
ENABLED_BACKEND_PLUGINS = [
    'appalerts_backend',
    'sodar_cache',
    'timeline_backend',
    'example_backend_app',
]

# Projectroles app settings
PROJECTROLES_SITE_MODE = 'SOURCE'
PROJECTROLES_TARGET_CREATE = True
PROJECTROLES_DEFAULT_ADMIN = 'admin'
PROJECTROLES_ALLOW_LOCAL_USERS = True
PROJECTROLES_ALLOW_ANONYMOUS = False
PROJECTROLES_ENABLE_MODIFY_API = True
PROJECTROLES_DISABLE_CATEGORIES = False
PROJECTROLES_INVITE_EXPIRY_DAYS = 14
PROJECTROLES_SEND_EMAIL = True
PROJECTROLES_EMAIL_SENDER_REPLY = False
PROJECTROLES_SEARCH_PAGINATION = 10
PROJECTROLES_KIOSK_MODE = False
PROJECTROLES_HIDE_PROJECT_APPS = []
PROJECTROLES_DELEGATE_LIMIT = 1
PROJECTROLES_BROWSER_WARNING = True
PROJECTROLES_DISABLE_CDN_INCLUDES = False
PROJECTROLES_INLINE_HEAD_INCLUDE = None
PROJECTROLES_CUSTOM_JS_INCLUDES = []
PROJECTROLES_CUSTOM_CSS_INCLUDES = []
PROJECTROLES_SIDEBAR_ICON_SIZE = 36
PROJECTROLES_API_USER_DETAIL_RESTRICT = False

# Bgjobs app settings
BGJOBS_PAGINATION = 15

# Adminalerts app settings
ADMINALERTS_PAGINATION = 15

# Appalerts app settings
APPALERTS_STATUS_INTERVAL = 3

# Filesfolders app settings
FILESFOLDERS_MAX_UPLOAD_SIZE = 10485760
FILESFOLDERS_MAX_ARCHIVE_SIZE = 52428800
FILESFOLDERS_SERVE_AS_ATTACHMENT = False
FILESFOLDERS_LINK_BAD_REQUEST_MSG = 'Invalid request'
FILESFOLDERS_SHOW_LIST_COLUMNS = True

# Timeline app settings
TIMELINE_PAGINATION = 15

# Tokens app settings
TOKENS_CREATE_PROJECT_USER_RESTRICT = False

# UI test settings
PROJECTROLES_TEST_UI_CHROME_OPTIONS = [
    'headless=new',
    'no-sandbox',  # For Gitlab-CI compatibility
    'disable-dev-shm-usage',  # For testing stability
]
PROJECTROLES_TEST_UI_WINDOW_SIZE = (1400, 1000)
PROJECTROLES_TEST_UI_WAIT_TIME = 30
PROJECTROLES_TEST_UI_LEGACY_LOGIN = env.bool(
    'PROJECTROLES_TEST_UI_LEGACY_LOGIN', False
)

PROJECTROLES_APP_SETTINGS_TEST = None
