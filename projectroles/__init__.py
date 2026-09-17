"""
SODAR project and role management
"""

from setuptools_scm import get_version

__version__ = get_version(
    version_scheme='no-guess-dev', local_scheme='dirty-tag'
)

default_app_config = 'projectroles.apps.ProjectrolesConfig'  # pylint: disable=invalid-name
