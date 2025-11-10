.. _app_tokens_api_rest:


Tokens REST API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the HTTP REST API documentation for the ``tokens``
app. For general information on REST API usage in SODAR Core, see
:ref:`rest_api_overview`.


Tokens REST API Versioning
==========================

Media Type
    ``application/vnd.bihealth.sodar-core.tokens+json``
Current Version
    ``1.0``
Accepted Versions
    ``1.0``
Header Example
    ``Accept: application/vnd.bihealth.sodar-core.tokens+json; version=x.y``


Tokens REST API Views
=====================

.. currentmodule:: tokens.views_api

.. autoclass:: UserTokenCreateAPIView
