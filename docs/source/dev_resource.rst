.. _dev_resource:

General Resources
^^^^^^^^^^^^^^^^^

Via the projectroles app, SODAR Core provides optional features, APIs and
templates for common functionality and layout regardless of the app type. These
resources are described in this document.


Icons
=====

To use icons in your apps, use the ``iconify`` class along with the collection
and icon name into the ``data-icon`` attribute. See
`Iconify <https://docs.iconify.design/implementations/css.html>`_ and
`django-iconify <https://edugit.org/AlekSIS/libs/django-iconify/-/blob/master/README.rst>`_
documentation for further information.

Example:

.. code-block:: html

    <i class="iconify" data-icon="mdi:home"></i>

Also make sure to modify the ``icon`` attribute of your app plugins to include
the full ``collection:name`` syntax for Iconify icons.

In certain client side Javascript implementations in which icons are loaded or
replaced dynamically, you may have to refer to these URLs as a direct ``img``
element:

.. code-block:: html

    <img src="/icons/mdi/home.svg" />

For modifiers such as color and size when using ``img`` tags,
`see here <https://docs.iconify.design/implementations/css.html>`_.

SODAR Core uses the `Material Design Icons <https://materialdesignicons.com/>`_
collection for its own apps. You can also use additional collections supported
by Iconify on your site by retrieving them with the ``geticons`` management
command. Multiple collections can be downloaded with a single command, as seen
in the example below. Make sure to run ``collectstatic`` after this command.

.. code-block:: console

    $ ./manage.py geticons -c collection1 collection2
    $ ./manage.py collectstatic


Forms
=====

This section contains guidelines for implementing forms.

Form Base Classes
-----------------

Although not required, it is recommended to use common SODAR Core base classes
with built-in helpers for your Django forms. ``SODARForm`` and
``SODARModelForm`` extend Django's ``Form`` and ``ModelForm`` respectively.
These base classes can be imported from ``projectroles.forms``. Currently they
add logging to ``add_error()`` calls, which helps administrators track form
issues encountered by users. Further improvements are to be added in the future.

SODAR User Selection Field
--------------------------

Projectroles offers a custom field, widget and accompanying Ajax API views
for autocomplete-enabled selection of SODAR users in Django forms. The field
will handle providing appropriate choices according to the view context and user
permissions, also allowing for customization.

The recommended way to use the built-in user form field is by using the
``SODARUserChoiceField`` class found in ``projectroles.forms``. The field
extends Django's ``ModelChoiceField`` and takes most of the same keyword
arguments in its init function, with the exception of ``queryset``,
``to_field_name``, ``limit_choices_to`` and ``widget`` which will be overridden.

The init function also takes new arguments which are specified below:

``scope``
    Scope of users to include (string). Options:

    - ``all``: All users on the site
    - ``project``: Limit search to users in given project
    - ``project_exclude`` Exclude existing users of given project
``project``
    Project object or project UUID string (optional)
``exclude``
    List of User objects or User UUIDs to exclude (optional)
``forward``
    Parameters to forward to autocomplete view (optional)
``url``
    Autocomplete ajax class override (optional)
``widget_class``
    Widget class override (optional)

Below is an example of the classes usage. Note that you can also define the
field as a form class member, but the ``project`` or ``exclude`` values are
not definable at that point. The following example assumes you are setting up
your project app form with an extra ``project`` argument.

.. code-block:: python

    from projectroles.forms import SODARUserChoiceField

    class YourForm(forms.ModelForm):
        class Meta:
            # ...
        def __init__(self, project, *args, **kwargs):
            # ...
            self.fields['user'] = SODARUserChoiceField(
                label='User',
                help_text='Select user for your thing here',
                required=True,
                scope='project',
                project=project,
                exclude=[unwanted_user]
            )

For more examples of usage of this field and its widget, see
``projectroles.forms``. If the field class does not suit your needs, you can also
retrieve the related widget to your own field with
``projectroles.forms.get_user_widget()``.

