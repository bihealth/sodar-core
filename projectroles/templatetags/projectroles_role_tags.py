"""Template tags for role management views in projectroles"""

from django import template

from projectroles.models import RoleAssignment, SODAR_CONSTANTS


register = template.Library()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']

# Local constants
ROLE_RANK_ICONS = {
    10: 'mdi:star',
    20: 'mdi:star-half-full',
    30: 'mdi:account',
}


@register.simple_tag
def get_role_icon(role):
    """Return the icon class for a Role"""
    keys = list(ROLE_RANK_ICONS.keys())
    key_idx = min(range(len(keys)), key=lambda i: abs(keys[i] - role.rank))
    return ROLE_RANK_ICONS[keys[key_idx]]


@register.simple_tag
def get_role_perms(project, user):
    """
    Return role perms to template as dict.

    :param project: Project object
    :param user: SODARUser object
    :return: Dict
    """
    return {
        'can_update_owner': user.has_perm(
            'projectroles.update_project_owner', project
        ),
        'can_update_delegate': user.has_perm(
            'projectroles.update_project_delegate', project
        ),
        'can_update_members': user.has_perm(
            'projectroles.update_project_members', project
        ),
        'can_invite': user.has_perm('projectroles.invite_users', project),
    }


@register.simple_tag
def display_role_buttons(project, role_as, perms):
    """Return True/False on whether role buttons can be displayed for role"""
    if (
        role_as.role.name == PROJECT_ROLE_OWNER
        and role_as.project == project
        and perms['can_update_owner']
    ):
        return True
    if (
        role_as.role.name == PROJECT_ROLE_DELEGATE
        and role_as.project == project
        and perms['can_update_delegate']
    ):
        return True
    if (
        role_as.role.name not in [PROJECT_ROLE_OWNER, PROJECT_ROLE_DELEGATE]
        and perms['can_update_members']
    ):
        return True
    return False


@register.simple_tag
def get_inactive_role(project, inherited_as):
    """
    Return inactive role assignment for inherited user if it exists.

    :param project: Project object
    :param inherited_as: RoleAssignment for inherited role
    :return: RoleAssignment object or None
    """
    local_as = RoleAssignment.objects.filter(
        project=project, user=inherited_as.user
    ).first()
    if local_as and local_as.role.rank > inherited_as.role.rank:
        return local_as
    return None
