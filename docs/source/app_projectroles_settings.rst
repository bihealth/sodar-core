.. _app_projectroles_settings:


Projectroles Django Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document describes the Django settings for the ``projectroles`` app, which
also control the configuration of other apps in a SODAR Core based site.

These settings are usually found in ``config/settings/*.py``, with
``config/settings/base.py`` being the default configuration other files may
override or extend.

If your site is based on ``sodar_django_site``, mandatory settings are already
set to their default values. In that case, you only need to modify or customize
them where applicable.

If you are integrating django-sodar-core with an existing Djagno site or
building your site from scratch without the recommended template, make sure to
add all mandatory settings into your project.

For values retrieved from environment variables, make sure to configure your
env accordingly. For development and testing, using ``DJANGO_READ_DOT_ENV_FILE``
is recommended.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


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
    ]


Database
========

Under ``DATABASES``, the setting below is recommended:

.. code-block:: python

    DATABASES['default']['ATOMIC_REQUESTS'] = False

.. note::

    If this conflicts with your existing set up, you can modify the code in your
    other apps to use e.g. ``@transaction.atomic``.

.. note::

    This setting mostly is used for the ``sodar_taskflow`` transactions
    supported by projectroles but not commonly used, so having this setting as
    True *may* cause no issues. However, it is not officially supported at this
    time.


Templates
=========

Under ``TEMPLATES['OPTIONS']['context_processors']``, add the projectroles URLs
processor:

.. code-block:: python

    'projectroles.context_processors.urls_processor',


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

**Mandatory** projectroles app settings are explained below:

* ``PROJECTROLES_SITE_MODE``: Site mode for remote project metadata
  synchronization, either ``SOURCE`` (allow others to read local projects) or
  ``TARGET`` (read projects from another site)
* ``PROJECTROLES_TARGET_CREATE``: Whether or not local projects can be created
  if site is in ``TARGET`` mode. If your site is in ``SOURCE`` mode, this
  setting has no effect.
* ``PROJECTROLES_INVITE_EXPIRY_DAYS``: Days until project email invites expire
  (int)
* ``PROJECTROLES_SEND_EMAIL``: Enable/disable email sending (bool)
* ``PROJECTROLES_ENABLE_SEARCH``: Whether you want to enable SODAR search on
  your site (boolean)

Example:

.. code-block:: python

    # Projectroles app settings
    PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'TARGET')
    PROJECTROLES_TARGET_CREATE = env.bool('PROJECTROLES_TARGET_CREATE', True)
    PROJECTROLES_INVITE_EXPIRY_DAYS = env.int('PROJECTROLES_INVITE_EXPIRY_DAYS', 14)
    PROJECTROLES_SEND_EMAIL = env.bool('PROJECTROLES_SEND_EMAIL', False)
    PROJECTROLES_ENABLE_SEARCH = True


Optional Projectroles Settings
==============================

The following projectroles settings are **optional**:

* ``PROJECTROLES_SECRET_LENGTH``: Character length of secret token used in
  projectroles (int)
* ``PROJECTROLES_SEARCH_PAGINATION``: Amount of search results per each app to
  display on one page (int)
* ``PROJECTROLES_HELP_HIGHLIGHT_DAYS``: Days for highlighting tour help for new
  users (int)
* ``PROJECTROLES_DISABLE_CATEGORIES``: If set True, disable categories and only
  allow a list of projects on the root level (boolean) (see note)
* ``PROJECTROLES_HIDE_APP_LINKS``: Apps hidden from the project sidebar and
  dropdown menus for non-superusers. The app views and URLs are still
  accessible. The names should correspond to the ``name`` property in each
  project app's plugin (list)

Example:

.. code-block:: python

    # Projectroles app settings
    # ...
    PROJECTROLES_SECRET_LENGTH = 32
    PROJECTROLES_SEARCH_PAGINATION = 5
    PROJECTROLES_HELP_HIGHLIGHT_DAYS = 7
    PROJECTROLES_DISABLE_CATEGORIES = True
    PROJECTROLES_HIDE_APP_LINKS = ['filesfolders']

.. warning::

    Regarding ``PROJECTROLES_DISABLE_CATEGORIES``: In the current SODAR core
    version remote site access and remote project synchronization are disabled
    if this option is used! Use only if a simple project list is specifically
    required in your site.


Backend App Settings
====================

The ``ENABLED_BACKEND_PLUGINS`` settings lists backend plugins implemented using
``BackendPluginPoint`` which are enabled in the configuration. For more
information see :ref:`dev_backend_app`.

.. code-block:: python

    ENABLED_BACKEND_PLUGINS = env.list('ENABLED_BACKEND_PLUGINS', None, [])


SODAR API Settings (Optional)
=============================

There are also settings for providing and extending the general SODAR API,
which is currently in development.

The API uses accept header versioning. The ``SODAR_API_MEDIA_TYPE`` setting is
by default set to the SODAR Core API media type, but should preferably be
changed to your organization and API identification if API views are modified or
introduced. The ``SODAR_API_DEFAULT_HOST`` setting should post to the externally
visible host of your server and be configured in your environment settings.

These settings are **optional**. Default values will be used if they are unset.

Example:

.. code-block:: python

    SODAR_API_DEFAULT_VERSION = '0.1'
    SODAR_API_ACCEPTED_VERSIONS = [SODAR_API_DEFAULT_VERSION]
    SODAR_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar-core+json'  # Change this
    SODAR_API_DEFAULT_HOST = SODAR_API_DEFAULT_HOST = env.url('SODAR_API_DEFAULT_HOST', 'http://0.0.0.0:8000')


LDAP/AD Configuration (Optional)
================================

If you want to utilize LDAP/AD user logins as configured by projectroles, you
can add the following configuration. Make sure to also add the related env
variables to your configuration.

This part of the setup is **optional**.

.. note::

    In order to support LDAP, make sure you have installed the dependencies from
    ``utility/install_ldap_dependencies.sh`` and ``requirements/ldap.txt``! For
    more information see :ref:`dev_sodar_core`.

.. note::

    If only using one LDAP/AD server, you can leave the "secondary LDAP server"
    values unset.

.. code-block:: python

    ENABLE_LDAP = env.bool('ENABLE_LDAP', False)
    ENABLE_LDAP_SECONDARY = env.bool('ENABLE_LDAP_SECONDARY', False)

    if ENABLE_LDAP:
        import itertools
        import ldap
        from django_auth_ldap.config import LDAPSearch

        # Default values
        LDAP_DEFAULT_CONN_OPTIONS = {ldap.OPT_REFERRALS: 0}
        LDAP_DEFAULT_FILTERSTR = '(sAMAccountName=%(user)s)'
        LDAP_DEFAULT_ATTR_MAP = {
            'first_name': 'givenName', 'last_name': 'sn', 'email': 'mail'}

        # Primary LDAP server
        AUTH_LDAP_SERVER_URI = env.str('AUTH_LDAP_SERVER_URI', None)
        AUTH_LDAP_BIND_DN = env.str('AUTH_LDAP_BIND_DN', None)
        AUTH_LDAP_BIND_PASSWORD = env.str('AUTH_LDAP_BIND_PASSWORD', None)
        AUTH_LDAP_CONNECTION_OPTIONS = LDAP_DEFAULT_CONN_OPTIONS

        AUTH_LDAP_USER_SEARCH = LDAPSearch(
            env.str('AUTH_LDAP_USER_SEARCH_BASE', None),
            ldap.SCOPE_SUBTREE, LDAP_DEFAULT_FILTERSTR)
        AUTH_LDAP_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
        AUTH_LDAP_USERNAME_DOMAIN = env.str('AUTH_LDAP_USERNAME_DOMAIN', None)
        AUTH_LDAP_DOMAIN_PRINTABLE = env.str(
            'AUTH_LDAP_DOMAIN_PRINTABLE', AUTH_LDAP_USERNAME_DOMAIN)

        AUTHENTICATION_BACKENDS = tuple(itertools.chain(
           ('projectroles.auth_backends.PrimaryLDAPBackend',),
           AUTHENTICATION_BACKENDS,))

        # Secondary LDAP server
        if ENABLE_LDAP_SECONDARY:
            AUTH_LDAP2_SERVER_URI = env.str('AUTH_LDAP2_SERVER_URI', None)
            AUTH_LDAP2_BIND_DN = env.str('AUTH_LDAP2_BIND_DN', None)
            AUTH_LDAP2_BIND_PASSWORD = env.str('AUTH_LDAP2_BIND_PASSWORD', None)
            AUTH_LDAP2_CONNECTION_OPTIONS = LDAP_DEFAULT_CONN_OPTIONS

            AUTH_LDAP2_USER_SEARCH = LDAPSearch(
                env.str('AUTH_LDAP2_USER_SEARCH_BASE', None),
                ldap.SCOPE_SUBTREE, LDAP_DEFAULT_FILTERSTR)
            AUTH_LDAP2_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
            AUTH_LDAP2_USERNAME_DOMAIN = env.str('AUTH_LDAP2_USERNAME_DOMAIN')
            AUTH_LDAP2_DOMAIN_PRINTABLE = env.str(
                'AUTH_LDAP2_DOMAIN_PRINTABLE', AUTH_LDAP_USERNAME_DOMAIN)

            AUTHENTICATION_BACKENDS = tuple(itertools.chain(
                ('projectroles.auth_backends.SecondaryLDAPBackend',),
                AUTHENTICATION_BACKENDS,))

Logging (Optional)
==================

It is also recommended to add "projectroles" under ``LOGGING['loggers']``. For
production, ``INFO`` debug level is recommended.


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
