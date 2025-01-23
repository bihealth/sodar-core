.. _app_sodarcache_api_rest:


Sodarcache REST API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the HTTP REST API documentation for the ``sodarcache``
app.


Sodarcache REST API Versioning
==============================

Media Type
    ``application/vnd.bihealth.sodar-core.sodarcache+json``
Current Version
    ``2.0``
Accepted Versions
    ``2.0``
Header Example
    ``Accept: application/vnd.bihealth.sodar-core.sodarcache+json; version=x.y``


Sodarcache REST API Views
=========================

.. currentmodule:: sodarcache.views_api

.. autoclass:: CacheItemRetrieveAPIView

.. autoclass:: CacheItemDateRetrieveAPIView

.. autoclass:: CacheItemSetAPIView


Sodarcache REST API Version Changes
===================================

v2.0
----

- ``CacheItemRetrieveAPIView``
    * Return ``user`` as UUID instead of ``SODARUserSerializer`` dict
