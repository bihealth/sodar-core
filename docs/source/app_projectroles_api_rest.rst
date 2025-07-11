.. _app_projectroles_api_rest:


Projectroles REST API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the HTTP REST API documentation for the ``projectroles``
app. For general information on REST API usage in SODAR Core, see
:ref:`rest_api_overview`.


Projectroles REST API Versioning
================================

Media Type
    ``application/vnd.bihealth.sodar-core.projectroles+json``
Current Version
    ``2.0``
Accepted Versions
    ``1.0``, ``1.1``, ``2.0``
Header Example
    ``Accept: application/vnd.bihealth.sodar-core.projectroles+json; version=x.y``


Projectroles REST API Views
===========================

.. currentmodule:: projectroles.views_api

.. autoclass:: ProjectListAPIView

.. autoclass:: ProjectRetrieveAPIView

.. autoclass:: ProjectCreateAPIView

.. autoclass:: ProjectUpdateAPIView

.. autoclass:: ProjectDestroyAPIView

.. autoclass:: RoleAssignmentCreateAPIView

.. autoclass:: RoleAssignmentUpdateAPIView

.. autoclass:: RoleAssignmentDestroyAPIView

.. autoclass:: RoleAssignmentOwnerTransferAPIView

.. autoclass:: ProjectInviteListAPIView

.. autoclass:: ProjectInviteRetrieveAPIView

.. autoclass:: ProjectInviteCreateAPIView

.. autoclass:: ProjectInviteRevokeAPIView

.. autoclass:: ProjectInviteResendAPIView

.. autoclass:: ProjectSettingRetrieveAPIView

.. autoclass:: ProjectSettingSetAPIView

.. autoclass:: UserSettingRetrieveAPIView

.. autoclass:: UserSettingSetAPIView

.. autoclass:: UserListAPIView

.. autoclass:: UserRetrieveAPIView

.. autoclass:: CurrentUserRetrieveAPIView


Projectroles REST API Version Changes
=====================================

v2.0
----

- ``ProjectInviteListAPIView``
    * Replace ``issuer`` field user serializer with user UUID
- ``ProjectInviteRetrieveAPIView``
    * Add view
- ``ProjectRetrieveAPIView``
    * Replace ``roles`` field user serializer with user UUID
    * Replace ``public_guest_access`` field with ``public_access``
- ``ProjectCreateAPIView``
    * Replace ``public_guest_access`` field with ``public_access``
- ``ProjectUpdateAPIView``
    * Replace ``public_guest_access`` field with ``public_access``
- ``ProjectSettingRetrieveAPIView``
    * Replace ``user`` field user serializer with user UUID
- ``UserSettingRetrieveAPIView``
    * Replace ``user`` field user serializer with user UUID

v1.1
----

- ``ProjectDestroyAPIView``
    * Add view
- ``ProjectRetrieveAPIView``
    * Add ``children`` field
- ``RoleAssignmentOwnerTransferAPIView``
    * Allow empty value for ``old_owner_role``
- ``UserListAPIView``
    * Add ``include_system_users`` parameter
- ``UserRetrieveAPIView``
    * Add view
- ``CurrentUserRetrieveAPIView``
    * Add ``auth_type`` field
