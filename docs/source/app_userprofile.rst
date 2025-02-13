.. _app_userprofile:


Userprofile App
^^^^^^^^^^^^^^^

The ``userprofile`` app is a site app which provides a user profile view for
projectroles compatible Django users and management of user specific settings.


Installation
============

It is **strongly recommended** to install the userprofile app into your site
when using projectroles, unless you require a specific user profile providing
app of your own.

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.

Django Settings
---------------

The userprofile app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'userprofile.apps.UserprofileConfig',
    ]

URL Configuration
-----------------

In the Django URL configuration file, add the following line under
``urlpatterns`` to include userprofile URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^user/', include('userprofile.urls')),
    ]

Register Plugin
---------------

To register the app plugin, run the following management command:

.. code-block:: console

    $ ./manage.py syncplugins

You should see the following output:

.. code-block:: console

    Registering Plugin for userprofile.plugins.ProjectAppPlugin


Usage
=====

After successful installation, the link for "User Profile" should be available
in the user dropdown menu in the top-right corner of the website UI after you
have logged in.


User Settings
=============

User settings are configured in the ``app_settings`` dictionary in your project
app plugins.

User settings defined in the ``projectroles`` app, available for all SODAR Core
using sites:

Receive Email for Admin Alerts
    Receive email for :ref:`admin alerts <app_adminalerts>`.
Display Project UUID Copying Link
    If set true, display a link in the project title bar for copying the project
    UUID into the clipboard.
Receive Email for Project Updates
    Receive email notifications for project or category creation, updating,
    moving and archiving.
Receive Email for Project Membership Updates
    Receive email notifications for project or category membership updates and
    invitation activity.
Project list title highlight
    Highlight project title in paths displayed in the project list.
Project list page size
    Amount of projects per page in the project list.

In the development setup, the SODAR Core example site apps also provide
additional settings for demonstrating settings features.


Additional Emails
=================

The user can configure additional emails for their user account in case they
want to receive automated emails to addresses other than their primary address.
The user profile view displays additional emails and provides controls for
managing these addresses.

.. hint::

    Managing addresses is only possible on a source site. On a target site,
    emails will be visible but not mofifiable.

A new additional email address can be added with a form accessible by clicking
on the :guilabel:`Add Email` button. After creation, a verification email will
be sent to the specified address. Opening a link contained in the email and
logging into the site will verify the email. Only verified email addresses will
receive automated emails from the site.

For each email address displayed in the list, there are controls to re-send the
verification email (in case of an unverified email) and deleting the address.
