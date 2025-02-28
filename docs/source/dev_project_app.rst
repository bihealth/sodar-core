.. _dev_project_app:

Project App Development
^^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for developing
**project apps** to be used with the SODAR Core framework. This also applies for
modifying existing Django apps into project apps.

.. hint::

   The package ``example_project_app`` in the projectroles repository provides
   a concrete minimal example of a working project app.


Project App Basics
==================

**Characteristics** of a project app:

- Provides a functionality related to a project.
- Is dynamically included in project views by projectroles using plugins.
- Uses the project-based role and access control provided by projectroles.
- Is (optionally) included in projectroles search.
- Provides a dynamically included element (e.g. content overview) for the
  project details page.
- Appears in the project menu sidebar in the default projectroles templates.
- Can be archived or unarchived to enable/disable read-only mode.

**Requirements** for setting up a project app:

- Implement project relations and SODAR UUIDs in the app's Django models.
- Use provided mixins, keyword arguments and conventions in views.
- Extend projectroles base templates in your templates.
- Implement specific templates for dynamic inclusion by Projectroles.
- Create ``plugins.py`` with a project app plugin implementation.
- Create ``rules.py`` with rules for access permissions.

Fulfilling these requirements is detailed further in this document.


Prerequisites
=============

This documentation assumes you have a Django site with the ``projectroles``
app set up, either started with
`sodar-django-site <https://github.com/bihealth/sodar-django-site>`_ or by
integrating SODAR Core on an existing site (see
:ref:`projectroles integration <app_projectroles_integration>`).
The instructions can be applied either to modify a previously existing app, or
to set up a fresh app generated in the standard way with
``./manage.py startapp``.

It is also assumed that apps are more or less created according to best
practices defined by `Two Scoops <https://www.twoscoopspress.com/>`_, with the
use of `Class-Based Views <https://docs.djangoproject.com/en/4.2/topics/class-based-views/>`_
being a requirement.


Models
======

In order to hook up your Django models into projects, there are two
requirements: implementing a **project foreign key** and a **UUID field**.

Project Foreign Key
-------------------

Add a ``ForeignKey`` field for the ``projectroles.models.Project`` model,
either called ``project`` or accessible with a ``get_project()`` function
implemented in your model.

If the project foreign key for your model is **not** ``project``, make sure to
define a ``get_project_filter_key()`` method. It should return the name of the
field to use as key for filtering your model by project.

.. note::

    If your app contains a complex model structure with e.g. nested models using
    foreign keys, it's not necessary to add this to all your models, just the
    topmost one(s) used e.g. in URL kwargs.

Model UUID Field
----------------

To provide a unique identifier for objects in the SODAR context, add a
``UUIDField`` with the name of ``sodar_uuid`` into your model.

.. note::

    SODAR Core links to objects in URLs, links and forms using UUIDs instead
    of database private keys. This is strongly recommended for all Django models
    in apps using the SODAR Core framework.

.. note::

    When updating an existing Django model with an existing database, the
    ``sodar_uuid`` field needs to be populated. See
    `instructions in Django documentation <https://docs.djangoproject.com/en/4.2/howto/writing-migrations/#migrations-that-add-unique-fields>`_
    on how to create the required migrations.

Model Example
-------------

Below is an example of a projectroles-compatible Django model:

.. code-block:: python

    import uuid
    from django.db import models
    from projectroles.models import Project

    class SomeModel(models.Model):
        some_field = models.CharField(
            help_text='Your own field'
        )
        project = models.ForeignKey(
            Project,
            related_name='some_objects',
            help_text='Project to which this object belongs',
        )
        sodar_uuid = models.UUIDField(
            default=uuid.uuid4,
            unique=True,
            help_text='SomeModel SODAR UUID',
        )

.. note::

    The ``related_name`` field is optional, but recommended as it provides an
    easy way to lookup objects of a certain type related to a project. For
    example the ``project`` foreign key in a model called ``Document`` could
    feature e.g. ``related_name='documents'``.


Rules File
==========

