.. _dev_projectroles_integration:


Integration in an Existing Site
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Instructions for setting up projectroles and SODAR Core on an existing Django
site or a fresh site generated with cookiecutter-django are detailed in this
chapter. See :ref:`getting_started` for a list of the system requirements.

.. warning::

    In order to successfully set up projectroles, you are expected to **follow
    all the instructions here in the order they are presented**. Please note
    that leaving out steps may result in a non-working Django site! Attempting
    to run the site before following all of the steps may (and probably will)
    result in errors.

.. warning::

    The rest of this section was originally written for the
    `1.11 release of cookiecutter-django <https://github.com/pydanny/cookiecutter-django/releases/tag/1.11.10>`_.
    Some details such as directory structures and settings variables may differ.


Installation
============

First, add the ``django-sodar-core`` dependency into your
``requirements/base.txt`` file (the package can be found in PyPI). Make sure
you are pointing to the desired release tag, as the package is under active
development and breaking changes are expected.

.. code-block:: console

    django-sodar-core==x.y.z

Install the requirements for development:

.. code-block:: console

    $ pip install -r requirements/local.txt

If any version conflicts arise between django-sodar-core and your existing site,
you will have to resolve them before continuing.

Please note that the django-sodar-core package only installs
:term:`Django apps<Django App>`, which you need to include in a
:term:`Django web site<Django Site>` project. For instructions for integrating
SODAR Core into an existing Django site or setting up a new site,
see the :ref:`projectroles app documentation <app_projectroles>`.
A list of all the apps which are part of SODAR Core can be found in the
:ref:`overview_sodar_core_apps` section

.. hint::

    You can always refer to either the ``sodar-django-site`` repository or
    ``example_site`` in the SODAR Core repository for a working example of a
    Cookiecutter-based Django site integrating SODAR Core. However, note that
    some aspects of the site configuration may vary depending on the
    cookiecutter-django version used on your site.


Django Settings
===============

Next you need to modify your default :term:`Django settings<Django Settings>`
file, usually located in ``config/settings/base.py``. For sites created with an
older cookiecutter-django version the file name may also be ``common.py``.
Naturally, you should make sure no settings in other configuration files
conflict with ones set here.

For values retrieved from environment variables, make sure to configure your
env accordingly. For development and testing, using ``READ_DOT_ENV_FILE`` is
recommended.

Required and optional Django settings are described in the
:ref:`app_projectroles_settings` document.


User Configuration
==================

In order for SODAR Core apps to work on your Django site, you need to extend the
default user model.

Extending the User Model
------------------------

In a cookiecutter-django based project, an extended user model should already
exist in ``{SITE_NAME}/users/models.py``. The abstract model provided by the
projectroles app provides the same model with critical additions.

Notable additions to the ``SODARUser`` model:

``enable_update``
    Field for enabling or disabling the ability to update the user profile for a
    local non-superuser account. Currently only affects local user accounts.
``sodar_uuid``
    Field used as an unique identifier for SODAR Core objects, including users.

If you have not added any of your own modifications to the model, you can simply
**replace** the existing model extension with the following code:

.. code-block:: python

    from projectroles.models import SODARUser

    class User(SODARUser):
        pass

If you need to include your own extra fields or functions (or have existing ones
already), you can add them in this model.

After updating the user model, create and run database migrations.

.. code-block:: console

    $ ./manage.py makemigrations
    $ ./manage.py migrate

.. note::

    You probably will need to edit the default unit tests under
    ``{SITE_NAME}/users/tests/`` for them to work after making these changes.
    See ``example_site.users.tests`` in this repository for an example.

Populating UUIDs for Existing Users
-----------------------------------

When integrating projectroles into an existing site with existing users, the
``sodar_uuid`` field needs to be populated. See
`instructions in Django documentation <https://docs.djangoproject.com/en/3.1/howto/writing-migrations/#migrations-that-add-unique-fields>`_
on how to create the required migrations.

Custom User Admin Class
-----------------------

If you want to manage your users in the admin interface in addition to the
Django shell, it is strongly recommended to use or extend the ``SODARUserAdmin``
class on your site. You can do this by e.g. setting up ``$SITE/users/admin.py``
as follows:

.. code-block:: django

    from django.contrib import admin
    from projectroles.admin import SODARUserAdmin
    from .models import User

    # ...

    @admin.register(User)
    class MyUserAdmin(SODARUserAdmin):
        form = MyUserChangeForm
        add_form = MyUserCreationForm
        # Add other overrides here as needed

Synchronizing User Groups for Existing Users
--------------------------------------------

To set up user groups for existing users, run the ``syncgroups`` management
command.

.. code-block:: console

    $ ./manage.py syncgroups

