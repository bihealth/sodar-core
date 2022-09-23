.. _repository:

Repository Contents
^^^^^^^^^^^^^^^^^^^

Directories
===========

The following directories are included in the repository. These include internal
SODAR Core apps, example apps, directories containing files for running the
Django development site, as well as a CI and issue tracker setup.


``.github``
    Files for GitHub Actions CI and issue templates.
``adminalerts``
    :ref:`app_adminalerts`.
``appalerts``
    :ref:`app_appalerts`.
``bgjobs``
    :ref:`app_bgjobs`.
``config``
    Example Django site configuration.
``docs``
    This documentation.
``example_backend_app``
    Example backend app.
``example_project_app``
    Example project app.
``example_site``
    Example Django site to be run in development.
``example_site_app``
    Example site-wide app.
``filesfolders``
    :ref:`app_filesfolders`.
``projectroles``
    :ref:`app_projectroles`. The main application containing the base project
    management logic of SODAR Core, required to run a SODAR Core based site.
``requirements``
    Requirements for SODAR Core and its development.
``siteinfo``
    :ref:`app_siteinfo`.
``sodarcache``
    :ref:`app_sodarcache`.
``timeline``
    :ref:`app_timeline`.
``tokens``
    :ref:`app_tokens`.
``userprofile``
    :ref:`app_userprofile`.
``utility``
    Setup scripts for development.

Files
=====

Relevant files in the root of the repository are detailed here.

``.gitlab-ci.yml``
    GitLab CI configuration, used on the internal CUBI GitLab server.
``CHANGELOG.rst``
    :ref:`Full changelog <changelog>` for the project.
``env.example``
    Example ``.env`` file for development.
``Makefile``
    Makefile used to run the server and tests during development along with
    other shortcuts.
``manage.py``
    The Django file for running management commands.
``README.rst``
    The project readme.
``requirements.txt``
    Requirements file placed here for compatibility. Actual requirements can be
    found in ``requirements/*.txt``.
``setup.cfg``
    Settings for Flake8, Pycodestyle and Versioneer. Generally these should not
    be touched.
``setup.py``
    The setup file for the ``django-sodar-core`` package.
``versioneer.py``
    Versioneer file for maintaining the SODAR Core version.
