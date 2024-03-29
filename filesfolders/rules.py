import rules

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates


# Predicates -------------------------------------------------------------


# If we need to assign new predicates, we do it here


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------


# Allow viewing data in project
rules.add_perm(
    'filesfolders.view_data',
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow adding data to project
rules.add_perm(
    'filesfolders.add_data',
    pr_rules.can_modify_project_data
    & (
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
    ),
)

# Allow updating own data in project
rules.add_perm(
    'filesfolders.update_data_own',
    pr_rules.can_modify_project_data
    & (
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
    ),
)

# Allow updating all data in project
rules.add_perm(
    'filesfolders.update_data_all',
    pr_rules.can_modify_project_data
    & (pr_rules.is_project_owner | pr_rules.is_project_delegate),
)

# Allow sharing public temporary URLs
rules.add_perm(
    'filesfolders.share_public_link',
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)
