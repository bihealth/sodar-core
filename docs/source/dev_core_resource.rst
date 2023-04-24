.. _dev_core_resource:

SODAR Core Development Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for development of the SODAR
Core package.


App Development
===============

Guidelines for developing **internal** SODAR Core apps (ones included when
installing the django-sodar-core package) are detailed in this section.

For the most part, developing apps within the SODAR Core package follow the
same guidelines as detailed in :ref:`dev_site`. However, there are certain
exceptions.

REST API Views
--------------

For internal SODAR Core apps, you need to use core counterparts to the mixins
than provided for SODAR Core using sites. The counterparts use different media
type and versioning from views to be implemented on external sites. This is to
prevent version number clashes requiring changes in external APIs. The classes
can be found in ``projectroles.views_api`` and are as follows:

- ``CoreAPIVersioning``
- ``CoreAPIRenderer``
- ``CoreAPIBaseMixin``
- ``CoreAPIBaseProjectMixin``
- ``CoreAPIGenericProjectMixin``

For detailed API descriptions, see docstrings in the ``view_api`` module. The
media type and versioning for these views are **hardcoded** and should not be
changed, except version information upon a new release of SODAR Core.


Projectroles App Development
============================

This section details issues regarding updates to the ``projectroles`` app.

.. warning::

    As all other apps in SODAR Core as well as sites implementing SODAR Core
    are based on projectroles, changes to this app need to be implemented and
    tested with extra care. Also make sure to provide detailed documentation for
    all breaking changes.

Projectroles App Settings
-------------------------

Projectroles defines its own app settings in ``projectroles/app_settings.py``.
These are not expected to be altered by SODAR Core based sites. These settings
add the ``local`` attribute, which allows/disallows editing the value on a
``TARGET`` site.

To alter projectroles app settings when developing the app, update the
``PROJECTROLES_APP_SETTINGS`` dictionary as follows:

.. code-block:: python

     'example_setting': {
         'scope': 'PROJECT',  # PROJECT/USER
         'type': 'STRING',  # STRING/INTEGER/BOOLEAN
         'default': 'example',
         'options': ['example', 'example2'],  # Optional, only for settings of type STRING or INTEGER
         'label': 'Project setting',  # Optional, defaults to name/key
         'placeholder': 'Enter example setting here',  # Optional
         'description': 'Example project setting',  # Optional
         'user_modifiable': True,  # Optional, show/hide in forms
         'local': False,  # Allow editing in target site forms if True
     }


Testing
=======

To run unit tests, you have to install Chrome and Chromedriver followed by the
Python test requirements:

.. code-block:: console

    $ sudo utility/install_chrome.sh
    $ pip install -r requirements/test.txt

Now you can run all tests with the following make command:

.. code-block:: console

    $ make test

If you want to only run a certain subset of tests, use e.g.:

.. code-block:: console

    $ make test arg=projectroles.tests.test_views


Remote Site Development
=======================

For developing remote site features, you will want to run two or more SODAR Core
example sites concurrently: one ``SOURCE`` site and one or more ``TARGET``
sites.

For running a single ``TARGET`` site in addition to the main site, the fastest
way to get started is the following:

First, set up a second database called ``sodar_core_target`` using
``utility/setup_database.sh``.

Next, migrate the new database and create a superuser using
``make manage_target``. The admin user name is hardcoded into ``admin_target``
in ``config.settings.target``, so you are strongly recommended to use that
name for your target site admin.

.. code-block:: console

    $ make manage_target arg=migrate
    $ make manage_target arg=createsuperuser

Launch your site with ``make serve_target``. By default, you can access the site
at Port ``8001`` on localhost. The port can be altered by providing the
``target_port`` parameter, e.g. ``make serve_target target_port=8002``.
Management commands to the target site can be issued with the ``make manage_target``
make command.

Due to how cookies are set by Django, you currently may have to relogin when
switching to a different site on your browser. As a workaround you can launch
one of the sites in a private/incognito window or use different browsers.

If you need to create multiple target sites for testing ``PEER`` synchronization
features, make sure that you have a separate SODAR Core database for each site
and launch each site on a different port on localhost. The configuration
``local_target2.py`` is included for developing with multiple ``TARGET`` sites.