Create a file ``rules.py`` in your app's directory. You should declare at least
one basic permission for enabling a user to view the app data for the project.
This can be named e.g. ``{APP_NAME}.view_data``. Common predicates for the rules
file can be found in ``projectroles.rules``. They can be extended within your
app if needed.

.. code-block:: python

    import rules
    from projectroles import rules as pr_rules

    rules.add_perm(
        'example_project_app.view_data',
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
        | pr_rules.is_project_guest,
    )

.. hint::

    The ``rules.is_superuser`` predicate is often redundant, as permission
    checks are skipped for Django superusers. However, it can be handy if you
    e.g. want to define a rule allowing only superuser access for now, with the
    potential for adding other predicates later.

.. hint::

    For permissions dealing with modifying data, you are strongly recommend to
    use the ``can_modify_project_data`` predicate. For more information, see
    :ref:`dev_project_app_archive`.

.. hint::

    To support the site read-only mode introduced in SODAR Core v1.1, the rules
    for your app's views need to be implemented accordingly. A check for the
    read-only mode is contained in the ``can_modify_project_data()`` predicate.
    If your view already uses that predicate, no further steps are necessary.
    For site views, ``is_site_writable`` should be used. For more information,
    see :ref:`dev_resources_read_only`.


ProjectAppPlugin
================

Create a file ``plugins.py`` in your app's directory. In the file, declare a
``ProjectAppPlugin`` class implementing
``projectroles.plugins.ProjectAppPluginPoint``. Within the class, implement
member variables and functions as instructed in comments and docstrings.

.. code-block:: python

    from projectroles.plugins import ProjectAppPluginPoint
    from .urls import urlpatterns

    class ProjectAppPlugin(ProjectAppPluginPoint):
        """Plugin for registering app with Projectroles"""
        name = 'yourprojectapp'
        title = 'Your Project App'
        urls = urlpatterns
        # ...

The following variables and functions are **mandatory**:

``name``
    Plugin name. If only introducing a single plugin in your app, this should
    match the app name. For multiple plugins within a single app, additional
    plugins should start with the app name, e.g. ``yourapp_xxx``. This ensures
    the correct highlighting of active apps in the UI. Note that the name
    variables of plugins are expected to be unique, although not currently
    strictly enforced.
``title``
    Plugin title to be displayed in the UI.
``urls``
    URL patterns, usually imported from the app's ``urls.py`` file. For
    multiple plugins within the same app providing UI views, it is recommended
    to only provide the UI view URLs relevant to the plugin in question. This
    ensures the correct highlighting of active apps in the UI.
``icon``
    Iconify collection and icon name (e.g. ``mdi:home``).
``entry_point_url_id``
    View ID for the app entry point (**NOTE:** The view **must** take the
    project ``sodar_uuid`` as a kwarg named ``project``).
``description``
    Verbose description of the app.
``app_permission``
    Basic permission for viewing app data in the related project (see above).
``search_enable``
    Boolean for enabling/disabling app search.
``details_template``
    Path to template to be included in the project details page, usually
    called ``{APP_NAME}/_details_card.html``.
``details_title``
    Title string to be displayed in the project details page for the app details
    template.
``plugin_ordering``
    Number to define the ordering of the app on the project menu sidebar and the
    details page.

Implementing the following is **optional**:

``app_settings``
    Implement if project, user or project_user (Settings specific to a project
    and user) specific settings for the app are needed. See the plugin point
    definition for an example.
``search_types``
    Implement if searching the data of the app is enabled.
``search_template``
    Implement if searching the data of the app is enabled.
``project_list_columns``
    Optional custom columns do be shown in the project list. See the plugin
    point definition for an example.
``category_enable``
    Whether the app should also be made available for categories. Defaults to
    ``False`` and should only be overridden when required. For an example of a
    project app enabled in categories, see :ref:`Timeline <app_timeline>`.
``info_settings``
    List of names for app-specific Django settings to be displayed for
    administrators in the siteinfo app.
``get_object_link()``
    Return object link for a Timeline event. Expected to return a
    ``PluginObjectLink`` object or ``None``.
``get_extra_data_link()``
    Return extra data link for a Timeline event.
