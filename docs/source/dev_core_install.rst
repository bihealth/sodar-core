.. _dev_core_install:

Development Installation
^^^^^^^^^^^^^^^^^^^^^^^^

Instructions on how to install a local development version of SODAR Core are
detailed here. Ubuntu 20.04 LTS (Focal) is the supported OS at this time.
Later Ubuntu versions and Centos 7 have also been proven to to work, but some
system dependencies may vary for different OS versions or distributions.

Installation and development should be possible on most recent versions of
Linux, Mac and Windows (WSL2 recommended). However, this may require extra work
and your mileage may vary.

If you need to set up the accompanying example site in Docker, please see online
for up-to-date Docker setup tutorials for Django related to your operating
system of choice.


System Dependencies
===================

First you need to install OS dependencies, PostgreSQL >=9.6 and Python >=3.8.

.. code-block:: console

    $ sudo utility/install_os_dependencies.sh
    $ sudo utility/install_python.sh
    $ sudo utility/install_postgres.sh


Database Setup
==============

Next you need to setup the database and postgres user. You'll be prompted to
enter a database name, a username and a password.

.. code-block:: console

    $ sudo utility/setup_database.sh

You have to set the database URL and credentials for Django in the environment
variable ``DATABASE_URL``. For development it is recommended to place
environment variables in file ``.env`` located in your project root. To enable
loading the file in Django, set ``DJANGO_READ_DOT_ENV_FILE=1`` in your
environment variables when running SODAR or any of its management commands.
See ``config/settings/base.py`` for more information and the ``env.example``
file for an example environment file.

Example of the database URL variable as set within an ``.env`` file:

.. code-block:: console

    DATABASE_URL=postgres://sodar_core:sodar_core@127.0.0.1/sodar_core


Repository and Environment Setup
================================

Clone the repository, setup and activate the virtual environment. Once in
the environment, install Python requirements for the project:

.. code-block:: console

    $ git clone https://github.com/bihealth/sodar-core.git
    $ cd sodar-core
    $ python3.x -m venv .venv
    $ source .venv/bin/activate
    $ utility/install_python_dependencies.sh


LDAP Setup (Optional)
=====================

If you will be using LDAP/AD auth on your site, make sure to also run:

.. code-block:: console

    $ sudo utility/install_ldap_dependencies.sh
    $ pip install -r requirements/ldap.txt


Final Setup
===========

Initialize the database (this will also synchronize django-plugins):

.. code-block:: console

    $ ./manage.py migrate

Create a Django superuser for the example_site:

.. code-block:: console

    $ ./manage.py createsuperuser --skip-checks --username admin

You are now able to run the server:

.. code-block:: console

    $ make serve
