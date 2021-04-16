.. _app_appalerts:


Appalerts App
^^^^^^^^^^^^^

The ``appalerts`` site app enables SODAR Core apps to generate alerts for users.
The user will receive a notify about these alerts anywhere on the site even if
they are tied to a specific project.


Basics
======

**TODO**


Installation
============

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.

Django Settings
---------------

**TODO**

URL Configuration
-----------------

In the Django URL configuration file, add the following line under
``urlpatterns`` to include adminalerts URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^alerts/', include('appalerts.urls')),
    ]

Migrate Database and Register Plugin
------------------------------------

To migrate the Django database and register the appalerts site app plugin,
run the following management command:

.. code-block:: console

    $ ./manage.py migrate

In addition to the database migration operation, you should see the following
output:

.. code-block:: console

    Registering Plugin for appalerts.plugins.SiteAppPlugin
    Registering Plugin for appalerts.plugins.BackendPlugin


Usage
=====

When logged in as an authenticated user, you can find the "App Alerts" option in
your user dropdown menu. This displays a list of active alerts you have in the
system. You have the possibility to dismiss alerts or follow a related link. The
latter action will also dismiss the alert.

**TODO:** Screenshot

When you are anywhere on the site, a notification about existing events will
appear on the top bar of the site.

**TODO:** Screenshot

For creation of alers, see the development documentation.
