.. _app_timeline_api_rest:


Timeline REST API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the HTTP REST API documentation for the ``timeline``
app. For general information on REST API usage in SODAR Core, see
:ref:`rest_api_overview`.


Timeline REST API Versioning
============================

Media Type
    ``application/vnd.bihealth.sodar-core.timeline+json``
Current Version
    ``1.0``
Accepted Versions
    ``1.0``
Header Example
    ``Accept: application/vnd.bihealth.sodar-core.timeline+json; version=x.y``


Timeline REST API Views
=======================

.. currentmodule:: timeline.views_api

.. autoclass:: ProjectTimelineEventListAPIView

.. autoclass:: SiteTimelineEventListAPIView

.. autoclass:: TimelineEventRetrieveAPIView


Timeline REST API Version Changes
=================================

v2.0
----

- ``TimelineEventRetrieveAPIView``
    * Return ``user`` as UUID instead of ``SODARUserSerializer`` dict
