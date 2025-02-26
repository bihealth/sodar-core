.. _app_projectroles_settings:


Projectroles Django Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document describes the :term:`Django settings<Django Settings>` for the
``projectroles`` app, which also control the configuration of other apps in a
SODAR Core based site.

These settings are usually found in ``config/settings/*.py``, with
``config/settings/base.py`` being the default configuration other files may
override or extend.

If your site is based on ``sodar-django-site``, mandatory settings are already
set to their default values. In that case, you only need to modify or customize
them where applicable.

If you are integrating django-sodar-core with an existing Django site or
building your site from scratch without the recommended template, make sure to
add all mandatory settings into your project.

For values retrieved from environment variables, make sure to configure your
env accordingly. For development and testing, it is highly recommended to set
``DJANGO_READ_DOT_ENV_FILE=1`` in your system's environment variables and
place the env variables into a ``.env`` file in the root directory of your
Django site repository. See ``env.example`` for an example of such a file.


Site Package and Paths
======================

The site package and path configuration should be found at the beginning of the
default configuration file. Substitute {SITE_NAME} with the name of your site
package.

.. code-block:: python

    import environ
    SITE_PACKAGE = '{SITE_NAME}'
    ROOT_DIR = environ.Path(__file__) - 3
    APPS_DIR = ROOT_DIR.path(SITE_PACKAGE)


Apps
====

Apps installed from django-sodar-core are placed in ``THIRD_PARTY_APPS``. The
following apps need to be included in the list in order for SODAR Core to work:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'crispy_forms',
        'rules.apps.AutodiscoverRulesConfig',
        'djangoplugins',
        'pagedown',
        'markupfield',
        'rest_framework',
        'knox',
        'projectroles.apps.ProjectrolesConfig',
        'dal',
        'dal_select2',
        'dj_iconify.apps.DjIconifyConfig',
    ]


Database
========

Under ``DATABASES``, we recommend setting ``ATOMIC_REQUESTS`` to ``True`` as in
the following sample. This ensures transactions to be atomic on a view-level.
It is still possible to ensure atomicity of specific blocks of code with
Django's ``transaction.atomic`` decorator or context manager.

.. code-block:: python

    DATABASES['default']['ATOMIC_REQUESTS'] = True


Templates
=========

Under ``TEMPLATES['OPTIONS']['context_processors']``, add the required
projectroles processors:

.. code-block:: python

    'projectroles.context_processors.urls_processor',
    'projectroles.context_processors.site_app_processor',
    'projectroles.context_processors.app_alerts_processor',
    'projectroles.context_processors.sidebar_processor',


Email
=====

Under ``EMAIL_CONFIGURATION`` or ``EMAIL``, configure email settings:

.. code-block:: python

    EMAIL_SENDER = env('EMAIL_SENDER', default='noreply@example.com')
    EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='')


Authentication
==============

``AUTHENTICATION_BACKENDS`` should contain the following backend classes:

.. code-block:: python

    AUTHENTICATION_BACKENDS = [
        'rules.permissions.ObjectPermissionBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]

.. note::

    The default setup by cookiecutter-django adds the ``allauth`` package. This
    can be left out of the project if not needed, as it mostly provides adapters
    for e.g. social media account logins. If removing allauth, you can also
    remove unused settings variables starting with ``ACCOUNT_*``.

The following settings remain in your auth configuration:

.. code-block:: python

    AUTH_USER_MODEL = 'users.User'
    LOGIN_REDIRECT_URL = 'home'
    LOGIN_URL = 'login'


Icons
=====

The ``ICONIFY_JSON_ROOT`` setting must point to the appropriate path within
your static files directory in order to make icons work on your SODAR Core based
site.

.. code-block:: python

    ICONIFY_JSON_ROOT = os.path.join(STATIC_ROOT, 'iconify')


Django REST Framework
=====================

To enable ``djangorestframework`` API views and ``knox`` authentication, these
values should be added under ``DEFAULT_AUTHENTICATION_CLASSES``:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            'knox.auth.TokenAuthentication',
        ),
    }


General Site Settings
=====================

For display in projectroles based templates, customize related variables to
describe your site. ``SITE_INSTANCE_TITLE`` may be used to e.g. differentiate
between site versions used for deployment or staging, use in different
organizations, etc.

.. code-block:: python

    SITE_TITLE = 'Name of Your Project'
    SITE_SUBTITLE = env.str('SITE_SUBTITLE', 'Beta')
    SITE_INSTANCE_TITLE = env.str('SITE_INSTANCE_TITLE', 'Deployment Instance Name')


Projectroles Settings
=====================

**Mandatory** projectroles Django settings are explained below:

``PROJECTROLES_SITE_MODE``
    Site mode for remote project metadata synchronization, either ``SOURCE``
    (allow others to read local projects) or ``TARGET`` (read projects from
    another site)
``PROJECTROLES_TARGET_CREATE``
    Whether or not local projects can be created if site is in ``TARGET`` mode.
    If your site is in ``SOURCE`` mode, this setting has no effect.
``PROJECTROLES_INVITE_EXPIRY_DAYS``
    Days until project email invites expire (int)
``PROJECTROLES_SEND_EMAIL``
    Enable/disable email sending (bool)
``PROJECTROLES_EMAIL_SENDER_REPLY``
    Whether replies are expected to the sender address (bool). If set ``False``
    and nothing is set in the ``reply-to`` header, a "do not reply" note is
    added to the email body.
``PROJECTROLES_ENABLE_SEARCH``
    Whether you want to enable SODAR search on your site (boolean)
``PROJECTROLES_DEFAULT_ADMIN``
    User name of the default superuser account used in e.g. replacing an
    unavailable user or performing backend admin commands (string)
``PROJECTROLES_TEMPLATE_INCLUDE_PATH``
    Full system path for custom template includes. The default path is
    ``{APPS_DIR}/templates/include`` (string)
``PROJECTROLES_READ_ONLY_MSG``
    Custom message to be displayed if site read-only mode is enabled (string)

Example:

.. code-block:: python

    # Projectroles Django settings
    PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'TARGET')
    PROJECTROLES_TARGET_CREATE = env.bool('PROJECTROLES_TARGET_CREATE', True)
    PROJECTROLES_INVITE_EXPIRY_DAYS = env.int('PROJECTROLES_INVITE_EXPIRY_DAYS', 14)
    PROJECTROLES_SEND_EMAIL = env.bool('PROJECTROLES_SEND_EMAIL', False)
    PROJECTROLES_EMAIL_SENDER_REPLY = env.bool('PROJECTROLES_EMAIL_SENDER_REPLY', False)
    PROJECTROLES_ENABLE_SEARCH = True
    PROJECTROLES_DEFAULT_ADMIN = env.str('PROJECTROLES_DEFAULT_ADMIN', 'admin')
    PROJECTROLES_READ_ONLY_MSG = env.str('PROJECTROLES_READ_ONLY_MSG', None)


Optional Projectroles Settings
==============================

The following projectroles settings are **optional**:

``PROJECTROLES_EMAIL_HEADER``
    Custom email header (string)
``PROJECTROLES_EMAIL_FOOTER``
    Custom email footer (string)
``PROJECTROLES_SECRET_LENGTH``
    Character length of secret token used in projectroles (int)
``PROJECTROLES_SEARCH_PAGINATION``
    Amount of search results per each app to display on one page (int)
``PROJECTROLES_HELP_HIGHLIGHT_DAYS``
    Days for highlighting tour help for new users (int)
``PROJECTROLES_DISABLE_CATEGORIES``
    If set True, disable categories and only allow a list of projects on the
    root level (boolean) (see note)
``PROJECTROLES_HIDE_PROJECT_APPS``
    Apps hidden from the project sidebar and dropdown menus for all users. The
    app views and URLs are still accessible via other links or knowing the URL.
    The names should correspond to the ``name`` property in project app plugins
    (list)
``PROJECTROLES_DELEGATE_LIMIT``
    The number of delegate roles allowed per project. The amount is limited to 1
    per project if not set, unlimited if set to 0. Will be ignored for remote
    projects synchronized from a source site (int)
``PROJECTROLES_BROWSER_WARNING``
    If true, display a warning to users using Internet Explorer (bool)
``PROJECTROLES_ALLOW_LOCAL_USERS``
    If true, roles for local non-LDAP users can be synchronized from a source
    during remote project sync if they exist on the target site. Similarly,
    local users will be selectable in member dropdowns when selecting users
    (bool)
``PROJECTROLES_KIOSK_MODE``
    If true, allow accessing certain project views *without* user authentication
    in order to e.g. demonstrate features in a kiosk-style deployment. Also
    hides and/or disables views not intended to be used in this mode (bool)
``PROJECTROLES_BREADCRUMB_STICKY``
    Set this false to make project breadcrumb navigation scroll along page
    content. If true, maintain a sticky breadcrumb below the titlebar instead.
    Assumed true if not set (bool)
``PROJECTROLES_ALLOW_ANONYMOUS``
    If true, allow anonymous users to access the site and all projects where
    ``public_guest_access`` is set true (bool)
``PROJECTROLES_SIDEBAR_ICON_SIZE``
    Set the icon size for the project sidebar. Minimum=18, maximum=42,
    default=36 (int)
``PROJECTROLES_SEARCH_OMIT_APPS``
    List of apps to omit from search results (list)
``PROJECTROLES_TARGET_SYNC_ENABLE``
    Enable/disable remote project synchronization as a target site. Ignored for
    source sites (bool)
``PROJECTROLES_TARGET_SYNC_INTERVAL``
    Interval in minutes for remote project synchronization as a target site.
    Ignored for source sites (int)
``PROJECTROLES_API_USER_DETAIL_RESTRICT``
    If true, restrict projectroles API user list and detail view results to
    users who have roles in at least one category or project. For
    ``UserListAPIView`` this will be restricted to contributor access or above.
    ``UserRetrieveAPIView`` is accessible to users with any role (bool)

Example:

.. code-block:: python

    # Projectroles Django settings
    # ...
    PROJECTROLES_EMAIL_HEADER = 'This email has been sent by X from Y'
    PROJECTROLES_EMAIL_FOOTER = 'For assistance contact admin@example.com'
    PROJECTROLES_SECRET_LENGTH = 32
    PROJECTROLES_SEARCH_PAGINATION = 5
    PROJECTROLES_HELP_HIGHLIGHT_DAYS = 7
    PROJECTROLES_DISABLE_CATEGORIES = True
    PROJECTROLES_HIDE_PROJECT_APPS = ['filesfolders']
    PROJECTROLES_DELEGATE_LIMIT = 1
    PROJECTROLES_BROWSER_WARNING = True
    PROJECTROLES_ALLOW_LOCAL_USERS = True
    PROJECTROLES_KIOSK_MODE = False
    PROJECTROLES_API_USER_LIST_RESTRICT=True

.. warning::

    Regarding ``PROJECTROLES_DISABLE_CATEGORIES``: In the current SODAR core
    version remote site access and remote project synchronization are disabled
    if this option is used! Use only if a simple project list is specifically
    required in your site.

.. warning::

    Regarding ``PROJECTROLES_ALLOW_LOCAL_USERS``: Please note that this will
    allow synchronizing project roles to local non-LDAP users based on their
    **user name**. You should personally ensure that the users in question are
    authorized for these roles. Furthermore, only roles for **existing** local
    users will be synchronized. New local users will have to be added manually
    through the Django admin or shell on the target site.

.. warning::

    The ``PROJECTROLES_KIOSK_MODE`` setting is under development and considered
    experimental. More implementation, testing and documentation is forthcoming.


Backend App Settings
====================

The ``ENABLED_BACKEND_PLUGINS`` settings lists backend plugins implemented using
``BackendPluginPoint`` which are enabled in the configuration. For more
information see :ref:`dev_backend_app`.

.. code-block:: python

    ENABLED_BACKEND_PLUGINS = env.list('ENABLED_BACKEND_PLUGINS', None, [])


REST API Settings (Optional)
============================

.. warning::

    General site-based REST API versioning settings have been deprecated in
    SODAR Core v1.0. They will be removed in v1.1. You are expected to provide
    your own app-based media type and versioning schema. For more information,
    see :ref:`dev_project_app_rest_api`.

If your site provides a REST API, the ``SODAR_API_DEFAULT_HOST`` setting should
point to the externally visible host of your server and be configured in your
environment settings. Example:

.. code-block:: python

    SODAR_API_DEFAULT_HOST = env.url('SODAR_API_DEFAULT_HOST', 'http://0.0.0.0:8000')

For enabling page size customization for pagination, it's recommended to set
``REST_FRAMEWORK['PAGE_SIZE']`` using an environment variable as follows:

.. code-block:: python

    REST_FRAMEWORK = {
        'PAGE_SIZE': env.int('SODAR_API_PAGE_SIZE', 100),
    }


LDAP/AD Configuration (Optional)
================================

If you want to utilize LDAP/AD user logins as configured by projectroles, you
can add the following configuration. Make sure to also add the related
environment variables to your configuration.

This part of the setup is **optional**.

.. note::

    In order to support LDAP, make sure you have installed the dependencies from
    ``utility/install_ldap_dependencies.sh`` and ``requirements/ldap.txt``! For
    more information see :ref:`dev_core_install`.

.. note::

    If only using one LDAP/AD server, you can leave the "secondary LDAP server"
    values unset.

.. hint::

    To help debug possible connection problems with your LDAP server(s), set
    ``LDAP_DEBUG=1`` in your environment variables.

.. code-block:: python

    ENABLE_LDAP = env.bool('ENABLE_LDAP', False)
    ENABLE_LDAP_SECONDARY = env.bool('ENABLE_LDAP_SECONDARY', False)
    LDAP_DEBUG = env.bool('LDAP_DEBUG', False)
    LDAP_ALT_DOMAINS = env.list('LDAP_ALT_DOMAINS', None, default=[])

    if ENABLE_LDAP:
        import itertools
        import ldap
        from django_auth_ldap.config import LDAPSearch

        if LDAP_DEBUG:
            ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        # Default values
        LDAP_DEFAULT_CONN_OPTIONS = {ldap.OPT_REFERRALS: 0}
        LDAP_DEFAULT_ATTR_MAP = {
            'first_name': 'givenName',
            'last_name': 'sn',
            'email': 'mail',
        }

        # Primary LDAP server
        AUTH_LDAP_SERVER_URI = env.str('AUTH_LDAP_SERVER_URI', None)
        AUTH_LDAP_BIND_DN = env.str('AUTH_LDAP_BIND_DN', None)
        AUTH_LDAP_BIND_PASSWORD = env.str('AUTH_LDAP_BIND_PASSWORD', None)
        AUTH_LDAP_START_TLS = env.bool('AUTH_LDAP_START_TLS', False)
        AUTH_LDAP_CA_CERT_FILE = env.str('AUTH_LDAP_CA_CERT_FILE', None)
        AUTH_LDAP_CONNECTION_OPTIONS = {**LDAP_DEFAULT_CONN_OPTIONS}
        if AUTH_LDAP_CA_CERT_FILE:
            AUTH_LDAP_CONNECTION_OPTIONS[ldap.OPT_X_TLS_CACERTFILE] = (
                AUTH_LDAP_CA_CERT_FILE
            )
            AUTH_LDAP_CONNECTION_OPTIONS[ldap.OPT_X_TLS_NEWCTX] = 0
        AUTH_LDAP_USER_FILTER = env.str(
            'AUTH_LDAP_USER_FILTER', '(sAMAccountName=%(user)s)'
        )
        AUTH_LDAP_USER_SEARCH_BASE = env.str('AUTH_LDAP_USER_SEARCH_BASE', None)
        AUTH_LDAP_USER_SEARCH = LDAPSearch(
            AUTH_LDAP_USER_SEARCH_BASE,
            ldap.SCOPE_SUBTREE,
            AUTH_LDAP_USER_FILTER,
        )
        AUTH_LDAP_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
        AUTH_LDAP_USERNAME_DOMAIN = env.str('AUTH_LDAP_USERNAME_DOMAIN', None)
        AUTH_LDAP_DOMAIN_PRINTABLE = env.str(
            'AUTH_LDAP_DOMAIN_PRINTABLE', AUTH_LDAP_USERNAME_DOMAIN
        )
        AUTHENTICATION_BACKENDS = tuple(
            itertools.chain(
                ('projectroles.auth_backends.PrimaryLDAPBackend',),
                AUTHENTICATION_BACKENDS,
            )
        )

        # Secondary LDAP server (optional)
        if ENABLE_LDAP_SECONDARY:
            AUTH_LDAP2_SERVER_URI = env.str('AUTH_LDAP2_SERVER_URI', None)
            AUTH_LDAP2_BIND_DN = env.str('AUTH_LDAP2_BIND_DN', None)
            AUTH_LDAP2_BIND_PASSWORD = env.str('AUTH_LDAP2_BIND_PASSWORD', None)
            AUTH_LDAP2_START_TLS = env.bool('AUTH_LDAP2_START_TLS', False)
            AUTH_LDAP2_CA_CERT_FILE = env.str('AUTH_LDAP2_CA_CERT_FILE', None)
            AUTH_LDAP2_CONNECTION_OPTIONS = {**LDAP_DEFAULT_CONN_OPTIONS}
            if AUTH_LDAP2_CA_CERT_FILE:
                AUTH_LDAP2_CONNECTION_OPTIONS[ldap.OPT_X_TLS_CACERTFILE] = (
                    AUTH_LDAP2_CA_CERT_FILE
                )
                AUTH_LDAP2_CONNECTION_OPTIONS[ldap.OPT_X_TLS_NEWCTX] = 0
            AUTH_LDAP2_USER_FILTER = env.str(
                'AUTH_LDAP2_USER_FILTER', '(sAMAccountName=%(user)s)'
            )
            AUTH_LDAP2_USER_SEARCH_BASE = env.str(
                'AUTH_LDAP2_USER_SEARCH_BASE', None
            )
            AUTH_LDAP2_USER_SEARCH = LDAPSearch(
                AUTH_LDAP2_USER_SEARCH_BASE,
                ldap.SCOPE_SUBTREE,
                AUTH_LDAP2_USER_FILTER,
            )
            AUTH_LDAP2_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
            AUTH_LDAP2_USERNAME_DOMAIN = env.str('AUTH_LDAP2_USERNAME_DOMAIN')
            AUTH_LDAP2_DOMAIN_PRINTABLE = env.str(
                'AUTH_LDAP2_DOMAIN_PRINTABLE', AUTH_LDAP2_USERNAME_DOMAIN
            )
            AUTHENTICATION_BACKENDS = tuple(
                itertools.chain(
                    ('projectroles.auth_backends.SecondaryLDAPBackend',),
                    AUTHENTICATION_BACKENDS,
                )
            )


.. _app_projectroles_settings_oidc:

OpenID Connect (OIDC) Configuration (Optional)
==============================================

SODAR Core supports single sign-on authentication via OIDC from v1.0 onwards. To
enable OIDC logins, add the following Django settings and related environment
variables to your configuration.

This part of the setup is **optional**.

OIDC support is implemented using the ``social_django`` app. You first need to
add the app to your ``INSTALLED_APPS``:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'social_django',  # For OIDC authentication
    ]

Next, you must add the app's URL patterns in ``config/urls.py``:

.. code-block:: python

    urlpatterns = [
        # ...
        # Social auth for OIDC support
        path('social/', include('social_django.urls')),
    ]

Finally, you should add the following Django settings in your ``base.py``
settings file:

.. code-block:: python

    ENABLE_OIDC = env.bool('ENABLE_OIDC', False)

    if ENABLE_OIDC:
        AUTHENTICATION_BACKENDS = tuple(
            itertools.chain(
                ('social_core.backends.open_id_connect.OpenIdConnectAuth',),
                AUTHENTICATION_BACKENDS,
            )
        )
        TEMPLATES[0]['OPTIONS']['context_processors'] += [
            'social_django.context_processors.backends',
            'social_django.context_processors.login_redirect',
        ]
        SOCIAL_AUTH_JSONFIELD_ENABLED = True
        SOCIAL_AUTH_JSONFIELD_CUSTOM = 'django.db.models.JSONField'
        SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
        SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = [
            'username',
            'name',
            'first_name',
            'last_name',
            'email',
        ]
        SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = env.str(
            'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT', None
        )
        SOCIAL_AUTH_OIDC_KEY = env.str('SOCIAL_AUTH_OIDC_KEY', 'CHANGEME')
        SOCIAL_AUTH_OIDC_SECRET = env.str('SOCIAL_AUTH_OIDC_SECRET', 'CHANGEME')
        SOCIAL_AUTH_OIDC_USERNAME_KEY = env.str(
            'SOCIAL_AUTH_OIDC_USERNAME_KEY', 'username'
        )

Critical settings which should be provided through environment variables:

``SOCIAL_AUTH_OIDC_OIDC_ENDPOINT``
    Endpoint URL for the OIDC provider. The configuration file
    ``.well-known/openid-configuration`` is expected to be found under this URL.
``SOCIAL_AUTH_OIDC_KEY``
    Your client ID in the OIDC provider.
``SOCIAL_AUTH_OIDC_SECRET``
    Secret for the OIDC provider.
``SOCIAL_AUTH_OIDC_USERNAME_KEY``
    If the username key of the browser is expected to be something other than
    the default ``username``, it can be configured here. The values in this must
    be unique and should preferably be human readable. If the OIDC provider does
    not return such a username directly, it is possible to e.g. use the user
    email as a unique user name.

If you want to provide a custom template for directing login to your OIDC
provider, add it as ``{PROJECTROLES_TEMPLATE_INCLUDE_PATH}/_login_oidc.html``
(by default: ``your_site/templates/include/_login_oidc.html``). The include will
be displayed as an element in the login view.

Below is an example of a custom template. You can e.g. change the content of the
link to the logo of your OIDC provider. Note that the login URL must equal
``{% url 'social:begin' 'oidc' %}?next={{ oidc_redirect_url|default:'/' }}`` to
ensure it works in all views.

.. code-block:: django

    <a role="button" class="btn btn-md btn-info btn-block" id="sodar-login-oidc-link"
       href="{% url 'social:begin' 'oidc' %}?next={{ oidc_redirect_url|default:'/' }}">
      <i class="iconify" data-icon="mdi:login-variant"></i> OpenID Connect Login
    </a>


SAML SSO Configuration (Removed in v1.0)
========================================

.. note::

    SAML support has been removed in SODAR Core v1.0. It has been replaced with
    the possibility to set up OpenID Connect (OIDC) authentication. The library
    previously used for SAML in SODAR Core is incompatible with Django v4.x. We
    are unaware of SODAR Core based projects requiring SAML at this time. If
    there are specific needs to use SAML on a SODAR Core based site, we are
    happy to review pull requests to reintroduce it. Please note the
    implementation has to support Django v4.2+.


Global JS/CSS Include Modifications (Optional)
==============================================

It is possible to supplement (or replace, see below) global Javascript and CSS
includes of your SODAR Core site without altering the base template. You can
place a list of custom includes into the list variables
``PROJECTROLES_CUSTOM_JS_INCLUDES`` and ``PROJECTROLES_CUSTOM_CSS_INCLUDES``.
These can either be local static file paths or web URLs to e.g. CDN served
files.

If using the default CDN imports for JQuery, Bootstrap4 etc. are not an optimal
solution in your use case due to e.g. network issues, you can disable these
includes by setting ``PROJECTROLES_DISABLE_CDN_INCLUDES`` to ``True``.

.. warning::

    If disabling the default CDN includes, you **must** provide replacements for
    **all** disabled files in your custom includes. Otherwise your SODAR Core
    based site will not function correctly!

Example:

.. code-block:: python

    PROJECTROLES_DISABLE_CDN_INCLUDES = True
    PROJECTROLES_CUSTOM_JS_INCLUDES = [
        STATIC_ROOT + '/your/path/jquery-3.3.1.min.js',
        STATIC_ROOT + '/your/path/popper.min.js',
        'https://some-cdn.com/bootstrap.min.js',
        # ...
    ]
    PROJECTROLES_CUSTOM_CSS_INCLUDES = [
        STATIC_ROOT + '/your/path/bootstrap.min.css',
        # ...
    ]

It is also possible to define inline HTML in an environment variable and include
it in the ``head`` tag of the base template. To use this feature, add HTML
script as the value of the variable ``PROJECTROLES_INLINE_HEAD_INCLUDE``.

Example:

.. code-block::

    PROJECTROLES_INLINE_HEAD_INCLUDE="<meta name=\"keywords\" content=\"SODAR Core\">"

.. warning::

    Make sure you are inputting valid HTML or you risk breaking the HTML on
    **all** pages of your SODAR Core based site!


Modifying SODAR_CONSTANTS (Optional)
====================================

String identifiers used globally in SODAR project management are defined in the
``SODAR_CONSTANTS`` dictionary. It can be imported into your app code with the
import:

.. code-block:: python

    from projectroles.models import SODAR_CONSTANTS

If you need to update or extend the constants for use your site, you can import
the default dictionary into your Django settings and modify it as necessary with
the following snippet:

.. code-block:: python

    from projectroles.constants import get_sodar_constants
    SODAR_CONSTANTS = get_sodar_constants(default=True)
    # Your changes here..

.. warning::

    Modifying existing default constants may result in unwanted issues,
    especially on a site which already contains created projects. Proceed with
    caution!


Logging (Optional)
==================

It is recommended to add "projectroles" under ``LOGGING['loggers']``. For
production, ``ERROR`` debug level is recommended.

The example site and SODAR Django Site template provide the ``LOGGING_APPS`` and
``LOGGING_FILE_PATH`` helpers for easily adding SODAR Core apps to logging and
providing a system path for optional log file writing.

If you are using ``ManagementCommandLogger`` for logging your management command
output, you can disable redundant console input in e.g. your test configuration
by setting ``LOGGING_DISABLE_CMD_OUTPUT`` to ``True``.
