"""App links retrieval API for projectroles views"""

from typing import Any, Optional

from django.conf import settings
from django.urls import reverse

from projectroles.models import Project, SODARUser, SODAR_CONSTANTS
from projectroles.plugins import PluginAPI
from projectroles.utils import get_display_name


plugin_api = PluginAPI()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']

# Local constants
APP_NAME = 'projectroles'
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


class AppLinkAPI:
    """API for application link retrieval for UI and Ajax views"""

    @classmethod
    def _is_active_projectroles(
        cls,
        app_name: Optional[str] = None,
        url_name: Optional[str] = None,
        link_names: Optional[list[str]] = None,
    ) -> bool:
        """
        Check if current URL is active under the projectroles app.

        :param app_name: String or None
        :param url_name: String or None
        :param link_names: List of strings or None
        """
        if not app_name and not url_name:
            return False
        # HACK: Avoid circular import
        from projectroles.urls import urlpatterns

        if app_name != APP_NAME:
            return False
        return url_name in [u.name for u in urlpatterns] and (
            not link_names or url_name in link_names
        )

    @classmethod
    def _is_active_plugin(
        cls,
        app_plugin: Any,
        app_name: Optional[str] = None,
        url_name: Optional[str] = None,
    ) -> bool:
        """Check if current URL is active for a specific app plugin"""
        if not app_name and not url_name:
            return False
        if app_plugin.name.startswith(app_name) and (
            not url_name
            or url_name in [u.name for u in getattr(app_plugin, 'urls', [])]
        ):
            return True
        # Remote site views, see issue #1336
        if (
            app_name == APP_NAME
            and app_plugin.name == 'remotesites'
            and url_name.startswith('remote_')
        ):
            return True
        # Site app settings view
        if (
            app_name == APP_NAME
            and app_plugin.name == 'siteappsettings'
            and url_name == 'site_app_settings'
        ):
            return True
        return False

    @classmethod
    def _is_app_visible(
        cls, plugin: Any, project: Project, user: SODARUser
    ) -> bool:
        """Check if app should be visible for user in a specific project"""
        can_view_app = user.has_perm(plugin.app_permission, project)
        app_hidden = False
        if plugin.name in getattr(
            settings, 'PROJECTROLES_HIDE_PROJECT_APPS', []
        ):
            app_hidden = True
        if (
            can_view_app
            and not app_hidden
            and (project.is_project() or plugin.category_enable)
        ):
            return True
        return False

    @classmethod
    def _allow_project_creation(cls) -> bool:
        """Check whether creating a project is allowed on the site"""
        if (
            settings.PROJECTROLES_SITE_MODE
            == SODAR_CONSTANTS['SITE_MODE_TARGET']
            and not settings.PROJECTROLES_TARGET_CREATE
        ):
            return False
        return True

    def get_project_links(
        self,
        user: SODARUser,
        project: Optional[Project] = None,
        app_name: Optional[str] = None,
        url_name: Optional[str] = None,
    ) -> list[dict]:
        """
        Return project links based on the current project and user.

        :param user: User object
        :param project: Project object or None
        :param app_name: App name string or None
        :param url_name: URL name string or None
        :return: List of dicts
        """
        ret = []
        pr_display = get_display_name(PROJECT_TYPE_PROJECT, title=True)
        cat_display = get_display_name(PROJECT_TYPE_CATEGORY, title=True)

        # Add project related links
        if project:
            current_display = get_display_name(project.type, title=True)
            # Add project overview link
            ret.append(
                {
                    'name': 'project-detail',
                    'url': reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    'label': f'{current_display} Overview',
                    'icon': (
                        'mdi:rhombus-split'
                        if project.is_category()
                        else 'mdi:cube'
                    ),
                    'active': self._is_active_projectroles(
                        link_names=['detail'],
                        app_name=app_name,
                        url_name=url_name,
                    ),
                }
            )
            # Add app plugins links
            app_plugins = plugin_api.get_active_plugins(custom_order=True)
            for plugin in app_plugins:
                if self._is_app_visible(plugin, project, user):
                    ret.append(
                        {
                            'name': "app-plugin-" + plugin.name,
                            'url': reverse(
                                plugin.entry_point_url_id,
                                kwargs={'project': project.sodar_uuid},
                            ),
                            'label': ' '.join(plugin.title.split(' ')),
                            'icon': plugin.icon,
                            'active': self._is_active_plugin(
                                plugin, app_name=app_name, url_name=url_name
                            ),
                        }
                    )
            # Add role editing link
            if user.has_perm('projectroles.view_project_roles', project):
                ret.append(
                    {
                        'name': 'project-roles',
                        'url': reverse(
                            'projectroles:roles',
                            kwargs={'project': project.sodar_uuid},
                        ),
                        'label': 'Members',
                        'icon': 'mdi:account-multiple',
                        'active': self._is_active_projectroles(
                            link_names=ROLE_URLS,
                            app_name=app_name,
                            url_name=url_name,
                        ),
                    }
                )
            # Add project update link
            if user.has_perm('projectroles.update_project', project):
                ret.append(
                    {
                        'name': 'project-update',
                        'url': reverse(
                            'projectroles:update',
                            kwargs={'project': project.sodar_uuid},
                        ),
                        'label': f'Update {current_display}',
                        'icon': 'mdi:lead-pencil',
                        'active': self._is_active_projectroles(
                            link_names=['update'],
                            app_name=app_name,
                            url_name=url_name,
                        ),
                    }
                )

        # Add project/category creation link
        allow_create = self._allow_project_creation()
        create_active = self._is_active_projectroles(
            link_names=['create'], app_name=app_name, url_name=url_name
        )
        link = {
            'name': 'project-create',
            'icon': 'mdi:plus-thick',
            'active': create_active,
        }
        if (
            project
            and project.is_category()
            and user.has_perm('projectroles.create_project', project)
            and allow_create
            and not project.is_remote()
        ):
            link['url'] = reverse(
                'projectroles:create',
                kwargs={'project': project.sodar_uuid},
            )
            link['label'] = f'Create {pr_display} or {cat_display}'
            ret.append(link)
        elif (
            (url_name == 'home' or app_name == APP_NAME and not project)
            and user.has_perm('projectroles.create_project')
            and allow_create
        ):
            link['name'] = 'home-project-create'
            link['url'] = reverse('projectroles:create')
            link['label'] = f'Create {cat_display}'
            ret.append(link)
        elif (
            getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False)
            and user.is_superuser
        ):
            link['url'] = reverse('projectroles:create')
            link['label'] = f'Create {pr_display}'
            ret.append(link)
        return ret

    def get_user_links(
        self,
        user: SODARUser,
        app_name: Optional[str] = None,
        url_name: Optional[str] = None,
    ) -> list[dict]:
        """
        Return user links for the user dropdown.

        :param user: SODARUser object
        :param app_name: App name string or None
        :param url_name: URL name string or None
        """
        ret = []
        # Add site-wide apps links
        site_apps = plugin_api.get_active_plugins('site_app')
        for app in site_apps:
            if not app.app_permission or user.has_perm(app.app_permission):
                ret.append(
                    {
                        'name': app.name,
                        'url': reverse(app.entry_point_url_id),
                        'label': app.title,
                        'icon': app.icon,
                        'active': self._is_active_plugin(
                            app, app_name=app_name, url_name=url_name
                        ),
                    }
                )
        # Add admin link
        if user.is_superuser:
            ret.append(
                {
                    'name': 'admin',
                    'url': None,
                    'label': 'Django Admin',
                    'icon': 'mdi:cogs',
                    'active': False,
                }
            )
        # Add log out / sign in link
        if user.is_authenticated:
            ret.append(
                {
                    'name': 'sign-out',
                    'url': reverse('logout'),
                    'label': 'Logout',
                    'icon': 'mdi:logout-variant',
                    'active': False,
                }
            )
        elif not getattr(settings, 'PROJECTROLES_KIOSK_MODE', False):
            ret.append(
                {
                    'name': 'sign-in',
                    'url': reverse('login'),
                    'label': 'Login',
                    'icon': 'mdi:login-variant',
                    'active': False,
                }
            )
        return ret
