.. _app_projectroles_api_rest:


Projectroles REST API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the HTTP REST API documentation for the ``projectroles``
app. The provided API endpoints allow project and role operations through
HTTP API calls in addition to the GUI.


API Usage
=========

General information on usage of the REST APIs in SODAR Core is detailed in this
section. These instructions also apply to REST APIs in any other application
within SODAR Core. They are recommended as guidelines for API development in
your SODAR Core based Django site.

Authentication
--------------

The API supports authentication through Knox authentication tokens as well as
logging in using your SODAR username and password. Tokens are the recommended
method for security purposes.

For token access, first retrieve your token using the :ref:`app_tokens`. Add
the token in the ``Authorization`` header of your HTTP request as follows:

.. code-block:: console

    Authorization: token 90c2483172515bc8f6d52fd608e5031db3fcdc06d5a83b24bec1688f39b72bcd

Versioning
----------

The SODAR Core REST API uses accept header versioning. While specifying the
desired API version in your HTTP requests is optional, it is
**strongly recommended**. This ensures you will get the appropriate return data
and avoid running into unexpected incompatibility issues.

From SODAR Core v1.0 onwards, each application is expected to use its own media
type and version numbering. To enable versioning, add the ``Accept`` header to
your request with the app's respective media type and version number. Example
for the projectroles API:

.. code-block:: console

    Accept: application/vnd.bihealth.sodar-core.projectroles+json; version=x.y

Model Access and Permissions
----------------------------

Objects in SODAR Core API views are accessed through their ``sodar_uuid`` field.
This is strongly recommended for views implemented in your Django site as well,
as using a field such as ``pk`` may reveal internal database details to users as
well as be incompatible if e.g. mirroring roles between multiple SODAR Core
sites.

In the remainder of this document and other REST API documentation, *"UUID"*
refers to the ``sodar_uuid`` field of each model unless otherwise noted.

For permissions the API uses the same rules which are in effect in the SODAR
Core GUI. That means you need to have appropriate project access for each
operation.

Project Type Restriction
------------------------

IF you want to explicitly restrict access for your API view to a specific
project type, you can set the ``project_type`` attribute of your class to either
``PROJECT_TYPE_PROJECT`` or ``PROJECT_TYPE_CATEGORY`` as defined in
``SODAR_CONSTANTS``. A request to the view using the wrong project type will
result in a ``403 Not Authorized`` response, with the reason displayed in the
``detail`` view.

This works with any API view using ``SODARAPIProjectPermission`` as its
permission class, which includes ``SODARAPIBaseProjectMixin`` and
``SODARAPIGenericProjectMixin``. An example is shown below.

.. code-block:: python

    from rest_framework.generics import RetrieveAPIView
    from projectroles.models import SODAR_CONSTANTS
    from projectroles.views_api import SODARAPIGenericProjectMixin

    class YourAPIView(SODARAPIGenericProjectMixin, RetrieveAPIView):
        # ...
        project_type = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

Return Data
-----------

The return data for each request will be a JSON document unless otherwise
specified.

If return data is not specified in the documentation of an API view, it will
return the appropriate HTTP status code along with an optional ``detail`` JSON
field upon a successfully processed request.

For creation views, the ``sodar_uuid`` of the created object is returned
along with other object fields.

Pagination
----------

From SODAR Core V1.0 onwards, list views support pagination unless otherwise
specified. Pagination can be enabled by providing the ``?page=x`` query string
in the API request. This will change the return data into a paginated format.
Example:

.. code-block:: python

    {
        'count' 170,
        'next': 'api/url?page=3',
        'previous': 'api/url?page=1',
        'results': [
            # ...
        ]
    }


Projectroles REST API Versioning
================================

Media Type
    ``application/vnd.bihealth.sodar-core.projectroles+json``
Current Version
    ``1.1``
Accepted Versions
    ``1.0``, ``1.1``
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
