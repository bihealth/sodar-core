import random
import string

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from projectroles.constants import get_sodar_constants
from projectroles.plugins import get_active_plugins

# Settings
SECRET_LENGTH = getattr(settings, 'PROJECTROLES_SECRET_LENGTH', 32)
INVITE_EXPIRY_DAYS = settings.PROJECTROLES_INVITE_EXPIRY_DAYS

# SODAR constants
SODAR_CONSTANTS = get_sodar_constants()

# Local constants
SIDEBAR_ICON_MIN_SIZE = 18
SIDEBAR_ICON_MAX_SIZE = 42
ROLE_URLS = [
    'roles',
    'role_create',
    'role_update',
    'role_delete',
    'invites',
    'invite_create',
    'invite_resend',
    'invite_revoke',
]


def get_display_name(key, title=False, count=1, plural=False):
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


def get_user_display_name(user, inc_user=False):
    """
    Return full name of user for displaying.

    :param user: User object
    :param inc_user: Include user name if true (boolean)
    :return: String
    """
    if user.name != '':
        return user.name + (' (' + user.username + ')' if inc_user else '')
    # If full name can't be found, return username
    return user.username


def build_secret(length=SECRET_LENGTH):
    """
    Return secret string for e.g. public URLs.

    :param length: Length of string if specified, default value from settings
    :return: Randomized secret (string)
    """
    length = int(length) if int(length) <= 255 else 255
    return ''.join(
        random.SystemRandom().choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )


def build_invite_url(invite, request):
    """
    Return invite URL for a project invitation.

    :param invite: ProjectInvite object
    :param request: HTTP request
    :return: URL (string)
    """
    return request.build_absolute_uri(
        reverse('projectroles:invite_accept', kwargs={'secret': invite.secret})
    )


def get_expiry_date():
    """
    Return expiry date based on current date + INVITE_EXPIRY_DAYS

    :return: DateTime object
    """
    return timezone.now() + timezone.timedelta(days=INVITE_EXPIRY_DAYS)


def get_app_names():
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


class SidebarContent:
    """Class for generating sidebar content for the site"""

    def _is_active(self, request, link_names=None):
        """Check if current URL is active in the sidebar."""
        # HACK: Avoid circular import
        from projectroles.urls import urlpatterns

        if request.resolver_match.app_name != 'projectroles':
            return False
        url_name = request.resolver_match.url_name
        if url_name in [u.name for u in urlpatterns]:
            if link_names:
                if not isinstance(link_names, list):
                    link_names = [link_names]
                if url_name not in link_names:
                    return False
            return True
        return False

    def _is_active_plugin(self, app_plugin, app_name, url_name):
        """
        Check if current URL is active in the sidebar for a specific app plugin.
        """
        if app_plugin.name.startswith(app_name) and url_name in [
            u.name for u in getattr(app_plugin, 'urls', [])
        ]:
            return True
        # HACK for remote site views, see issue #1336
        if (
            app_name == 'projectroles'
            and app_plugin.name == 'remotesites'
            and url_name.startswith('remote_')
        ):
            return True
        return False

    def _is_app_visible(self, plugin, project, user):
        """Check if app should be visible for user in a specific project."""
        can_view_app = user.has_perm(plugin.app_permission, project)
        app_hidden = False
        if plugin.name in getattr(
            settings, 'PROJECTROLES_HIDE_PROJECT_APPS', []
        ):
            app_hidden = True
        if (
            can_view_app
            and not app_hidden
            and (
                project.type == SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
                or plugin.category_enable
            )
        ):
            return True
        return False

    def _allow_project_creation(self):
        """Check whether creating a project is allowed on the site."""
        if (
            settings.PROJECTROLES_SITE_MODE
            == SODAR_CONSTANTS['SITE_MODE_TARGET']
            and not settings.PROJECTROLES_TARGET_CREATE
        ):
            return False
        return True

    def get_sidebar_links(self, request, project=None):
        """Return sidebar links based on the current project and user."""
        links = []
        # Add project related links
        if project:
            # Add project overview link
            links.append(
                {
                    'name': 'project-detail',
                    'url': reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    'label': 'Project<br />Overview',
                    'icon': (
                        'mdi:rhombus-split'
                        if project.type
                        == SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
                        else 'mdi:cube'
                    ),
                    'active': self._is_active(request, 'detail'),
                }
            )
            # Add app plugins links
            app_plugins = get_active_plugins()
            for plugin in app_plugins:
                if self._is_app_visible(plugin, project, request.user):
                    links.append(
                        {
                            'name': "app-plugin-" + plugin.name,
                            'url': reverse(
                                plugin.entry_point_url_id,
                                kwargs={'project': project.sodar_uuid},
                            ),
                            'label': '<br />'.join(plugin.title.split(' ')),
                            'icon': plugin.icon,
                            'active': self._is_active_plugin(
                                plugin,
                                request.resolver_match.app_name,
                                request.resolver_match.url_name,
                            ),
                        }
                    )
            # Add role editing link
            if request.user.has_perm(
                'projectroles.view_project_roles', project
            ):
                links.append(
                    {
                        'name': 'project-roles',
                        'url': reverse(
                            'projectroles:roles',
                            kwargs={'project': project.sodar_uuid},
                        ),
                        'label': 'Members',
                        'icon': 'mdi:account-multiple',
                        'active': self._is_active(request, ROLE_URLS),
                    }
                )
            # Add project update link
            if request.user.has_perm('projectroles.update_project', project):
                links.append(
                    {
                        'name': 'project-update',
                        'url': reverse(
                            'projectroles:update',
                            kwargs={'project': project.sodar_uuid},
                        ),
                        'label': 'Update<br />Project',
                        'icon': 'mdi:lead-pencil',
                        'active': self._is_active(request, 'update'),
                    }
                )

        # Add project and category creation links
        if (
            project
            and project.type == SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
            and request.user.has_perm('projectroles.create_project', project)
            and self._allow_project_creation()
            and not project.is_remote()
        ):
            links.append(
                {
                    'name': 'project-create',
                    'url': reverse(
                        'projectroles:create',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    'label': 'Create<br />Project or<br />Category',
                    'icon': 'mdi:plus-thick',
                    'active': self._is_active(request, 'create'),
                }
            )
        elif (
            getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False)
            and request.user.is_superuser
        ):
            links.append(
                {
                    'name': 'project-create',
                    'url': reverse('projectroles:create'),
                    'label': 'Create<br />Project',
                    'icon': 'mdi:plus-thick',
                    'active': self._is_active(request, 'create'),
                }
            )
        elif (
            (
                request.resolver_match.url_name == 'home'
                or request.resolver_match.app_name == 'projectroles'
                and not project
            )
            and request.user.has_perm('projectroles.create_project')
            and self._allow_project_creation()
        ):
            links.append(
                {
                    'name': 'home-project-create',
                    'url': reverse('projectroles:create'),
                    'label': 'Create<br />Category',
                    'icon': 'mdi:plus-thick',
                    'active': self._is_active(request, 'create'),
                }
            )
        return links
