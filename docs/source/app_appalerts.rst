.. _app_appalerts:


Appalerts App
^^^^^^^^^^^^^

The ``appalerts`` site app enables SODAR Core apps to generate alerts for users.
The user will receive a notify about these alerts anywhere on the site even if
they are tied to a specific project.


Basics
======

The app consists of two plugins: the site app plugin for alert displaying and
the backend plugin to create and access alerts from your SODAR Core based apps.


Installation
============

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.

Django Settings
---------------

Add the app into ``THIRD_PARTY_APPS`` in ``config/settings/base.py`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'adminalerts.apps.AdminalertsConfig',
    ]

Next, make sure the context processor for app alerts is included in the
``TEMPLATES`` dictionary:

.. code-block:: python

    TEMPLATES = [
        {
            'OPTIONS': {
                'context_processors': {
                    # ...
                    'projectroles.context_processors.app_alerts_processor',
                }
            }
        }

To set the interval for JQuery status updates in the title bar, use
``APPALERTS_STATUS_INTERVAL`` and provide the value in seconds. Example:

.. code-block:: python

    APPALERTS_STATUS_INTERVAL = env.int('APPALERTS_STATUS_INTERVAL', 5)

URL Configuration
-----------------

In the Django URL configuration file, add the following line under
``urlpatterns`` to include adminalerts URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^alerts/app/', include('appalerts.urls')),
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

Base Template Include
---------------------

If your site is overriding the base site template, the following snippet should
be added in the ``javascript`` block of ``{SITE}/templates/base.html`` to enable
appalerts JQuery:

.. code-block:: django

    {% block javascript %}
      {# ... #}
      <!-- App alerts Javascript -->
      {% include 'projectroles/_appalerts_include.html' %}
    {% endblock javascript %}


Usage
=====

When logged in as an authenticated user, you can find the "App Alerts" option in
your user dropdown menu. This displays a list of active alerts that you currently
have in the system. Under the dropdown menu labeled 'Alert Operations', you have
the option to dismiss all active alerts or view previously dismissed alerts.

When you are anywhere on the site, a notification about existing events will
appear on the top bar of the site.

.. figure:: _static/app_appalerts/app_alerts.png
    :align: center
    :scale: 50%

    App alert list and title bar notification


Backend API
===========

For creation and management of alerts, it is recommended to use the backend API
to retrieve and use the plugin, without the need for hard-coded includes. The
``add_alert()`` helper is also provided to simplify alert creation. See the
accompanying API documentation for details.

.. note::

    The logic for alert life cycle management is mostly left to the app issuing
    alerts. Alerts with an accompanying project or plugin will get deleted with
    the accompanying object. Please try to make sure you will not e.g. provide
    a related URL to the event which may no longer be valid when the user
    accesses the alert.


Backend Django API Documentation
================================

The backend API can be retrieved as follows.

.. code-block:: python

    from projectroles.plugins import get_backend_api
    app_alerts = get_backend_api('appalerts_backend')

Make sure to also enable ``appalerts_backend`` in the
``ENABLED_BACKEND_PLUGINS`` Django setting.

.. currentmodule:: appalerts.api

.. autoclass:: AppAlertAPI
    :members:
    :show-inheritance:
