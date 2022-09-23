.. _app_timeline_api_django:


Timeline Django API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains Django API documentation for the ``timeline`` app.
Included are functionalities and classes intended to be used by other
applications.


Backend API
===========

The backend API can be retrieved as follows.

.. code-block:: python

    from projectroles.plugins import get_backend_api
    app_alerts = get_backend_api('timeline_backend')

Make sure to also enable ``timeline_backend`` in the ``ENABLED_BACKEND_PLUGINS``
Django setting.

.. autoclass:: timeline.api.TimelineAPI
    :members:

Models
======

.. automodule:: timeline.models
    :members:
