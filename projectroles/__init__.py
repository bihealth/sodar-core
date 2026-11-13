"""
SODAR project and role management
"""

from importlib.metadata import (
    distribution,
    version as get_version_il,
    PackageNotFoundError,
)
from setuptools_scm import get_version as get_version_scm

dist_origin = ''
try:
    dist_origin = distribution('django-sodar-core').origin
except PackageNotFoundError:
    pass
if dist_origin:
    __version__ = get_version_il('django-sodar-core')
else:
    __version__ = get_version_scm(
        version_scheme='no-guess-dev',
        local_scheme='no-local-version',
        search_parent_directories=True,
    )

default_app_config = 'projectroles.apps.ProjectrolesConfig'  # pylint: disable=invalid-name