``search()``
    Function called when searching for data related to the app if search is
    enabled. Expected to return a list of ``PluginSearchResult`` objects.
``get_statistics()``
    Return statistics for the siteinfo app. See details in
    :ref:`the siteinfo documentation <app_siteinfo>`.
``get_project_list_value()``
    A function which **must** be implemented if ``project_list_columns`` are
    defined, to retrieve a column cell value for a specific project.
``handle_project_update()``
    A function for enabling carrying out specific tasks within your app when the
    project is updated in projectroles. This is a work-in-progress functionality
    to be expanded later.

Once you have implemented the ``rules.py`` and ``plugins.py`` files and added
the app and its URL patterns to the Django site configuration, you can create
the project app plugin in the Django database with the following command:

.. code-block:: console

    $ ./manage.py syncplugins

You should see the following output to ensure the plugin was successfully
registered:

.. code-block:: console

    Registering Plugin for {APP_NAME}.plugins.ProjectAppPlugin

For info on how to implement the specific required views/templates, see the rest
of this document.

.. hint::

    If you want to define multiple plugins within a single app, see the
    :ref:`dev_resource_multi_plugin` documentation.


Views
=====

Certain guidelines must be followed in developing Django web UI views for them
to be successfully used with projectroles.

URL Keyword Arguments
---------------------

In order to link a view to project and check user permissions using mixins,
the URL keyword arguments **must** include an argument which matches *one of
the following conditions*:

- Contains a kwarg ``project`` which corresponds to the ``sodar_uuid``
  member value of a ``projectroles.models.Project`` object
- Contains a kwarg corresponding to the ``sodar_uuid`` of another Django
  model, which must contain a member field ``project`` which is a foreign key
  for a ``Projectroles.models.Project`` object. The kwarg **must** be named
  after the Django model of the referred object (in lowercase).
- Same as above, but the Django model provides a
  ``get_project()`` function which returns a ``Projectroles.models.Project``
  object.
- Contains a kwarg corresponding to a model in another app. The app must be
  specified in the URL kwarg as ``app__model``.

Examples:

.. code-block:: python

   urlpatterns = [
       # Direct reference to the Project model
       url(
           regex=r'^(?P<project>[0-9a-f-]+)$',
           view=views.ProjectDetailView.as_view(),
           name='detail',
       ),
       # RoleAssignment model has a "project" member which is also OK
       url(
           regex=r'^members/update/(?P<roleassignment>[0-9a-f-]+)$',
           view=views.RoleAssignmentUpdateView.as_view(),
           name='role_update',
       ),
       # Reference to a model in another app
       url(
           regex=r'^example/path/(?P<filesfolders__folder>[0-9a-f-]+)$',
           view=views.ExampleView.as_view(),
           name='example_ext_model',
       ),
   ]

Path URL syntax from Django v2+ is also supported. Examples:

.. code-block:: python

    urlpatterns = [
        # Direct reference to the Project model
        path(
            route='path-url/<uuid:project>',
            view=views.ExampleView.as_view(),
            name='example_path_url',
        ),
        # Reference to a model in another app
        path(
            route='path-ext/<uuid:filesfolders__folder>',
            view=views.ExampleView.as_view(),
            name='example_path_ext',
        ),
    ]

Mixins
------

The ``projectroles.views`` module provides several useful mixins for augmenting
your view classes to add projectroles functionality. These can be found in the
``projectroles.views`` module.

The most commonly used mixins:

``LoginRequiredMixin``
    Override of the standard Django mixin which may also allow anonymous guests
    if so configured in SODAR Core. If you plan on supporting anonymous users on
    your site, you **must** use this mixing instead of the original one in
    Django.
``LoggedInPermissionMixin``
    Ensure correct redirection of users on no permissions. Can also be used to
    customize messages displayed to the user.
``ProjectPermissionMixin``
    Provides a ``Project`` object for permission checking based on URL kwargs.
``ProjectContextMixin``
    Provides a ``Project`` object into the view context  based on URL kwargs.

See ``example_project_app.views.ExampleView`` for an example.


