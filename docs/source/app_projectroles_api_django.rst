.. _app_projectroles_api_django:


Projectroles Django API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the Django API documentation for the ``projectroles``
app. Included are functionalities and classes intended to be used by other
applications when building a SODAR Core based Django site.


.. _app_projectroles_api_django_ui:

Base UI View Classes
====================

Base mixins and classes for building UI views can be found in
``projectroles.views``.

.. currentmodule:: projectroles.views

.. autoclass:: LoginRequiredMixin
    :members:
    :show-inheritance:

.. autoclass:: LoggedInPermissionMixin
    :members:
    :show-inheritance:

.. autoclass:: ProjectAccessMixin
    :members:
    :show-inheritance:

.. autoclass:: ProjectPermissionMixin
    :members:
    :show-inheritance:

.. autoclass:: ProjectContextMixin
    :members:
    :show-inheritance:

.. autoclass:: PluginContextMixin
    :members:
    :show-inheritance:

.. autoclass:: InvalidFormMixin
    :members:
    :show-inheritance:


Plugins
=======

SODAR plugin point definitions and helper functions for plugin retrieval are
detailed in this section.

.. automodule:: projectroles.plugins
    :members:


Models
======

Projectroles models are used by other apps for project access and metadata
management as well as linking objects to projects.

.. automodule:: projectroles.models
    :members:


.. _app_projectroles_api_django_settings:

App Settings
============

Projectroles provides an API for getting or setting project and user specific
settings. The API can be invoked as follows:

.. code-block:: python

    from projectroles.app_settings import AppSettingAPI
    app_settings = AppSettingAPI()

.. autoclass:: projectroles.app_settings.AppSettingAPI
    :members:


.. _app_projectroles_api_django_tags:

Common Template Tags
====================

These tags can be included in templates with
``{% load projectroles_common_tags %}``.

.. automodule:: projectroles.templatetags.projectroles_common_tags
    :members:


Utilities
=========

General utility functions are stored in ``utils.py``.

.. automodule:: projectroles.utils
    :members:


.. _app_projectroles_api_django_ajax_common:

Common Use Ajax Views
=====================

Ajax views intended to be used in a SODAR Core based site are described here.

.. currentmodule:: projectroles.views_ajax

.. autoclass:: CurrentUserRetrieveAjaxView

.. autoclass:: SiteReadOnlySettingAjaxView

.. autoclass:: SidebarContentAjaxView

.. autoclass:: UserDropdownContentAjaxView



.. _app_projectroles_api_django_rest:

Base REST API View Classes
==========================

Base view classes and mixins for building REST APIs can be found in
``projectroles.views_api``.

.. currentmodule:: projectroles.views_api

Permissions
-----------

.. autoclass:: SODARAPIProjectPermission
    :members:
    :show-inheritance:

Base API View Mixins
--------------------

.. autoclass:: SODARAPIBaseProjectMixin
    :members:
    :show-inheritance:

.. autoclass:: APIProjectContextMixin
    :members:
    :show-inheritance:

.. autoclass:: SODARAPIGenericProjectMixin
    :members:
    :show-inheritance:

.. autoclass:: ProjectQuerysetMixin
    :members:

.. autoclass:: SODARPageNumberPagination
    :members:


.. _app_projectroles_api_django_ajax:

Base Ajax API View Classes
==========================

Base view classes and mixins for building Ajax API views can be found in
``projectroles.views_ajax``.

.. currentmodule:: projectroles.views_ajax

.. autoclass:: SODARBaseAjaxMixin
    :members:
    :show-inheritance:

.. autoclass:: SODARBaseAjaxView
    :members:
    :show-inheritance:

.. autoclass:: SODARBasePermissionAjaxView
    :members:
    :show-inheritance:

.. autoclass:: SODARBaseProjectAjaxView
    :members:
    :show-inheritance:


.. _app_projectroles_api_django_serial:

Base Serializers
================

Base serializers for SODAR Core compatible models are available in
``projectroles.serializers``.

.. currentmodule:: projectroles.serializers

.. autoclass:: SODARModelSerializer
    :members:
    :show-inheritance:

.. autoclass:: SODARProjectModelSerializer
    :members:
    :show-inheritance:

.. autoclass:: SODARNestedListSerializer
    :members:
    :show-inheritance:

.. autoclass:: SODARUserSerializer
    :members:
    :show-inheritance:
