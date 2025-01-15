"""Permissions for the tokens app"""

import rules

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates


# View tokens list
rules.add_perm('tokens.view_list', rules.is_authenticated)

# Create token
rules.add_perm(
    'tokens.create', rules.is_authenticated & pr_rules.is_site_writable
)

# Delete token
rules.add_perm(
    'tokens.delete', rules.is_authenticated & pr_rules.is_site_writable
)