Templates
=========

Template Structure
------------------

It is strongly recommended to extend ``projectroles/project_base.html`` in your
project app templates. Just start your template with the following line:

.. code-block:: django

    {% extends 'projectroles/project_base.html' %}

The following **template blocks** are available for overriding or extending when
applicable:

``title``
    Page title.
``css``
    Custom CSS (extend with ``{{ block.super }}``).
``projectroles_extend``
    Your app content goes here.
``javascript``
    Custom Javascript (extend with ``{{ block.super }}``).
``head_extend``
    Optional block if you need to include additional content inside the HTML
    ``<head>`` element.

Within the ``projectroles_extend`` block, it is recommended to use the
following ``div`` classes, both extending the Bootstrap 4 ``container-fluid``
class:

``sodar-subtitle-container``
    Container for the page title.
``sodar-content-container``
    Container for the actual content of your app.

If you do not want to include the project title header to your project
templates, you can replace the ``projectroles_extend`` block with a
``projectroles`` block.

.. warning::

    When customizing your templates, make sure you are not accidentally nesting
    built-in blocks within each other by e.g. placing the ``css`` block *inside*
    the ``projectroles`` or ``projectroles_extend`` block. Doing so may cause
    the page to render incorrectly or includes to fail.

Rules
-----

To control user access within a template with permissions introduced in
``rules.py``, do it as follows:

.. code-block:: django

    {% load rules %}
    {% has_perm 'app.do_something' request.user project as can_do_something %}

This checks if the current user from the HTTP request has permission for
``app.do_something`` in the current project retrieved from the page context.

Common Template Tags
--------------------

General purpose template tags are available in
``projectroles/templatetags/projectroles_common_tags.py``. Include them to your
template as follows:

.. code-block:: django

    {% load projectroles_common_tags %}

See the :ref:`template tag API documentation <app_projectroles_api_django_tags>`
for detailed instructions on using different tags in your templates.

Example
-------

Minimal example for a project app template:

