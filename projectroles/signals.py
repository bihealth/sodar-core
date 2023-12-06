"""Django signals for the projectroles app"""

import logging

from django.conf import settings
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)


logger = logging.getLogger(__name__)


# User signals -----------------------------------------------------------------


def handle_ldap_login(sender, user, **kwargs):
    """Signal for LDAP login handling"""
    try:
        if hasattr(user, 'ldap_username'):
            user.update_full_name()
            user.update_ldap_username()
    except Exception as ex:
        logger.error('Exception in handle_ldap_login(): {}'.format(ex))
        if settings.DEBUG:
            raise ex


def assign_user_group(sender, user, **kwargs):
    """Signal for user group assignment"""
    try:
        user.set_group()
    except Exception as ex:
        logger.error('Exception in assign_user_group(): {}'.format(ex))
        if settings.DEBUG:
            raise ex


def log_user_login(sender, user, **kwargs):
    """Signal for logging user login"""
    logger.info('User logged in: {}'.format(user.username))


def log_user_logout(sender, user, **kwargs):
    """Signal for logging user logout"""
    if user:
        logger.info('User logged out: {}'.format(user.username))


def log_user_login_failure(sender, credentials, **kwargs):
    """Signal for user login failure"""
    logger.info('User login failed: {}'.format(credentials.get('username')))


user_logged_in.connect(handle_ldap_login)
user_logged_in.connect(assign_user_group)
user_logged_in.connect(log_user_login)
user_logged_out.connect(log_user_logout)
user_login_failed.connect(log_user_login_failure)
