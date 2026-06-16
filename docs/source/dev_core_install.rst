.. _dev_core_install:

Development Installation
^^^^^^^^^^^^^^^^^^^^^^^^

Instructions on how to install a local development version of SODAR Core are
detailed here. Ubuntu 24.04 LTS is the supported OS for development. For
deployment, the same Ubuntu version or a corresponding Debian release are
recommended. Other Linux variants can be used for development or deployment, but
some system dependencies may vary for different OS versions or distributions.

.. note::

    These instructions are also valid for developing the
    `sodar-django-site <https://github.com/bihealth/sodar-django-site>`_
    repository.


.. _dev_core_install_database:

1. Setup Database Servers
=========================

Developing SODAR Core requires PostgreSQL v12+ (v16 recommended) and Redis.
There are two options for setting up the databases: bringing up the
pre-configured Docker Compose network or manual setup.

Setup with Docker Compose (Recommended)
---------------------------------------

The easiest way to set up the database servers is by cloning
`sodar-core-docker-compose <https://github.com/bihealth/sodar-core-docker-compose>`_.
This repository sets up a Docker Compose network with the database servers as
containers. Follow the instructions in the repository readme to bring up the
network. The SODAR Core database and user will be set up automatically on
initial launch.

Manual Setup
------------

It is also possible to set up a server manually or use an existing server. To
install PostgreSQL prerequisites, run the following script:

.. code-block:: console

    $ sudo utility/install_postgres.sh

Once you have a PostgreSQL server running, you'll need to run the following SQL:

.. code-block:: sql

    CREATE DATABASE sodar_core;
    CREATE USER sodar_core WITH PASSWORD 'sodar_core';
    ALTER DATABASE sodar_core OWNER TO sodar_core;
    ALTER USER sodar_core CREATEDB;

If your PostgreSQL is running directly on your development host, you can also
use the following utility script:

.. code-block:: console

    $ sudo utility/setup_database.sh

To install Redis manually, run the following script:

.. code-block:: console

    $ sudo utility/install_redis.sh


2. Setup Repository
===================

Clone the SODAR Core repository from GitHub and create yourself a ``.env``
environment configuration file.

.. code-block:: console

    $ git clone https://github.com/bihealth/sodar-core.git
    $ cd sodar-core
    $ git checkout dev
    $ cp env.example .env

.. important::

    To enable loading environment variables from the ``.env`` file, make sure to
    set ``DJANGO_READ_DOT_ENV_FILE=1`` in the environment variables of the
    development host.

.. important::

    Make sure you are basing your work branches on  the ``dev`` branch. This is
    the bleeding edge branch used for SODAR Core development, except for
    specific situations such as patches to past releases.


3. Install OS Dependencies
==========================

For development, you are expected to run the Django server and possible Celery
worker locally. To get started, install the OS dependencies and Python >=3.11
(3.13 recommended).

.. code-block:: console

    $ sudo utility/install_os_dependencies.sh
    $ sudo utility/install_python.sh


4. Install Python Dependencies
==============================

To set up Python dependencies for the repository, you'll first need to activate
a virtual environment. Once within an active virtual environment, use the
provided script to install the Python dependencies for development. Example:

.. code-block:: console

    $ python3.x -m venv .venv
    $ source .venv/bin/activate
    $ utility/install_python_dependencies.sh


5. Install LDAP Dependencies (Optional)
=======================================

If you will be using LDAP/AD auth when developing, make sure to also run:

.. code-block:: console

    $ sudo utility/install_ldap_dependencies.sh
    $ pip install -r requirements/ldap.txt


6. Setup Django
===============

Initialize the SODAR Core Django database (this will also synchronize plugins):

.. code-block:: console

    $ ./manage.py migrate

Create a Django superuser for the example site:

.. code-block:: console

    $ ./manage.py createsuperuser --skip-checks --username admin

Run the ``geticons`` and ``collectstatic`` commands to download and enable
Iconify icons:

.. code-block:: console

    $ ./manage.py geticons
    $ ./manage.py collectstatic

You are now able to run the server:

.. code-block:: console

    $ make serve

To enable periodic tasks, you need to start a Celery worker in addition to the
Django server. This is done by running the ``make celery`` command in a separate
terminal.

.. code-block:: console

    $ make celery

.. note::

    SODAR Core itself currently uses Celery tasks only for remote project
    synchronization for target sites. If developing a source site, running this
    process is not necessary.


7. Create Development Users (Optional)
======================================

For creating a group of example users for your development site, it is
recommended to run the ``createdevusers`` management command. This creates the
users "alice", "bob", "carol", "dan" and "erin". The users will be created with
the password "sodarpass", unless a custom password is supplied via the ``-p`` or
``--password`` argument.

.. code-block:: console

    $ ./manage.py createdevusers

.. hint::

    Having multiple non-admin user accounts is useful for developing and trying
    out project and member access management features. It is recommended to log
    in to a dev server as a regular user whenever developing non-admin features,
    as this is enables quickly noting possible user access issues.
