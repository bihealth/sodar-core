"""General utility methods for projectroles and SODAR Core"""

import logging
import random
import string

from typing import Optional

from django.conf import settings

from projectroles.models import SODAR_CONSTANTS


logger = logging.getLogger(__name__)


def get_display_name(
    key: str, title: bool = False, count: int = 1, plural: bool = False
) -> str:
    """
    Return display name from SODAR_CONSTANTS.

    :param key: Key in SODAR_CONSTANTS['DISPLAY_NAMES'] to return (string)
    :param title: Return name in title case if true (boolean, optional)
    :param count: Item count for returning plural form, overrides plural=False
                  if not 1 (int, optional)
    :param plural: Return plural form if True, overrides count != 1 if True
                   (boolean, optional)
    :return: String
    """
    ret = SODAR_CONSTANTS['DISPLAY_NAMES'][key][
        'plural' if count != 1 or plural else 'default'
    ]
    return ret.lower() if not title else ret.title()


def build_secret(length: Optional[int] = None) -> str:
    """
    Return secret string for e.g. public URLs.

    :param length: Length of string, use None for default (integer or None)
    :return: Randomized secret (string)
    """
    if not length:
        length = getattr(settings, 'PROJECTROLES_SECRET_LENGTH', 32)
    length = int(length) if int(length) <= 255 else 255
    return ''.join(
        random.SystemRandom().choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )


def get_app_names() -> list[str]:
    """Return list of names for locally installed non-django apps"""
    ret = []
    for a in settings.INSTALLED_APPS:
        s = a.split('.')
        if s[0] not in ['django', settings.SITE_PACKAGE]:
            if len(s) > 1 and 'apps' in s:
                ret.append('.'.join(s[0 : s.index('apps')]))
            else:
                ret.append(s[0])
    return sorted(ret)