User Profile Site App
---------------------

The ``userprofile`` site app is installed with SODAR Core. It adds a user
profile page in the user dropdown. Use of the app is not mandatory but
recommended, unless you are already using some other user profile app. See
the :ref:`userprofile app documentation <app_userprofile>` for instructions.

Add Login Template
------------------

You should add a login template to ``{SITE_NAME}/templates/users/login.html``. If
you're OK with using the projectroles login template, the file can consist of
the following line:

.. code-block:: django

    {% extends 'projectroles/login.html' %}

If you intend to use projectroles templates for user management, you can delete
other existing files within the directory.


URL Configuration
=================

In the Django URL configuration file, usually found in ``config/urls.py``, add
the following lines under ``urlpatterns`` to include projectroles URLs in your
site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'api/auth/', include('knox.urls')),
        url(r'^project/', include('projectroles.urls')),
    ]

If you intend to use projectroles views and templates as the basis of your site
layout and navigation (which is recommended), also make sure to set the site's
home view accordingly:

.. code-block:: python

    from projectroles.views import HomeView

    urlpatterns = [
        # ...
        url(r'^$', HomeView.as_view(), name='home'),
    ]

Finally, make sure your login and logout links are correctly linked. You can
remove any default allauth URLs if you're not using it.

.. code-block:: python

    from django.contrib.auth import views as auth_views

    urlpatterns = [
        # ...
        url(r'^login/$', auth_views.LoginView.as_view(
            template_name='users/login.html'), name='login'),
        url(r'^logout/$', auth_views.logout_then_login, name='logout'),
    ]


Base Template for Your Django Site
==================================

In order to make use of Projectroles views and templates, you should set the
base template of your site accordingly in ``{SITE_NAME}/templates/base.html``.

For a supported example, see ``projectroles/base_site.html``. It is strongly
recommended to use this as the base template for your site, either by extending
it or copying the content into ``{SITE_NAME}/templates/base.html`` and modifying
it to suit your needs.

If you do not need to make any modifications, the most simple way is to replace
the content of the ``{SITE_NAME}/templates/base.html`` file with the following
line:

.. code-block:: django

    {% extends 'projectroles/base_site.html' %}

.. note::

    CSS and Javascript includes in ``site_base.html`` are **mandatory** for
    Projectroles-based views and functionalities.

.. note::

    The container structure defined in the example base.html, along with
    including the ``{STATIC}/projectroles/css/projectroles.css`` are
    **mandatory** for Projectroles-based views to work without modifications.


Site Error Templates
====================

The projectroles app contains default error templates to use on your site.
These are located in the ``projectroles/error/`` template directory. You can
use them by entering ``{% extends 'projectroles/error/*.html %}`` in the
corresponding files found in the ``{SITE_NAME}/templates/`` directory. You have
the options of extending or replacing content on the templates, or simply
implementing your own.


Site Icons
==========

SODAR Core uses `Iconify <https://iconify.design/>`_ to include icons on the
site. SODAR Core apps use the `Material Design Icons <https://materialdesignicons.com>`_
icon collection, however other collections can be added to your site.

To enable the icons on your site, run the following management commands:

.. code-block:: console

    $ ./manage.py geticons
    $ ./manage.py collectstatic

If you want to use additional icon collections, you can add them using the
``-c`` argument as displayed in the following example:

.. code-block:: console

    $ ./manage.py geticons -c carbon clarity

You can view the supported icon collections
`here <https://github.com/iconify/collections-json/tree/master/json>`_.

The Iconify JSON files are rather large and potentially frequently updated, so
it is recommended to ignore them in your Git setup and instead retrieve them
dynamically for CI and deployment. Before committing your code, it is
recommended to update your ``.gitignore`` file with the following lines:

.. code-block::

    */static/iconify/*.json
    */static/iconify/json/*.json

All Done!
=========

After following all the instructions above, you should have a working SODAR Core
based Django site with support for projectroles features and SODAR Core apps. To
test the site locally execute the supplied make command:

.. code-block:: console

    $ make serve

Or, run the standard Django ``runserver`` command:

.. code-block:: console

    $ ./manage.py runserver

To enable periodic tasks, you need to additionally start a Celery worker. This
is done by running the ``make celery`` command:

.. code-block:: console

    $ make celery

You can now browse your site locally at ``http://127.0.0.1:8000``. You are
expected to log in to view the site. Use e.g. the superuser account you created
when setting up your cookiecutter-django site.

You can now continue on to create apps or modify your existing apps to be
compatible with the SODAR Core framework. See the
:ref:`development section <dev_site>` for app development guides. Also see the
:ref:`customization documentation <app_projectroles_custom>` for tips for
modifying the default appearance of SODAR Core.
