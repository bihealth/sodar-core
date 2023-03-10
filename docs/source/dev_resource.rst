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

- ``scope``: Scope of users to include (string)
    * ``all``: All users on the site
    * ``project``: Limit search to users in given project
    * ``project_exclude`` Exclude existing users of given project
- ``project``: Project object or project UUID string (optional)
- ``exclude``: List of User objects or User UUIDs to exclude (optional)
- ``forward``: Parameters to forward to autocomplete view (optional)
- ``url``: Autocomplete ajax class override (optional)
- ``widget_class``: Widget class override (optional)

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

For fields supporting markdown, it is recommended to use the
``SODARPagedownWidget`` found in ``projectroles.models``.


App Setting API
===============

For accessing and modifying app settings for project or site apps, you should
use the ``AppSettingAPI``. Below is an example of invoking the API. For the full
API docs, see :ref:`app_projectroles_api_django`.

.. code-block:: python

    from projectroles.app_settings import AppSettingAPI
    app_settings = AppSettingAPI()
    app_settings.get_app_setting('app_name', 'setting_name', project_object)  # Etc..

See the
:ref:`app settings API documentation <app_projectroles_api_django_settings>` for
detailed instructions for using the API.


Pagination Template
===================

A common template for adding navigation for list pagination can be found in
``projectroles/_pagination.html``. This can be included to any Django
``ListView`` template which provides the ``paginate_by`` definition, enabling
pagination. If a smaller layout is desired, the ``pg_small`` argument can be
used. An example can be seen below:

.. code-block:: django

    {% include 'projectroles/_pagination.html' with pg_small=True %}


Tour Help
=========

SODAR Core uses `Shepherd <https://shipshapecode.github.io/shepherd/docs/welcome/>`_
to present an optional interactive tour for a rendered page. To enable the tour
in your template, set it up inside the ``javascript`` template block. Within an
inline javascript strucure, set the ``tourEnabled`` variable to ``true`` and add
steps according to the `Shepherd documentation <https://shipshapecode.github.io/shepherd>`_.

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

    The use of this logger class assumes your site sets up logging simlarly to
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
these settings can be found in ``config/settings/test.py``. The settins are as
follows:

- ``PROJECTROLES_TEST_UI_CHROME_OPTIONS``: Options for Chrome through Selenium.
  Can be used to e.g. enable/disable headless testing mode.
- ``PROJECTROLES_TEST_UI_WINDOW_SIZE``: Custom browser window size.
- ``PROJECTROLES_TEST_UI_WAIT_TIME``: Maximum wait time for UI test operations
- ``PROJECTROLES_TEST_UI_LEGACY_LOGIN``: If set ``True``, use the legacy UI
  login and redirect function for testing with different users. This can be used
  if e.g. issues with cookie-based logins are encountered.

Base Test Classes and Helpers
-----------------------------

For base classes and mixins with useful helpers, see the ``projectroles.tests``
modules. The test cases also provide useful examples on how to set up your own
tests.

.. note::

    For REST API testing, SODAR Core uses separate base test classes for the
    internal SODAR Core API, and the API views implemented in the actual site
    built on SODAR Core. For the API views in your site, make sure to test them
    using e.g. ``TestAPIViewsBase`` and **not** ``TestCoreAPIViewsBase``.


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