To provide required Javascript and CSS includes for DAL in your form, make sure
to include ``form.media`` in your template. Example:

.. code-block:: django

    <div class="container-fluid sodar-page-container">
      <form method="post">
        {{ form.media }}
        {{ form | crispy }}
        {% ... %}
      </form>
    </div>

If using customized Javascript for your widget, the corresponding JS file can be
provided in the ``javascript`` block. See the ``django-autocomplete-light``
documentation for more information on how to customize your widget.

Markdown
--------

For fields supporting Markdown, it is recommended to use the
``SODARPagedownWidget`` found in ``projectroles.models``.

.. hint::

    When rendering Markdown fields in templates, add the
    ``sodar-markdown-content`` CSS class to the field's parent container for
    improved Markdown styling.

Submit Multi-Click Protection
-----------------------------

To avoid unwanted effects from a user clicking the submit button on a form
multiple times, it is recommended to use the ``sodar-btn-submit-once`` class on
the submit button in your server-side form templates. Introducing this class
will disable the button after the initial click while the form is submitted.
This is especially recommended for forms responsible for creating objects.

Invalid Form View Mixin
-----------------------

Adding ``projectroles.views.InvalidFormMixin`` to your create or update view
displays a standardized Django message notifying the user of form submission
failure. This is recommended to be used especially for long scrolling forms,
where errors pinned to specific fields may be initially invisible to the user.


Template Includes and Helpers
=============================

This section details general template includes and helpers provided by SODAR
Core. Unless otherwise mentioned, these can be imported from the projectroles
app.

For common template tags, see :ref:`app_projectroles_api_django_tags`.

Pagination Template
-------------------

A common template for adding navigation for list pagination can be found in
``projectroles/_pagination.html``. This can be included to any Django
``ListView`` template which provides the ``paginate_by`` definition, enabling
pagination. If a smaller layout is desired, the ``pg_small`` argument can be
used. An example can be seen below:

.. code-block:: django

    {% include 'projectroles/_pagination.html' with pg_small=True %}

Project Badge
-------------

Projectroles provides a project badge which can be used to display a fixed-size
link to a category or a project among text. It can be included in your template
as follows:

.. code-block:: django

    {% include 'projectroles/_project_badge.html' with project=project color='info' can_view=True %}

The following arguments are expected:

``project``
    Project object for the related project or category.
``color``
    String for the badge color (must correspond to bootstrap classes, e.g.
    "info" or "success").
``can_view``
    Boolean for whether the current user should have access to view the project.

Tour Help
---------

SODAR Core uses `Shepherd <https://shipshapecode.github.io/shepherd/docs/welcome/>`_
to present an optional interactive tour for a rendered page. To enable the tour
in your template, set it up inside the ``javascript`` template block. Within an
inline javascript structure, set the ``tourEnabled`` variable to ``true`` and
add steps according to the
`Shepherd documentation <https://shipshapecode.github.io/shepherd>`_.

Example:

