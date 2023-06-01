"""Django signals for the projectroles app"""

from django.contrib.auth.signals import user_logged_in


# User signals -----------------------------------------------------------------


def handle_ldap_login(sender, user, **kwargs):
    """Signal for LDAP login handling"""
    if hasattr(user, 'ldap_username'):
        user.update_full_name()
        user.update_ldap_username()


def assign_user_group(sender, user, **kwargs):
    """Signal for user group assignment"""
    user.set_group()


user_logged_in.connect(handle_ldap_login)
user_logged_in.connect(assign_user_group)
