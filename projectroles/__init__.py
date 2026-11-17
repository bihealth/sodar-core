"""
SODAR project and role management
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('django-sodar-core')
except PackageNotFoundError:
    __version__ = ''

default_app_config = 'projectroles.apps.ProjectrolesConfig'  # pylint: disable=invalid-name
