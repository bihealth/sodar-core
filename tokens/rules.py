"""Permissions for the tokens app"""

import rules

from django.conf import settings

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates
from projectroles.models import RoleAssignment


# Predicates -------------------------------------------------------------------


@rules.predicate
def can_create_token(user):
    if (
        not user.is_superuser
        and getattr(settings, 'TOKENS_CREATE_PROJECT_USER_RESTRICT', False)
        and RoleAssignment.objects.filter(user=user).count() == 0
    ):
        return False
    return True


# Permissions ------------------------------------------------------------------

# View tokens list
rules.add_perm('tokens.view_list', rules.is_authenticated)

# Create token
rules.add_perm(
    'tokens.create',
    rules.is_authenticated & pr_rules.is_site_writable & can_create_token,
)

# Delete token
rules.add_perm(
    'tokens.delete', rules.is_authenticated & pr_rules.is_site_writable
)
