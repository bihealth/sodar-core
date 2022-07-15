.. _dev_core_guide:

SODAR Core Development Guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This subsection lists specific conventions and guidelines for contributing
code or documentation to SODAR Core.


Work Branches
=============

Make sure to base your work branch on the ``dev`` branch. This branch is used
for development and is always the latest "bleeding edge" version of SODAR Core.
The ``main`` branch is only used for merging stable releases.

When naming your work branches, prefix them with the issue name, e.g.
``123-your-new-feature`` or ``123-bug-being-fixed``. It is recommended to keep
the branch names short and concise.


Commits
=======

It is recommended to use short but descriptive commit messages and always
include the related issue ID(s) in the message. Examples:

- ``add local irods auth api view (#1263)``
- ``fix ontology column config tooltip hiding (#1379)``


Pull Requests
=============

Please add the related issue ID(s) to the title of your pull request and ensure
the pull request is set against the ``dev`` branch.

Before submitting a pull request for review, ensure the following:

- You have followed code conventions (see :ref:`dev_core_guide_code`).
- You have updated existing tests and/or written new tests as applicable (see
  :ref:`dev_core_guide_test`).
- You have updated documentation if your pull requests adds or modifies features
  (see :ref:`dev_core_guide_doc`).
- ``make black`` has been run for the latest commit.
- ``flake8 .`` produces no errors.
- All tests pass with ``make test``.

Your pull request should work on the Python versions currently supported by the
SODAR Core dev version. These will be checked by GitHub Actions CI upon pushing
your commit(s).


.. _dev_core_guide_code:

Code Conventions
================

The following conventions should be adhered to in SODAR Core development:

- Limit line length to 80 characters.
    * Exception: Docstrings for REST API endpoint methods.
    * Exception: Documentation syntax where this can not be avoided, e.g. long
      references in RST.
- Use single quotes instead of double quotes for variables.
    * Black does not enforce this, so they have to be ensured manually.
- Do not use RST syntax in docstrings or comments.
    * Exception: Docstrings for REST API endpoint methods.
- No type hints should be used at the moment.
    * Possibility to expand the entire project into using type hints will be
      looked into.


.. _dev_core_guide_test:

Testing Conventions
===================

The following conventions should be followed when writing tests for your code
commits:

- Use common base classes and helpers from ``projectroles.tests.*`` where
  applicable.
- Update existing tests according to your changes.
- Add new tests for new features or cases where tests are missing.
- Always add tests for the following components:
    * Models
    * Views (UI, Ajax and REST)
    * Custom plugin methods
    * Management commands
- For views, add permission tests and view tests.
- Separate tests for forms are not necessary, they should go under UI view
  tests.
- Similarly, tests for serializers can be contained within API view tests.
- Add Selenium UI tests for any relevant changes in the UI logic, templates and
  JQuery.


.. _dev_core_guide_doc:

Documentation
=============

Documentation of SODAR Core is in the ReStructuredText (RST) format. It is
compiled using Sphinx with the Readthedocs theme. Please follow formatting
conventions displayed in existing documentation. A full style guide will be
provided later.

Static assets should be placed under ``docs/source/_static/document_name/``.

Once you have finished your edits, build the documentation to ensure no warnings
or errors are raised. You will need to be in your virtual environment with
Sphinx and other requirements installed.

.. code-block:: bash

    $ cd docs
    $ make html

Note that in some cases such as editing the index, changes may not be visible
unless you build the docs from scratch. In that case, first remove previously
built files with ``rm -rf build``.

When updating the ``CHANGELOG`` file, the following conventions should be
followed:

- Split updates into the Added/Changed/Fixed/Removed categories.
- Under each category, mark updates under the related app if applicable,
  otherwise use *General*.
- Write brief but descriptive descriptions followed by issue ID(s). Previous
  entries serve as examples.
