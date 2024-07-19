.. _dev_backend_app:


Backend App Development
^^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for developing
**backend apps** to be used with the SODAR Core framework.

It is recommended to read :ref:`dev_project_app` before this document.


Backend App Basics
==================

Backend apps are intended to be used by other apps via their plugin without
requiring hard-coded imports. They may provide their own views for e.g. Ajax API
functionality, but mostly they're intended to be internal "helper" apps as the
name suggests.


Prerequisites
=============

See :ref:`dev_project_app`.


Models
======

No specific model implementation is required. However, it is strongly to refer
to objects using ``sodar_uuid`` fields instead of the database private key.


BackendAppPlugin
================

The plugin is detected and retrieved using a ``BackendAppPlugin``.

Declaring the Plugin
--------------------

Create a file ``plugins.py`` in your app's directory. In the file, declare a
``BackendAppPlugin`` class implementing
``projectroles.plugins.BackendPluginPoint``. Within the class, implement
member variables and functions as instructed in comments and docstrings.

.. code-block:: python

    from projectroles.plugins import BackendPluginPoint
    from .urls import urlpatterns

    class BackendAppPlugin(BackendPluginPoint):
        """Plugin for registering a backend app"""
        name = 'example_backend_app'
        title = 'Example Backend App'
        urls = urlpatterns
        # ...

The following variables and functions are **mandatory**:

``name``
    Plugin name. If only introducing a single plugin in your app, this should
    match the app name. For multiple plugins within a single app, additional
    plugins should start with the app name, e.g. ``yourapp_xxx``. This ensures
    the correct highlighting of active apps in the UI. Note that the name
    variables of plugins are expected to be unique, although not currently
    strictly enforced.
``title``
    Plugin title to be displayed in the UI. In the case of a backend plugin,
    this will be mostly visible in the :ref:`app_siteinfo` views.
``icon``
    Iconify collection and icon name (e.g. ``mdi:home``).
``description``
    Verbose description of the app.
``get_api()``
    Method for retrieving the API class for the backend. The user should
    implement this API class to be retrieved.

Implementing the following is **optional**:

``javascript_url``
    Path to on demand includeable Javascript file.
``css_url``
    Path to on demand includeable CSS file.
``info_settings``
    List of names for app-specific Django settings to be displayed for
    administrators in the siteinfo app.
``get_statistics()``
    Return statistics for the siteinfo app. See details in
    :ref:`the siteinfo documentation <app_siteinfo>`.
``get_object_link()``
    Return object link for a Timeline event. Expected to return a
    ``PluginObjectLink`` object or ``None``.
``get_extra_data_link()``
    Return extra data link for a Timeline event.

.. hint::

    If you want to define multiple plugins within a single app, see the
    :ref:`dev_resource_multi_plugin` documentation.


Using the Plugin
----------------

To retrieve the API for the plugin, use the
function ``projectroles.plugins.get_backend_api()`` as follows:

.. code-block:: python

    from projectroles.plugins import get_backend_api
    example_api = get_backend_api('example_backend_app')

    if example_api:     # Make sure the API is there, and only after that..
        pass            # ..do stuff with the API

Including Backend Javascript/CSS
--------------------------------

If you want Javascript or CSS files to be associated with your plugin you can
set the ``javascript_url`` or ``css_url`` variables to specify the path to your
file. Note that these should correspond to ``STATIC`` paths under your app
directory.

.. code-block:: python

    class BackendPlugin(BackendPluginPoint):

        name = 'example_backend_app'
        title = 'Example Backend App'
        javascript_url = 'example_backend_app/js/example.js'
        css_url = 'example_backend_app/css/example.css'

The ``get_backend_include`` template-tag will return a ``<script>`` or
``<link>`` html tag with your specific file path, to be used in a template of
your app making use of the backend plugin:

.. code-block:: django

    {% load projectroles_common_tags %}
    {% get_backend_include 'example_backend_app' 'js' as javascript_include_tag %}
    {{ javascript_include_tag|safe }}

    {% get_backend_include 'example_backend_app' 'css' as css_include_tag %}
    {{ css_include_tag|safe }}

This will result in the following HTML:

.. code-block:: html

    <script type="text/javascript" src="/static/example.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/example.css"/>

Be sure to use the backend plugin's name (not the title) as the key and filter
the result by ``safe``, so the tag won't be auto-escaped.