.. code-block:: django

    {% block javascript %}
      {{ block.super }}
      {# Tour content #}
      <script type="text/javascript">
        tourEnabled = true;
        /* Normal step */
        tour.addStep('id_of_step', {
            title: 'Step Title',
            text: 'Description of the step',
            attachTo: '#some-element top',
            advanceOn: '.docs-link click',
            showCancelLink: true
        });
        /* Conditional step */
        if ($('.potentially-existing-element').length) {
            tour.addStep('id_of_another_step', {
                title: 'Another Title',
                text: 'Another description here',
                attachTo: '.potentially-existing-element right',
                advanceOn: '.docs-link click',
                showCancelLink: true
            });
        }
      </script>
    {% endblock javascript %}


.. warning::

    Make sure you call ``{{ block.super }}`` at the start of the declared
    ``javascript`` block or you will overwrite the site's default Javascript
    setup!


.. _dev_resource_app_settings:

App Settings
============

SODAR Core offers a common framework and API for defining, setting and accessing
modifiable settings from your apps. This makes it possible to introduce
variables changeable in runtime for different purposes and scopes without the
need to manage additional Django models in your apps. App settings are supported
for plugins in project and site apps.

The settings are defined as a list of ``PluginAppSettingDef`` objects in your
project or site app plugin. An example of a definition can be seen below:

.. code-block:: python

    from projectroles.models import SODAR_CONSTANTS
    from projectroles.plugins import ProjectAppPluginPoint, PluginAppSettingDef

    class ProjectAppPlugin(ProjectAppPluginPoint):
        # ...
        app_settings = [
            PluginAppSettingDef(
                name='allow_public_links',
                scope=SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
                type=SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN'],
                default=False,
                label='Allow public links',
                description='Allow generation of public links for files',
            )
        }

The mandatory and optional attributes for an app setting definition are as
follows:

``name``
    Name for the setting. Preferably something short and clear to call in code.
    Name must be unique within the settings of each plugin.
``scope``
    Scope of the setting, which determines whether the setting is unique per
    project, user, project and user, or site. Must correspond to one of
    ``APP_SETTING_SCOPE_*`` in ``SODAR_CONSTANTS``, see below for details
    (string)
``type``
    Setting type, must correspond to one of ``APP_SETTING_TYPE_*`` in
    ``SODAR_CONSTANTS``. Available options are ``APP_SETTING_TYPE_BOOLEAN``,
    ``APP_SETTING_TYPE_INTEGER``, ``APP_SETTING_TYPE_STRING`` and
    ``APP_SETTING_TYPE_JSON``.
``default``
    Default value for the setting. This is returned if no value has been set.
    Can alternatively be a callable with the signature
    ``callable(project=None, user=None)``.
``label``
    Label to be displayed in forms for ``PROJECT`` and ``USER`` scope settings
    (string, optional).
``placeholder``
    Placeholder string to be displayed in forms for ``PROJECT`` and ``USER``
    scope settings (optional).
``description``
    Description string shown in forms for ``PROJECT`` and ``USER`` scope
    settings (string, optional).
``options``
    List of selectable options for ``INTEGER`` and ``STRING`` type settings. Can
    alternatively be a callable with the signature
    ``callable(project=None, user=None)`` returning a list of strings or
    key/label tuples (optional).
``user_modifiable``
    Boolean value for whether this setting should be displayed in project or
    user forms. If false, will be displayed only to superusers. Set to true if
    your app is expected to manage this setting. Applicable for ``PROJECT`` and
    ``USER`` scope settings (optional).
``global_edit``
    Allowing/disallow editing the setting on target sites for remote projects.
    Relevant to ``SOURCE`` sites. If set ``True``, the value can not be edited
    on target sites, the default value being ``False`` (boolean, optional).
``project_types``
    Project types for which this setting is allowed to be set. Defaults to
    ``[PROJECT_TYPE_PROJECT]`` (list of strings, optional).
``widget_attrs``
    Form widget attributes (optional, dict)

Available project scopes for the ``scope`` attribute:

``APP_SETTING_SCOPE_PROJECT``
    Setting related to a project and displayed in the project create/update
    form.
``APP_SETTING_SCOPE_USER``
    Site-wide setting related to a user and displayed in the user profile form.
``APP_SETTING_SCOPE_PROJECT_USER``
    User setting related to a project, managed by your project app.
``APP_SETTING_SCOPE_SITE``
    Site-wide setting similar to Django settings but modifiable in runtime.

The settings are retrieved using ``AppSettingAPI`` provided by the
projectroles app. Below is an example of invoking the API. For the full API
docs, see
:ref:`app settings API documentation <app_projectroles_api_django_settings>`.

.. code-block:: python

    from projectroles.app_settings import AppSettingAPI
    app_settings = AppSettingAPI()
    app_settings.get('plugin_name', 'setting_name', project_object)  # Etc..

There is no need to separately generate settings for projects or users. If the
setting object does not exist in the Django database when
``AppSettingAPI.get()`` is first called on the setting and argument combination,
it is created based on the default value and the default value is returned.

If you modify definitions during development or retire a setting, run the
``cleanappsettings`` management command to delete unneeded app settings from
the Django database:

.. code-block:: console

    $ ./manage.py cleanappsettings

.. hint::

    If you want to ensure desired effects for cleanup when developing, run the
    command with the ``-c`` or ``--check`` argument. This will log changes to be
    made without actually altering the database.


Project Modifying API
=====================

If your site needs to perform specific actions when projects are created or
modified, or when project membership is altered, you can implement the project
modifying API in your app plugin. This can be useful if your site e.g. maintains
project data and access in other external databases or needs to set up some
specific data on project changes.

.. note::

    This API is intended for special cases. If you're unsure why you wouldn't
    need it on your site, it is possible you don't. Using it unnecessarily might
    complicate your site implementation.

This API works for :ref:`project apps <dev_project_app>` and
:ref:`backend apps <dev_backend_app>`. To use it, it is recommend to include the
``ProjectModifyPluginMixin`` in your plugin class and implement the methods
relevant to your site's needs. An example of this can be seen below.

.. code-block:: python

    from projectroles.plugins import ProjectModifyPluginMixin

    class ProjectAppPlugin(ProjectModifyPluginMixin, ProjectAppPluginPoint):
        # ...
        def perform_project_modify(
            self,
            project,
            action,
            project_settings,
            old_data=None,
            old_settings=None,
            request=None,
        ):
            pass  # Your implementation goes here

You will also need to set ``PROJECTROLES_ENABLE_MODIFY_API=True`` in your site's
Django settings to enable calling this API.

Project modification operations will be cancelled and reverted if errors are
encountered at any point in the project modify API calls. If your site has
multiple apps implementing this API, you should also implement reversion methods
for each operations to assert a clean rollback. These methods are also included
in the class.

You can control the order of the apps in which this API is called by listing
your plugins in the ``PROJECTROLES_MODIFY_API_APPS`` Django setting. This will
also affect the order of reversing.

To synchronize data for existing projects in development, you can implement the
``perform_project_sync()`` method.


.. _dev_resource_multi_plugin:

Multi-Plugin Apps
=================

In many cases, you may want to declare multiple app plugins within a single
SODAR Core app. For example, you may want your app to have both project specific
and site specific views and maybe also a backend API to be used by other apps.

For an example of a multi-plugin app in SODAR Core itself, see the
:ref:`app_timeline`.

There is no limit on how many plugins you can define for a SODAR Core app and
they may be of different types. However, certain conditions should be followed
when creating multi-plugin apps:

- Plugin names are expected to be unique. Not adhering to this may cause
  unexpected side-effects.
- For plugins with related UI views, it is strongly recommended to name all your
  plugins starting with the app name. For example, if your project app plugin is
  named ``yourapp``, it is recommended to name the secondary site app plugin
  e.g. ``yourapp_site``. This ensures the SODAR Core UI can detect your app and
  higlight active apps correctly.
- If your app includes multiple plugins with UI views, it is recommended to
  provide only the UI views relevant to that plugin in the ``urls`` attribute.
  This, again, ensures apps are correctly detected and highlighted in the UI.


.. _dev_resources_read_only:

Site Read-Only Mode
===================

A superuser can temporarily set the site into read-only mode. When the mode is
enabled, all data on the site is only accessible for reading. No project or user
data should be modifiable, except for superusers who still have full access.

SODAR Core apps enforce this mode by prohibiting access to views and/or UI
elements which enable the user to modify data. Apps developed for a SODAR Core
based site must implement this within their rule and UI logic.

If your data modifying view is in a project app and uses the
``can_modify_project_data()`` rule predicate, checks for view access are already
performed for that view in the permission checks. Example of this in a
``rules.py`` file:

.. code-block:: python

    import rules
    from projectroles import rules as pr_rules

    rules.add_perm(
        'your_project_app.update_data',
        pr_rules.can_modify_project_data
        & (
            pr_rules.is_project_owner
            | pr_rules.is_project_delegate
            | pr_rules.is_project_contributor
        ),
    )

For site views, you can use the ``is_site_writable()`` predicate. Example:

.. code-block:: python

    import rules
    from projectroles import rules as pr_rules

    rules.add_perm(
        'your_site_app.update_data',
        rules.is_authenticated & pr_rules.is_site_writable,
    )

To check for the mode in your Python code, you should use the app settings API
as follows:

.. code-block:: python

    from projectroles.app_settings import AppSettingAPI
    app_settings = AppSettingAPI()

    if app_settings.get('projectroles', 'site_read_only'):
        pass  # Add logic for read-only mode here

In templates, the same can be done using the ``get_app_setting()`` template tag.
Example:

.. code-block:: django

    {% load projectroles_common_tags %}
    {% get_app_setting 'projectroles' 'site_read_only' as site_read_only %}
    {% if site_read_only %}
      {# ... #}
    {% endif %}

If you need to check the site read-only status in client-side apps, you can
query the ``SiteReadOnlySettingAjaxView`` Ajax view. See
:ref:`app_projectroles_api_django_ajax_common` for more information.

.. note::

    It is assumed that in read-only mode, superusers are still able to access
    data modifying views and operations. The rule settings also allow this.
    Actions within management commands should thus also be allowed in read-only
    mode.


Management Command Logger
=========================

When developing management commands for your apps, you may want to log certain
events while also ensuring relevant output is provided to the administrator
issuing a command. For this SODAR Core provides the
``ManagementCommandLogger`` class. It can be called like the standard Python
logger with shortcut commands such as ``info()``, ``debug()`` etc. If you need
to access the actual Python logger being used, you can access it via
``ManagementCommandLogger.logger``. Example of logger usage can be seen below.

.. code-block:: python

    from projectroles.management.logging import ManagementCommandLogger
    logger = ManagementCommandLogger(__name__)
    logger.info('Testing')

.. note::

    The use of this logger class assumes your site sets up logging similarly to
    the example site and the SODAR Django Site template, including the use of a
    ``LOGGING_LEVEL`` Django settings variable.

.. hint::

    To disable redundant console output from commands using this logger in e.g.
    your site's test configuration, you can set the
    ``LOGGING_DISABLE_CMD_OUTPUT`` Django setting to ``True``.


Testing
=======

SODAR Core provides a range of ready made testing classes and mixins for
different aspects of SODAR app testing, from user permissions to UI testing.
See ``projectroles.tests`` for different base classes.

Test Settings
-------------

SODAR Core provides settings for configuring your UI tests, if using the base
UI test classes found in ``projectroles.tests.test_ui``. Default values for
these settings can be found in ``config/settings/test.py``. The settings are as
follows:

``PROJECTROLES_TEST_UI_CHROME_OPTIONS``
    Options for Chrome through Selenium. Can be used to e.g. enable/disable
    headless testing mode.
``PROJECTROLES_TEST_UI_WINDOW_SIZE``
    Custom browser window size.
``PROJECTROLES_TEST_UI_WAIT_TIME``
    Maximum wait time for UI test operations
``PROJECTROLES_TEST_UI_LEGACY_LOGIN``
    If set ``True``, use the legacy UI login and redirect function for testing
    with different users. This can be used if e.g. issues with cookie-based
    logins are encountered.

Base Test Classes and Helpers
-----------------------------

For base classes and mixins with useful helpers, see the ``projectroles.tests``
modules. The test cases also provide useful examples on how to set up your own
tests.


Debugging
=========

Debugging helpers and tips are detailed in this section.

Profiling Middleware
--------------------

SODAR Core provides a cProfile using profiler for tracing back sources of page
loading slowdowns. To enable the profiler middleware, include
``projectroles.middleware.ProfilerMiddleware`` in ``MIDDLEWARE`` under your site
configuration. It is recommended to use a settings variable for this similar to
the example site configuration, where ``PROJECTROLES_ENABLE_PROFILING`` controls
this.

Once enabled, adding the ``?prof`` query string attribute to and URL displays
the profiling information.
