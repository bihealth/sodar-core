"""
SODAR project and role management
"""

from . import _version  # noqa

__version__ = _version.get_versions()['version']

default_app_config = (
    'projectroles.apps.ProjectrolesConfig'  # pylint: disable=invalid-name
)
