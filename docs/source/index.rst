.. _manual_main:

Welcome to the SODAR Core documentation!
========================================

SODAR Core is a framework for Django web applications development. It is
primarily targeted towards project and data management in a scientific setting,
but can also serve more general purposes where project-based data encapsulation
is needed.

The framework provides a suite of Django apps that can be included on your
website to enable project-based access control, dynamic content management,
standardized UI and REST API as well as general-purpose apps for managing your
projects.

SODAR Core is fully `open source <https://github.com/bihealth/sodar-core>`_ and
made available under the permissive
`MIT license <https://opensource.org/license/MIT>`_.

How to Read This Manual
-----------------------

There are two ways:

Front to Back
  If you have the time and patience, reading the whole manual will teach
  you everything.

Jump Around (recommended)
  Start with :ref:`for_the_impatient` and/or :ref:`user_stories`, skim over the
  summary of each app, and explore what interests you most.

What SODAR Core Is and What It is Not
-------------------------------------

SODAR Core

- is Django-based and you will need some knowledge about Django programming in
  Python for it to be useful,
- provides you with libraries for developing your own applications.

SODAR Core

- is NOT a ready-made web application,
- is NOT for entry-level Python programmers (you will need intermediate Django
  knowledge; you probably do not want to base your first Django web application
  on SODAR Core).

What's Inside SODAR Core
------------------------

The main functionality offered by SODAR Core comes from the ``projectroles``
app, which provides user authentication, project management (including access
control), and a plugin system for dynamic content management. Furthermore, SODAR
Core comes with a number of built-in apps which can be enabled to activate
additional functionality.

The full list of apps are shown in the table of contents. See also the
:ref:`overview_sodar_core_apps` section for a summary of what each app does.

Highlights of application features:

- Project-based user access control
- Dynamic app content management
- Advanced project activity logging
- Small file uploading and browsing
- Managing server-side background jobs
- Caching and aggregation of data from external services
- Tracking site information and statistics

What's Inside This Documentation
--------------------------------

Overview & Getting Started
  This part aims at getting you an birds-eye view of SODAR Core and its usage.

SODAR Core Apps
  This part documents each Django app that ships with SODAR. As
  a reminder, in Django development, *apps* are re-usable modules with code
  for supporting a certain use case.

Project Info
  This part of the documentation provides meta information about the project
  and the full changelog.

What's Not Inside This Documentation
------------------------------------

You should know the following before this documentation is useful to you:

Python Programming
  There's tons of documentation on the internet but the `official Python
  documentation <https://docs.python.org/3/>`_ is a good starting point as
  any.

Django Development
  For learning about Django, head over to the
  `official Django documentation <https://docs.djangoproject.com/en/5.2/>`_.

HTML / Javascript / CSS / Bootstrap 4
  Together with Django, SODAR Core provides a framework to plug in your own
  HTML and related front-end code. We assume that you have web development
  experience and in particular know your way around Bootstrap 4.

  We're using the Bootstrap 4 CSS framework and you can learn about it in many
  places including `the official documentation
  <https://getbootstrap.com/docs/4.3/getting-started/introduction/>`_

.. note::

   You can find a pre-built version of this documentation at
   `readthedocs.io <https://sodar-core.readthedocs.io/en/latest/>`_.
   If you view these files on e.g. GitHub, beware that their renderer does not
   render the ReStructuredText files correctly and content may be missing.


.. toctree::
    :maxdepth: 2
    :caption: Overview & Getting Started
    :name: overview_getting_started
    :hidden:

    Overview <overview>
    getting_started
    for_the_impatient
    user_stories
    glossary

.. toctree::
    :maxdepth: 2
    :caption: SODAR Core Apps
    :name: sodar_core_apps
    :hidden:

    Projectroles <app_projectroles>
    Adminalerts <app_adminalerts>
    Appalerts <app_appalerts>
    Bgjobs <app_bgjobs>
    Filesfolders <app_filesfolders>
    Siteinfo <app_siteinfo>
    Sodarcache <app_sodarcache>
    Timeline <app_timeline>
    Tokens <app_tokens>
    Userprofile <app_userprofile>

.. toctree::
    :maxdepth: 2
    :caption: REST API Documentation
    :name: api_documentation
    :hidden:

    Overview <rest_api_overview>
    Projectroles <app_projectroles_api_rest>
    Filesfolders <app_filesfolders_api_rest>
    Sodarcache <app_sodarcache_api_rest>
    Timeline <app_timeline_api_rest>
    Tokens <app_tokens_api_rest>

.. toctree::
    :maxdepth: 2
    :caption: Developing Your Site
    :name: development_site
    :hidden:

    Overview <dev_site>
    Integration to an Existing Site <dev_integration>
    Project Apps <dev_project_app>
    Site Apps <dev_site_app>
    Backend Apps <dev_backend_app>
    General Resources <dev_resource>
    General Guidelines <dev_guideline>

.. toctree::
    :maxdepth: 2
    :caption: Contribute to SODAR Core
    :name: development_core
    :hidden:

    Overview <dev_core_overview>
    contributing
    code_of_conduct
    Installation <dev_core_install>
    Guidelines <dev_core_guide>
    Development Resources <dev_core_resource>

.. toctree::
    :maxdepth: 2
    :caption: Project Information
    :name: project_info
    :hidden:
    :titlesonly:

    repository
    major_changes
    Full Changelog <changelog>
