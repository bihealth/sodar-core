.. _app_sodarcache_api_django:


Sodarcache Django API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains Django API documentation for the backend plugin in the
``sodarcache`` app. Included are functionalities and classes intended to be used
by other applications.


Backend API
===========

The backend API can be retrieved as follows.

.. code-block:: python

    from projectroles.plugins import get_backend_api
    app_alerts = get_backend_api('sodar_cache')

Make sure to also enable ``sodar_cache`` in the ``ENABLED_BACKEND_PLUGINS``
Django setting.

.. autoclass:: sodarcache.api.SodarCacheAPI
    :members:


Models
======

.. automodule:: sodarcache.models
    :members:
