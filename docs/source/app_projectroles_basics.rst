.. _app_projectroles_basics:


Projectroles Basics
^^^^^^^^^^^^^^^^^^^

The basic concepts and functionalities of the ``projectroles`` app are detailed
in this document.


Projects
========

The projectroles app groups data into **projects**. Here, a **project** is a
data container object that other objects can be linked to (typically through a
1:n foreign key relationship). A **category** is a sub-type of a project which
is allowed to contain other categories and projects but no other data type.

Using categories and projects, data can be organized in a tree structure of
category and project "containers". Users can be granted access to projects using
roles as described in the next section.


.. _app_projectroles_basics_roles:

User Roles in Projects
======================

A **role** is a model defined by a string identifier (e.g., "project guest").
Roles are assigned to individual users in the context of individual projects
in a n:m relation. For example, user "alice" might be assigned the
"project guest" role in one project and another role (or no role at all) in a
second project. Users can only have one role in a given project at any given
time.

Roles are inherited to categories and projects from parent categories. Inherited
roles can be promoted to higher ranking local roles for specific categories and
projects. In the case of a category, this promotion will apply to all child
categories below it.

Demoting inherited roles is not allowed. In practice, this means that if a user
has a certain role for a category, they will either have the same or higher
level of user access for all of its child categories and projects.

The built-in roles in SODAR Core are as follows:

- **Project Owner**
    - Full read/write access to project data and roles
    - Can create sub-projects under owned categories
    - One per project
    - Must be specified upon project creation
    - Rank = 10
- **Project Delegate**
    - Full read/write access to project data
    - Can modify roles except for owner and delegate
    - One per project (by default, the limit can be increased in site settings)
    - Assigned by owner
    - Rank = 20
- **Project Contributor**
    - Can read and write project data
    - Can modify and delete own data
    - Rank = 30
- **Project Guest**
    - Read-only access to project data
    - Rank = 40
- **Project Viewer**
    - Limited read-only access to project data
    - User can see category or project readme and its members
    - User can not access bgjobs, filesfolders or timeline apps in the project
    - User may or may not access other project apps and data based on site rules
    - Used for cases where we want to enable discoverability without providing
      access to e.g. confidential data files
    - Rank = 45
- **Project Finder**
    - Role can only been given for categories
    - User can see categories and their member roles
    - User can see titles of projects under categories in UI home view project
      list, the corresponding REST API view and project search results
    - User can not access projects, project apps or project data without a
      greater role
    - Used for e.g. staff for ensuring relevant categories and projects are
      discoverable without granting superuser status
    - Rank = 50

.. note::

    Django **superuser** status overrides all project role access checks.

The projectroles app provides the following features for managing user roles in
projects:

- Adding/modifying/removing site users as project members
- Inviting people not yet using the site by email
- Automated emailing of users regarding role changes
- Mirroring user roles to/from an external projectroles-enabled site

.. note::

    Currently, only superusers can assign owner roles for top level categories.

New types of roles can be defined for third party apps by extending the default
model's database table in the projectroles app. Existing SODAR Core apps do not
fully support custom roles at the moment, but extended support is planned in a
future release.


Remote Project Sync
===================

SODAR Core allows optionally reading and synchronizing project metadata between
multiple SODAR-based Django sites. A superuser is able to set desired levels of
remote access for specific sites on a per-project basis.

A SODAR site can have one of three modes: **source**, **target** or **peer**
mode.

A SODAR site can be set by the user in either **source** or **target** mode.

- **Source site** is one expecting to (potentially) serve project metadata to
  an arbitrary number of other SODAR sites.
- **Target site** can be linked with exactly one source site, from which it
  can retrieve project metadata. Creation of local projects can be enabled or
  disabled according to local configuration.
- **Peer** mode is used only if two or more Target sites link to the same Source
  site. If synchronizing a project which has multiple accessing Target sites,
  metadata about those other Target sites is included and stored in Peer mode
  site objects.

Among the data which can be synchronized:

- General project information such as title, description and readme
- Project category structure
- User roles in projects
- User accounts for LDAP/AD and OIDC users (required for the previous step)
- Information of other Target Sites linking a common project

Target sites read remote project information from the source site. When
deploying a target site, it is possible to enable automated synchronization of
projects from the source site by running a Redis server and a Celery worker
process.


Rule System
===========

Projectroles uses the `django-rules <https://github.com/dfunckt/django-rules>`_
package to manage permissions for accessing data, apps and functionalities
within projects based on the user role. Predicates for project roles are
provided by the projectroles app and can be used and extended for developing
rules for your other project-specific Django apps.


App Plugins
===========

Projectroles provides a plugin framework to enable integrating apps and
content dynamically to a projectroles-enabled Django site. Types of apps and
corresponding app plugins currently included:

- **Project apps**: Apps related to specific projects, making use of project
  access control and providing data and content within the project's scope
- **Site apps**: Site-wide Django apps which are not project-specific
- **Backend apps**: Backend apps without a GUI entry point, imported and used
  dynamically by other SODAR-based apps for e.g. connectivity to external
  resources.

App plugins are not limited to one per Django app. A single Django app in SODAR
Core may contain one or more of the aforementioned plugin types, depending on
the required functionality.

Existing apps can be modified to conform to the plugin structure by implementing
certain variables, functions, views and templates within the app. For more
details, see the app development documents.


Other Features
==============

Other features in the projectroles app:

- **App settings**: Setting values for project, user or site specific variables,
  which can be defined in project and site app plugins
- **Project starring**: Ability for users to star projects as their favourites
- **Project search**: Functionality for searching data within projects using
  functions implemented in project app plugins
- **Tour help**: Inline help for pages
- **Project readme**: README document for each project with Markdown support
- **Custom user model**: Additions to the standard Django user model
- **Multi-domain LDAP/AD support**: Support for LDAP/AD users from multiple
  domains
- **Timeline integration**: Included but disabled unless the backend app
  for Timeline is enabled in your Django site


Templates and Styles
====================

Projectroles provides views and templates for all GUI-related functionalities
described above. The templates utilize the plugin framework to provide content
under projects dynamically. The project also provides default CSS stylings, base
templates and a base layout which can be used or adapted as needed. See the
usage and app development documentation for more details.
