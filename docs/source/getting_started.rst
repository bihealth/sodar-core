.. _getting_started:


Getting Started
^^^^^^^^^^^^^^^

Installation and basic concepts of the SODAR Core framework and its apps are
detailed in this document.


Installation
============

The ``django-sodar-core`` package can be installed into your Django project
from PyPI as follows. It is strongly recommended to specify a version tag, as
the package is under active development and breaking changes are expected.

.. code-block:: console

    pip install django-sodar-core==0.10.2

Please note that the django-sodar-core package only installs
:term:`Django apps<Django App>`, which you need to include in a
:term:`Django web site<Django Site>` project. For instructions for integrating
SODAR Core into an existing Django site or setting up a new site,
see the :ref:`projectroles app documentation <app_projectroles>`.


SODAR Core Apps
===============

The following Django apps will be installed when installing the
``django-sodar-core`` package:

- **projectroles**: Base app for project access management and dynamic app
  content management. All other apps require the integration of projectroles.
- **adminalerts**: Site app for displaying site-wide messages to all users.
- **appalerts**: Site app and backend for raising alerts to users from apps.
- **bgjobs**: Project app for managing background jobs.
- **siteinfo**: Site app for displaying site information and statistics for
  administrators.
- **sodarcache**: Generic caching and aggregation of data referring to external
  services.
- **taskflowbackend**: Backend app providing an API for the optional
  ``sodar_taskflow`` transaction service.
- **timeline**: Project app for logging and viewing project-related activity.
- **tokens**: Token management for API access.
- **userprofile**: Site app for viewing user profiles.


Requirements
============

Major requirements for integrating projectroles and other SODAR Core apps into
your Django site are listed below. For a complete requirement list, see the
``requirements`` and ``utility`` directories in the repository.

- Ubuntu (20.04 Focal recommended and supported) / CentOS 7
- System library requirements (see the ``utility`` directory and/or your own
  Django project)
- Python >=3.7 (**NOTE:** Python 3.6 no longer supported in SODAR Core v0.10+)
- Django 3.2
- PostgreSQL >=9.6 and psycopg2-binary
- Bootstrap 4.x
- JQuery 3.3.x
- Shepherd and Tether
- Clipboard.js
- DataTables

For more details on installation and requirements for local development, see
:ref:`dev_sodar_core`.


Next Steps
==========

To proceed with using the SODAR Core framework in your Django site, you must
first install and integrate the ``projectroles`` app. See the
:ref:`projectroles app documentation <app_projectroles>` for instructions.

Once projectroles has been integrated into your site, you may proceed to
install other apps as needed.
