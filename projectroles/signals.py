"""Django signals for the projectroles app"""

import logging

from axes.signals import user_locked_out
from django.conf import settings
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from rest_framework.exceptions import PermissionDenied

from projectroles.models import AUTH_PROVIDER_OIDC


logger = logging.getLogger(__name__)


# Local constants
ACCOUNT_LOCKED_MSG = 'Account locked, too many failed login attempts'


# User signals -----------------------------------------------------------------


def handle_ldap_login(sender, user, **kwargs):
    """Signal for LDAP login handling"""
    try:
        if hasattr(user, 'ldap_username'):
            logger.debug('Updating LDAP user..')
            user.update_ldap_username()
            user.update_full_name()
    except Exception as ex:
        logger.error(f'Exception in handle_ldap_login(): {ex}')
        if settings.DEBUG:
            raise ex


def handle_oidc_login(sender, user, **kwargs):
    """Signal for OIDC login handling"""
    social_auth = getattr(user, 'social_auth', None)
    if not social_auth:
        return
    try:
        social_auth = social_auth.first()
        if social_auth and social_auth.provider == AUTH_PROVIDER_OIDC:
            logger.debug('Updating OIDC user..')
            user.update_full_name()
    except Exception as ex:
        logger.error(f'Exception in handle_oidc_login(): {ex}')
        if settings.DEBUG:
            raise ex


def assign_user_group(sender, user, **kwargs):
    """Signal for user group assignment"""
    try:
        user.set_group()
    except Exception as ex:
        logger.error(f'Exception in assign_user_group(): {ex}')
        if settings.DEBUG:
            raise ex


def log_user_login(sender, user, **kwargs):
    """Signal for logging user login"""
    logger.info(f'User logged in: {user.username}')


def log_user_logout(sender, user, **kwargs):
    """Signal for logging user logout"""
    if user:
        logger.info(f'User logged out: {user.username}')


def log_user_login_failure(sender, credentials, **kwargs):
    """Signal for user login failure"""
    logger.info('User login failed: {}'.format(credentials.get('username')))


user_logged_in.connect(handle_ldap_login)
user_logged_in.connect(handle_oidc_login)
user_logged_in.connect(assign_user_group)
user_logged_in.connect(log_user_login)
user_logged_out.connect(log_user_logout)
user_login_failed.connect(log_user_login_failure)


# Axes signals -----------------------------------------------------------------


@receiver(user_locked_out)
def raise_axes_permission_denied(request, *args, **kwargs):
    """Raise permission denied for API views if axes has locked out user"""
    # TODO: This detection of API calls is somewhat hacky, better ideas?
    if (
        'json' in request.META.get('HTTP_ACCEPT', '').lower()
        or '/api/' in request.get_full_path()
    ):
        raise PermissionDenied(ACCOUNT_LOCKED_MSG)
