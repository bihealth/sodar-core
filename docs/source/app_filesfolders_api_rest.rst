.. _app_filesfolders_api_rest:


Filesfolders REST API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the HTTP REST API documentation for the ``filesfolders``
app. The provided API endpoints allow file operations through HTTP API calls in
addition to the GUI.

For general information on REST API usage in SODAR Core, see
:ref:`app_projectroles_api_rest`.


Filesfolders REST API Versioning
================================

Media Type
    ``application/vnd.bihealth.sodar-core.filesfolders+json``
Current Version
    ``1.0``
Accepted Versions
    ``1.0``
Header Example
    ``Accept: application/vnd.bihealth.sodar-core.filesfolders+json; version=x.y``


Filesfolders REST API Views
===========================

.. currentmodule:: filesfolders.views_api

.. autoclass:: FolderListCreateAPIView

.. autoclass:: FolderRetrieveUpdateDestroyAPIView

.. autoclass:: FileListCreateAPIView

.. autoclass:: FileRetrieveUpdateDestroyAPIView

.. autoclass:: FileServeAPIView

.. autoclass:: HyperLinkListCreateAPIView

.. autoclass:: HyperLinkRetrieveUpdateDestroyAPIView


Filesfolders REST API Version Changes
=====================================

v2.0
----

- All views
    * Return ``owner`` as UUID instead of ``SODARUserSerializer`` dict