.. code-block:: django

    {% extends 'projectroles/project_base.html' %}

    {% load projectroles_common_tags %}
    {% load rules %}

    {% block title %}
      Page Title
    {% endblock title %}

    {% block head_extend %}
      {# OPTIONAL: extra content under <head> goes here #}
    {% endblock head_extend %}

    {% block css %}
      {{ block.super }}
      {# OPTIONAL: Extend or override CSS here #}
    {% endblock css %}

    {% block projectroles_extend %}

      {# Page subtitle #}
      <div class="container-fluid sodar-subtitle-container">
        <h3>
          <i class="iconify" data-icon="mdi:rocket-launch"></i>
          App and/or Page Title
        </h3>
      </div>

      {# App content #}
      <div class="container-fluid sodar-page-container">
        <p>Your app content goes here!</p>
      </div>

    {% endblock projectroles_extend %}

    {% block javascript %}
      {{ block.super }}
      {# OPTIONAL: include additional Javascript here #}
    {% endblock javascript %}

See ``example_project_app/example.html`` for a working and fully commented
example of a minimal template.

.. hint::

    If you include some controls on your ``sodar-subtitle-container`` class and
    want it to remain sticky on top of the page while scrolling, use ``row``
    instead of ``container-fluid`` and add the ``bg-white sticky-top`` classes
    to the element.


General Guidelines for Views and Templates
==========================================

General guidelines and hints for developing views and templates are discussed
in this section.

Referring to Project Type
-------------------------

SODAR Core allows customizing the display name for the project type from the
default "project" or "category". For more information, see
:ref:`app_projectroles_custom`.

It is thus recommended that instead of hard coding "project" or "category" in
your views or templates, use the ``get_display_name()`` function to refer to
project type.

In templates, this can be achieved with a custom template tag. Example:

.. code-block:: django

    {% load projectroles_common_tags %}
    {% get_display_name project.type title=True plural=False %}

In views and other Python code, the similar function can be accessed through
``utils.py``:

.. code-block:: python

    from projectroles.utils import get_display_name
    display_name = get_display_name(project.type, plural=False)

.. hint::

    If not dealing with a ``Project`` object, you can provide the
    ``PROJECT_TYPE_*`` constant from ``SODAR_CONSTANTS``. In templates, it's
    most straightforward to use "CATEGORY" and "PROJECT".


Specific Views and Templates
============================

A few specific views/templates are expected to be implemented.

App Entry Point
---------------

As described in the Plugins chapter, an app entry point view is to be defined
in the ``ProjectAppPlugin``. This is **mandatory**.

The view **must** take a ``project`` URL kwarg which corresponds to a
``Project.sodar_uuid``.

For an example, see ``example_project_app.views.ExampleView`` and the associated
template.

Project Details Element
-----------------------

A sub-template to be included in the project details page (the project's "front
page" provided by projectroles, where e.g. overview of app content is shown).

Traditionally these files are called ``_details_card.html``, but you can name
them as you wish and point to the related template in the ``details_template``
variable of your plugin.

It is expected to have the content in a ``card-body`` container:

.. code-block:: django

   <div class="card-body">
     {# Content goes here #}
   </div>


Project Search API and Template
===============================

If you want to implement search in your project app, you need to implement the
``search()`` method in your plugin, as well as a template for displaying the
results.

.. hint::

   Implementing search *can* be complex. If you have access to the main SODAR
   repository, apps in that project might prove useful examples.

The search() Function
---------------------

See the signature of ``search()`` in
``projectroles.plugins.ProjectAppPluginPoint``. The arguments are as follows:

``search_terms``
    - One or more terms to be searched for (list of strings). Expected to be
      combined with OR operators in your search logic.
    - Multiple search terms or phrases containing whitespaces can be provided
      via the Advanced Search view.
``user``
    - User object for user initiating search.
``search_type``
    - The type of object to search for (string, optional).
    - Used to restrict search to specific types of objects.
    - You can specify supported types in the plugin's ``search_types`` list.
    - Examples: ``file``, ``sample``..
``keywords``
    - Special search keywords, e.g. "exact".
    - **NOTE:** Currently not implemented.

.. note::

   Within this method, you are expected to verify appropriate access of the
   searching user yourself!

The return data is a list of one or more ``PluginSearchResult`` objects. The
objects are expected to be split between search categories, of which there can
be one or multiple. This is useful where e.g. the same type of HTML list isn't
suitable for all returnable types. If only returning one type of data, you can
use e.g. ``all`` as your only category. Example of a return data:

.. code-block:: python

    from projectroles.plugins import PluginSearchResult
    # ...
    return [
        PluginSearchResult(
            category='all',  # Category ID to be used in your search template
            title='List title',  # Title of the result set
            search_types=[],  # Object types included in this category
            items=[],  # List or QuerySet of objects returned by search
        )
    ]

.. warning::

    The earlier search implementation expected a ``dict`` as return data. This
    has been deprecated and support for it will be removed in SODAR Core v1.1.


Search Template
---------------

Projectroles will provide your template context the ``search_results`` object,
which corresponds to the result dict of the aforementioned function. There are
also includes for formatting the results list, which you are encouraged to use.

Example of a simple results template, in case of a single ``all`` category:

.. code-block:: django

   {% if search_results.all.items|length > 0 %}

     {# Include standard search list header here #}
     {% include 'projectroles/_search_header.html' with search_title=search_results.all.title result_count=search_results.all.items|length %}

     {# Set up a table with your results #}
     <table class="table table-striped sodar-card-table sodar-search-table" id="sodar-ff-search-table">
       <thead>
         <tr>
           <th>Name</th>
           <th>Some Other Field</th>
         </tr>
      </thead>
      <tbody>
        {% for item in search_results.all.items %}
          <tr>
            <td>
              <a href="#link_to_somewhere_in your_app">{{ item.name }}</a>
            </td>
            <td>
              {{ item.some_other_field }}
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {# Include standard search list footer here #}
    {% include 'projectroles/_search_footer.html' %}

  {% endif %}


API Views
=========

API view usage in project apps is detailed in this section.

.. _dev_project_app_rest_api:

Rest API Views
--------------

To set up REST API views for project apps, it is recommended to use the base
SODAR API view classes and mixins found in ``projectroles.views_api``. These
set up the recommended authentication methods, versioning through accept headers
and project-based permission checks.

By default, the REST API views built on SODAR Core base classes support two
methods of authentication: Knox tokens and Django session auth. These can of
course be modified by overriding/extending the base classes.

For versioning we strongly recommend using accept header versioning, which is
what is supported by the SODAR Core base classes. From SODAR Core v1.0 onwards,
each app is expected to use its own media type and API versioning, preferably
based on semantic versioning. For this, you should supply your own versioning
mixin to be used in your views. Example:

.. code-block:: python

    from rest_framework.renderers import JSONRenderer
    from rest_framework.versioning import AcceptHeaderVersioning
    from rest_framework.views import APIView
    from projectroles.views_api import SODARAPIGenericProjectMixin

    YOURAPP_API_MEDIA_TYPE = application/vnd.yourorg.yoursite.yourapp+json
    YOURAPP_API_DEFAULT_VERSION = '1.0'
    YOURAPP_API_ALLOWED_VERSIONS = ['1.0']

    class YourAPIVersioningMixin:

        class YourAPIRenderer(JSONRenderer):
            media_type = YOURAPP_API_MEDIA_TYPE

        class YourAPIVersioning(AcceptHeaderVersioning):
            allowed_versions = YOURAPP_API_ALLOWED_VERSIONS
            default_version = YOURAPP_API_DEFAULT_VERSION

        render_classes = [YourAPIRenderer]
        versioning_class = YourAPIVersioning

    class YourAPIView(YourAPIVersioningMixin, SODARAPIGenericProjectMixin, APIView):
        # ...

The base classes provide permission checks via SODAR Core project objects
similar to UI view mixins. Base REST API classes without a project context can
also be used in site apps.

See the
:ref:`base REST API class documentation <app_projectroles_api_django_rest>` for
details on the base REST API classes.

An example "hello world" REST API view for SODAR apps is available in
``example_project_app.views.HelloExampleProjectAPIView``.

.. note::

    Internal SODAR Core REST API views, specifically ones used in apps provided
    by the django-sodar-core package, use different media types and versioning
    from views to be implemented on your site. From SODAR Core v1.0 onwards,
    each app is expected to provide their own versioning.

Ajax API Views
--------------

To set up Ajax API views for the UI, it is recommended to use the base Ajax
view classes found in ``projectroles.views_ajax``. These views only support
Django session authentication by default, so Knox token authentication will not
work. Versioning is omitted. Base views without project permission checks can
also be used in site apps.

If you want to enable anonymous access to an Ajax API view when
``PROJECTROLES_ALLOW_ANONYMOUS`` is enabled in your site's Django settings, you
can use the ``allow_anonymous`` property of the view.

See the
:ref:`base AJAX API view documentation <app_projectroles_api_django_ajax>` for
more information on using these base classes.

Example:

.. code-block:: python

    from projectroles.views_ajax import SODARBaseProjectAjaxView

    class ExampleAjaxAPIView(SODARBaseProjectAjaxView):

    permission_required = 'projectroles.view_project'

    def get(self, request):
        # ...

If you want to wrap a REST API view into an Ajax API view, you can use
``SODARBaseAjaxMixin`` and your original view as base to ensure appropriate
access control.

Serializers
-----------

Base serializers for SODAR Core based API views are available in
``projectroles.serializers``. They provide ``Project`` context where needed, as
well as setting default fields such as ``sodar_uuid`` which should be always
used in place of ``pk``.

See the :ref:`serializer API documentation <app_projectroles_api_django_serial>`
for details on using base serializer classes.


.. _dev_project_app_archive:

Project Archiving
=================

Projects can be set to *archived* mode. If a project is archived, it is expected
for apps to disable their data modifying functionality and prevent access to
views used to alter app data. There may of course be some exceptions in your use
case.

For most cases, your app should already be controlling user access to data
modifying views and UI elements by checking permissions set in the ``rules.py``
module within the app. In these cases, you can simply add the
``can_modify_project_data`` predicate into any permission dealing with modifying
project app data. An example from the filesfolders app:

.. code-block:: python

    from projectroles import rules as pr_rules  # To access common predicates

    # Allow adding data to project
    rules.add_perm(
        'filesfolders.add_data',
        pr_rules.can_modify_project_data
        & (
            pr_rules.is_project_owner
            | pr_rules.is_project_delegate
            | pr_rules.is_project_contributor
        ),
    )

In cases not covered by the permissions, you can check a project's archive
status via the ``Project.archive`` field.

For an example how to implement and test archiving support in your project app,
see the code and unit tests in :ref:`app_filesfolders`.

The archiving and unarchiving functionality will also call
``ProjectModifyPluginMixin.perform_project_archive()`` and its corresponding
revert method when the archival status for a project is changed. If your site
e.g. manages data in an external database, you may implement these methods for
additional actions to be taken.

.. note::

    In the current implementation, categories can not be archived. This may be
    implemented later.

.. note::

    The usage of backend apps like sodarcache and timeline are not limited by
    the project archive status, your app logic should handle it instead.


.. _dev_project_app_delete:

Project Deletion
================

If your apps only save data in Django models containing a ``Project`` foreign
key with cascading deletion, no extra steps are needed to support project
deletion.

If your app contains project-specific data which is e.g. stored in an external
system or in ways which will not be cascade-deleted along with the Django
``Project`` model object, you need to implement project deletion in the project
modify API. To do this, inherit ``ProjectModifyPluginMixin`` in your app's
plugin and implement the ``perform_project_delete()`` method to clean up data.

Project deletion can not be undone, so there is no revert method available for
this action.

.. note::

    While categories are not expected to store data, the project deletion API
    method is called for the deletion of both categories or projects, in case
    speficic logic is needed for both project types.


Removing a Project App
======================

Removing a project app from your Django site can be slightly more complicated
than removing a normal non-SODAR-supporting Django application. Following the
procedure detailed here you are able to cleanly remove a project app which has
been in use on your site.

The instructions apply to project apps you have created yourself as well as
project apps included in the django-sodar-core package, with the exception of
``projectroles`` which can not be removed from a SODAR based site.

.. warning::

    Make sure to perform these steps **in the order they are presented here**.
    Otherwise you may risk serious problems with your site functionality or your
    database!

.. note::

    Just in case, it is recommended to make a backup of your Django database
    before proceeding.

First you should delete all Timeline references to objects in your app. This is
not done automatically as, by design, the references are kept even after the
original objects are deleted. Go to the Django shell via management command
using ``shell`` or ``shell_plus`` and enter the following. Replace ``app_name``
with the name of your application as specified in its ``ProjectAppPlugin``.

.. code-block:: python

    from timeline.models import TimelineEvent
    TimelineEvent.objects.filter(app='app_name').delete()

Next you should delete existing database objects defined by the models in your
app. This is also most easily done via the Django shell. Example:

.. code-block:: python

    from yourapp.models import YourModel
    YourModel.objects.all().delete()

After the objects have been deleted, reset the database migrations of your
application.

.. code-block:: console

    $ ./manage.py migrate yourapp zero

Once this has been executed successfully, you should delete the plugin object
for your application. Returning to the Django shell, type the following:

.. code-block:: python

    from djangoplugins.models import Plugin
    Plugin.objects.get(name='app_name').delete()

Finally, you should remove the references to the removed app in the Django
configuration.

App dependency in ``config/settings/base.py``:

.. code-block:: python

    LOCAL_APPS = [
    # The app you are removing
    'yourapp.apps.YourAppConfig',
    # ...
    ]

App URL patterns in ``config/urls.py``:

.. code-block:: python

    urlpatterns = [
        # Your app's URLs
        url(r'^yourapp/', include('yourapp.urls')),
        # ...
    ]

Once you have performed the aforementioned database operations and deployed a
version of your Django site with the application dependency and URL patterns
removed, the project app should be cleanly removed from your site.
