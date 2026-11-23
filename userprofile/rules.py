import rules

from django.conf import settings

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates
from projectroles.models import RoleAssignment, ROLE_RANKING, SODAR_CONSTANTS

# Projectroles constants
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']


# Predicates -------------------------------------------------------------


@rules.predicate
def can_delete_email(user, obj):
    return obj.user == user


@rules.predicate
def can_view_list(user):
    if not getattr(settings, 'PROJECTROLES_USER_LIST_ENABLE', True):
        return False
    if getattr(settings, 'PROJECTROLES_API_USER_DETAIL_RESTRICT', False):
        role_kw = {
            'user': user,
            'role__rank__lte': ROLE_RANKING[PROJECT_ROLE_CONTRIBUTOR],
        }
        if RoleAssignment.objects.filter(**role_kw).count() == 0:
            return False
    return True


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------


# Allow viewing user details
rules.add_perm('userprofile.view_detail', rules.is_authenticated)

# Allow updating settings
rules.add_perm(
    'userprofile.update_settings',
    rules.is_authenticated & pr_rules.is_site_writable,
)

# Allow creating additional email
rules.add_perm(
    'userprofile.create_email',
    pr_rules.is_source_site
    & rules.is_authenticated
    & pr_rules.is_site_writable,
)

# Allow deleting additional email
rules.add_perm(
    'userprofile.delete_email',
    pr_rules.is_source_site & can_delete_email & pr_rules.is_site_writable,
)

# Allow viewing user list
rules.add_perm('userprofile.view_list', rules.is_authenticated & can_view_list)
