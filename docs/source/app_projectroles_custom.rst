.. _app_projectroles_custom:

Projectroles Customization
^^^^^^^^^^^^^^^^^^^^^^^^^^

Here you can find some customization instructions and tips for projectroles and
SODAR Core.


CSS Overrides
=============

If some of the CSS definitions in ``{STATIC}/projectroles/css/projectroles.css``
do not suit your purposes, it is possible to override them in your own includes.
It is still recommended to include the *"Flexbox page setup"* section as
provided.

In this chapter are examples of overrides you can place e.g. in ``project.css``
to change certain defaults.

.. hint::

    While not explicitly mentioned, some parameters may require the
    ``!important`` argument to take effect on your site.

.. warning::

    In the future we may instead offer a full Bootstrap 4 theme, which may
    deprecate current overriding/extending CSS classes.

Static Element Coloring
-----------------------

If you wish to recolor the background of the static elements on the page
(title bar, side bar and project navigation breadcrumb), add the following
CSS overrides.

.. code-block:: css

    .sodar-base-navbar, .sodar-pr-sidebar, .sodar-pr-sidebar-nav {
      background-color: #ff00ff;
    }

    .sodar-pr-navbar {
      background-color: #00ff00;
    }

Sidebar Width
-------------

If the sidebar is not wide enough for your liking or e.g. a name of an app
overflowing, the sidebar can be resized with the following override:

.. code-block:: css

    .sodar-pr-sidebar {
        width: 120px;
    }


Title Bar
=========

You can implement your own title bar by replacing the default base.html include
of ``projectroles/_site_titlebar.html`` with your own HTML or include.

When doing this, it is possible to include elements from the default title bar
separately:

- Search form: ``projectroles/_site_titlebar_search.html``
- Site app and user operation dropdown:
  ``projectroles/_site_titlebar_dropdown.html``

See the templates themselves for further instructions.


Additional Title Bar Links
==========================

If you want to add additional links *not* related to apps in the title bar, you
can implement in the template file ``_titlebar_nav.html`` in the site's template
include directory. By default the directory is
``{SITE_NAME}/templates/include/``. A custom path can be provided using the
``PROJECTROLES_TEMPLATE_INCLUDE_PATH`` Django setting and environment variable.
Example of an extra link template:

.. code-block:: django

    {# Example extra link #}
    <li class="nav-item">
      <a href="#" class="nav-link" id="site-extra-link-x" target="_blank">
        <i class="iconify" data-icon="mdi:help-circle"></i> Extra Link
      </a>
    </li>


Extra Login View Content
========================

If you want to provide extra content in your site's login view, you can add
custom HTML into the template file ``_login_extend.html`` in the site's template
include directory. The content will appear below the login form and its
formatting is not restricted.


Site Logo
=========

An optional site logo can be placed into ``{STATIC}/images/logo_navbar.png`` to
be displayed in the default Projectroles title bar.


Custom Icon Collections
=======================

To use icons other than the default
`Material Design Icons <https://materialdesignicons.com>`_
collection, download the corresponding collection JSON file from the
`Iconify JSON repository <https://github.com/iconify/collections-json/tree/master/json>`_
into ``{SITE_NAME}/static/iconify/json``. After that run ``collectstatic`` and
the icons will be available using the collection identifier.


Project Breadcrumb
==================

To add custom content in the end of the default project breadcrumb, use
``{% block nav_sub_project_extend %}`` in your app template.

The entire breadcrumb element can be overridden by declaring
``{% block nav_sub_project %}`` block in your app template.


Footer
======

Footer content can be specified in the optional template file
``{SITE_NAME}/templates/include/_footer.html``. Alternatively,
you can provide a full path to a ``_footer.html`` template directory
in the ``PROJECTROLES_TEMPLATE_INCLUDE_PATH`` in the environment file.


Project and Category Display Names
==================================

If the *project* and *category* labels don't match your use case, it is possible
to change the labels displayed to the user by editing ``SODAR_CONSTANTS`` in
your Django site settings file. Example:

.. code-block:: python

    SODAR_CONSTANTS = get_sodar_constants(default=True)
    SODAR_CONSTANTS['DISPLAY_NAMES']['CATEGORY'] = {
        'default': 'not-a-category',
        'plural': 'non-categories',
    }
    SODAR_CONSTANTS['DISPLAY_NAMES']['PROJECT'] = {
        'default': 'not-a-project',
        'plural': 'non-projects',
    }

See more about overriding ``SODAR_CONSTANTS``
:ref:`here <app_projectroles_settings>`.

To print out these values in your views or templates, call the
``get_display_name()`` function, which is available both as a template tag
through ``projectroles_common_tags.py`` and a general utility function in
``utils.py``. Capitalization and pluralization are handled by the function
according to arguments.
See the :ref:`Django API documentation <app_projectroles_api_django>` for
details.

.. note::

    These changes will **not** affect role names or IDs and descriptions of
    Timeline events.

