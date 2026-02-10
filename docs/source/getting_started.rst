.. _getting_started:


Getting Started
^^^^^^^^^^^^^^^

This document provides instructions and guidelines for integrating projectroles
and other SODAR Core apps into your Django site. Whether you want to set up a
new Django site, or integrating the projectroles app into an existing site, you
can follow one of the recommended options in this section.


Requirements
************

Major requirements for integrating projectroles and other SODAR Core apps into
your Django site are listed below. For a complete requirement list, see the
``requirements`` and ``utility`` directories in the repository.

- Ubuntu/Debian (Ubuntu 24.04 LTS recommended and supported for development)
- System library requirements (see the ``utility`` directory and/or your own
  Django project)
- Python 3.11-3.13 (3.13 recommended)
- Django 5.2
- PostgreSQL >=12 (16 recommended) and psycopg2-binary
- Bootstrap 4.x
- JQuery 3.3.x
- Shepherd and Tether
- Clipboard.js
- DataTables

For more details on installation and requirements for local development, see
:ref:`dev_core_install`.


Installation
************

This section shows three methods to start using SODAR Core.

SODAR Django Site Template (Recommended)
========================================

When setting up a new :term:`SODAR Core based site<SODAR Core Based Site>`, it
is strongly recommended to use
`sodar-django-site <https://github.com/bihealth/sodar-django-site>`_ as the
template. The repository contains a minimal :term:`Django site<Django Site>`
pre-configured with projectroles and other
:term:`SODAR Core apps<SODAR Core App>`. The ``main`` branch of this project
always integrates the latest stable release of SODAR Core and projectroles.

To set up your site with this template, clone the repository and follow the
installation instructions in the README.rst file.


Cookiecutter-Django
===================

If the SODAR Django site template does not suit your needs, it is also possible
to set up your site using `cookiecutter-django <https://github.com/pydanny/cookiecutter-django/>`_.
In this case, follow the instructions in the :ref:`Existing Site Integration
<dev_projectroles_integration>` document as if you were integrating SODAR Core
to an existing Django site.

.. note::

    The project was created using an old version of the cookiecutter script and
    evolved from there. This means the site created by the version currently may
    differ in several ways from how SODAR Core is set up. This method is
    recommended only for experienced Django developers.

.. note::

    For any other issues regarding the cookiecutter-django setup, see the
    cookiecutter-django documentation.


Integration in an Existing Site
================================

If you already have a working site and want to migrate it to SODAR Core, see
the :ref:`Existing Site Installation <dev_projectroles_integration>` document.


Next Steps
**********

You are now ready to develop your Django site using the SODAR Core framework.
You can start by configuring the :ref:`app_projectroles` and, optionally, the
other built-in apps. To modify default SODAR Core and projectroles settings, see
the :ref:`app_projectroles_settings` document. For customizing the look and feel
of your site, check out the :ref:`customization tips <app_projectroles_custom>`.

Later on, you may proceed to install or develop other apps as needed (see the
:ref:`dev_site` document for instructions).
