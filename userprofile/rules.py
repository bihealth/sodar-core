import rules

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates


# Predicates -------------------------------------------------------------


@rules.predicate
def can_delete_email(user, obj):
    return obj.user == user


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
