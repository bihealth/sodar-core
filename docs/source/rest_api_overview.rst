.. _rest_api_overview:

REST API Overview
^^^^^^^^^^^^^^^^^

This section contains general REST API information as well as app specific REST
API reference. Unless otherwise stated, general principles apply to all REST API
endpoints regardless of application.

For developing REST API views for your own SODAR Core based apps, see
:ref:`dev_project_app_rest_api`.

Model Access and Permissions
----------------------------

In SODAR Core REST API views, objects are accessed through their ``sodar_uuid``
field. In the API documentation, "UUID" stands for this field unless otherwise
noted. For most endpoints, you are expected to provide the UUID at the end of
the URL to specify the object you are trying to access. Examples:

- ``/project/api/retrieve/67eeba1e-3743-4b58-ad43-5f92e9faf426``
- ``/files/api/file/retrieve-update-destroy//bf5c9467-7e50-4087-8f90-699762f45150``

For permissions, the REST API uses the same rules which are in effect in the
SODAR Core GUI. That means you need to have appropriate project access for each
operation. Conversely, if you already have a certain level of access to a
project in the GUI, the same operations are available to you in the REST API
without the need to acquire extra permissions.

Authentication
--------------

The API supports authentication through Knox authentication tokens, as well as
logging in using your SODAR username and password. Tokens are the recommended
method for security purposes.

For token access, first retrieve your token using the :ref:`app_tokens`. Add
the token in the ``Authorization`` header of your HTTP request as follows:

.. code-block:: console

    Authorization: token 90c2483172515bc8f6d52fd608e5031db3fcdc06d5a83b24bec1688f39b72bcd


.. _rest_api_overview_version:

Versioning
----------

The SODAR Core REST API uses accept header versioning. While specifying the
desired API version in your HTTP requests is optional, it is
**strongly recommended**. This ensures you will get the appropriate return data
and avoid running into unexpected incompatibility issues.

Each application is expected to use its own media type and version numbering. To
enable versioning, add the ``Accept`` header to your request with the app's
respective media type and version number. Example for the projectroles API:

.. code-block:: console

    Accept: application/vnd.bihealth.sodar-core.projectroles+json; version=x.y

SODAR Core REST APIs **must** conform to semantic versioning. Breaking changes
require a major ``1.*`` update, while non-breaking new features can be tagged
with a minor ``*.1``. Patch updates should be reserved for bug fixes.

APIs should be kept backwards compatible as feasible, with support for previous
versions maintained and ensured in API view tests.

Removing support for old API versions should be done by announcing them as
deprecated in a major SODAR Core version ``*.1.*`` or greater (see
:ref:`SODAR Core Versioning <dev_core_guide_version>`), followed by removing
support in the next major version.

Return Data
-----------

The return data for each request will be a JSON document unless otherwise
specified.

If return data is not specified in the documentation of an API view, it will
return the appropriate HTTP status code along with an optional ``detail`` JSON
field upon a successfully processed request.

For creation views, the ``sodar_uuid`` of the created object is returned along
with other object fields.

Pagination
----------

List views support pagination unless otherwise specified. Pagination can be
enabled by providing the ``?page=x`` query string in the API request. This will
change the return data into a paginated format. Example:

.. code-block:: python

    {
        'count' 170,
        'next': 'api/url?page=3',
        'previous': 'api/url?page=1',
        'results': [
            # ...
        ]
    }
