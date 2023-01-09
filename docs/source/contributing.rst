.. _contributing:

Contributing
^^^^^^^^^^^^

Contributions to the SODAR Core package are welcome and they are greatly
appreciated! Every little bit helps, and credit will always be given. You can
contribute in many ways detailed in the following subsection.


Types of Contributions
======================

Report Bugs
-----------

Report bugs through the
`SODAR Core issue tracker <https://github.com/bihealth/sodar-core/issues>`_ in
GitHub.

When reporting a bug, please follow the provided template. Make sure to include
the following information:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

Fix Bugs
--------

Look through the issue tracker for bugs. Anything tagged with ``bug`` and
``help wanted`` is open to whoever wants to implement it.

Implement Features
------------------

Look through the issue tracker for features. Anything tagged with ``feature``
and ``help wanted`` is open to whoever wants to implement it.

Write Documentation
-------------------

SODAR Core can always use more documentation, whether as part of the
official SODAR Core docs, in docstrings, or even on the web in blog posts,
articles, and such.

For contributing to the official documentation, see
:ref:`Documentation Guidelines <dev_core_guide_doc>`.

For editing docstrings, see :ref:`dev_core_guide_code`.

Submit Feedback
---------------

The best way to send feedback is to file an issue in the issue tracker.

If you are proposing a feature:

- Follow the provided template.
- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Separate multiple suggestions into separate issues, avoiding "umbrella
  tickets" and ensuring simple assignment and follow-up.
- Remember that this is a volunteer-driven project, and that contributions are
  welcome :)


Get Started
===========

Ready to contribute code to SODAR Core? Here are the steps to get started.

1. Fork the `sodar-core <https://github.com/bihealth/sodar-core>`_ repo on
   GitHub.

2. Clone your fork locally. ::

    $ git clone git@github.com:your_name_here/sodar-core.git

3. Set up SODAR Core for development. For instructions see
   :ref:`dev_core_install`.

4. Create a branch for local development. Make sure to base it on the ``dev``
   branch. You can now make your changes locally. ::

    $ git checkout -b 123-branch-name dev

5. When you're done making changes, make sure to apply proper formatting using
   Black. Next, check linting with flake8. Finally, run the tests.::

    $ make black
    $ flake8 .
    $ make test

6. Once flake8 and tests, commit your changes and push your branch to GitHub. ::

    $ git add .
    $ git commit -m "add/update/fix issue-description-here (#issue-id)"
    $ git push origin 123-branch-name

7. Submit a pull request through the GitHub website.

For specific requirements and recommendations on work branches, commits and pull
requirements, see :ref:`dev_core_guide`.

For guidelines regarding the code itself, see :ref:`dev_core_guide_code`.
