"""Ajax API views for the projectroles app"""

import logging

from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse

from dal import autocomplete

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rules.contrib.views import PermissionRequiredMixin

from projectroles.app_links import AppLinkAPI
from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    RoleAssignment,
    RemoteProject,
    AppSetting,
    SODARUser,
    SODAR_CONSTANTS,
    CAT_DELIMITER,
    ROLE_RANKING,
)
from projectroles.plugins import (
    ProjectAppPluginPoint,
    PluginAPI,
    PluginCategoryStatistic,
)
from projectroles.utils import get_display_name
from projectroles.views import ProjectAccessMixin, User
from projectroles.views_api import (
    SODARAPIProjectPermission,
    CurrentUserRetrieveAPIView,
)


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
plugin_api = PluginAPI()


# SODAR consants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_FINDER = SODAR_CONSTANTS['PROJECT_ROLE_FINDER']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']

# Local constants
APP_NAME = 'projectroles'
CAT_STAT_ATTRS = ['title', 'value', 'unit', 'description', 'icon']


# Base Classes and Mixins ------------------------------------------------------


class SODARBaseAjaxMixin:
    """
    Base Ajax mixin with permission class retrieval. To be used if another base
    class instead of SODARBaseAjaxView is needed.

    The allow_anonymous property can be used to control whether anonymous users
    should access an Ajax view when PROJECTROLES_ALLOW_ANONYMOUS==True.
    """

    allow_anonymous = False
    authentication_classes = [SessionAuthentication]
    renderer_classes = [JSONRenderer]
    schema = None

    @property
    def permission_classes(self):
        if self.allow_anonymous and getattr(
            settings,
            'PROJECTROLES_ALLOW_ANONYMOUS',
            False,
        ):
            return [AllowAny]
        return [IsAuthenticated]


class SODARBaseAjaxView(SODARBaseAjaxMixin, APIView):
    """
    Base Ajax view with Django session authentication.

    No permission classes or mixins used, you will have to supply your own if
    using this class directly.
    """


class SODARBasePermissionAjaxView(PermissionRequiredMixin, SODARBaseAjaxView):
    """
    Base Ajax view with permission checks, to be used e.g. in site apps with no
    project context.

    User-based perms such as is_superuser can be used with this class.
    """

    def handle_no_permission(self):
        """Override handle_no_permission() to provide 403"""
        return HttpResponseForbidden()


class SODARBaseProjectAjaxView(ProjectAccessMixin, SODARBaseAjaxView):
    """Base Ajax view with SODAR project permission checks"""

    permission_classes = [SODARAPIProjectPermission]


# Projectroles Ajax Views ------------------------------------------------------


class ProjectListAjaxView(SODARBaseAjaxView):
    """View to retrieve project list entries from the client"""

    allow_anonymous = True

    @classmethod
    def _get_projects(
        cls,
        user: SODARUser,
        public_stat_cats: list[Project],
        parent: Optional[Project] = None,
    ) -> list[Project]:
        """
        Return a flat list of categories and projects the user can view.

        :param user: User for which the projects are visible
        :param public_stat_cats: List of Project objects with
                                 category_public_stats enabled
        :param parent: Project object of type CATEGORY or None
        """
        project_list = (
            Project.objects.all()
            .select_related('parent')
            .order_by('full_title')
        )
        # Filter out parents
        parent_prefix = parent.full_title + CAT_DELIMITER if parent else None
        if parent_prefix:
            project_list = project_list.filter(
                full_title__startswith=parent_prefix
            )
        # Get public stats cat UUIDs
        stats_uuids = [p.sodar_uuid for p in public_stat_cats]
        # Filter by user type
        if user.is_anonymous:
            project_list = project_list.filter(
                Q(public_access__isnull=False)
                | Q(has_public_children=True)
                | Q(sodar_uuid__in=stats_uuids)
            )
        elif not user.is_superuser:
            # Quick and dirty filtering for inheritance using full_title
            # role_owner = Role.objects.filter(name=PROJECT_ROLE_OWNER).first()
            role_cats = [
                r.project.full_title + CAT_DELIMITER
                for r in RoleAssignment.objects.filter(
                    project__type=PROJECT_TYPE_CATEGORY,
                    user=user,
                )
            ]
            # NOTE: Not using get_role() here as that would exclude finder role
            project_list = [
                p
                for p in project_list
                if p.public_access
                or p.has_public_children
                or any(p.full_title.startswith(c) for c in role_cats)
                or p.local_roles.filter(user=user).count() > 0
                or p in public_stat_cats
            ]
        if user.is_superuser:
            return project_list  # No further querying needed for superuser

        # Populate final list with parent categories for non-superusers
        ret = []
        prev_parent = None
        for p in project_list:
            ret.append(p)
            p_parent = p.parent
            if p_parent == prev_parent or not p_parent or p_parent in ret:
                continue  # Skip already collected parents
            while p_parent and p_parent != parent:
                if p_parent not in ret:
                    ret.append(p_parent)
                p_parent = p_parent.parent
            prev_parent = p.parent
        # Sort by full title
        return sorted(ret, key=lambda x: x.full_title.lower())

    @classmethod
    def _get_access(
        cls,
        project: Project,
        user: SODARUser,
        finder_cats: list[str],
        depth: int,
        blocked_projects: list[Project],
        public_stat_cats: list[Project],
    ) -> bool:
        """
        Return whether user has access to a project for the project list.

        :param project: Project object
        :param user: SODARUser object
        :param finder_cats: List of category names where user has finder role
        :param depth: Project depth in category structure (int)
        :param blocked_projects: List of projects with blocked access
        :param public_stat_cats: List of categories with public stats access
        :return: Boolean
        """
        # Top level categories with public stats are shown to everybody
        if project.is_category() and project in public_stat_cats:
            return True
        # Disable categories for anonymous users if anonymous access is enabled
        if project.is_category() and not user.is_authenticated:
            return False
        # Disable access for non-superuser in blocked project
        if project in blocked_projects and not user.is_superuser:
            return False
        # Cases which are always true if we get this far
        if (
            user.is_superuser
            or (user.is_authenticated and project.is_category())
            or project.public_access
        ):
            return True
        # If user has finder role in a parent category, we need to check role
        p_ft = project.full_title
        if (
            finder_cats
            and depth > 0
            and any([p_ft.startswith(c + CAT_DELIMITER) for c in finder_cats])
        ):
            for i in range(0, depth + 1):
                c = ' / '.join(project.full_title.split(' / ')[:i])
                if c in finder_cats:
                    role_as = project.get_role(user)
                    if (
                        role_as
                        and role_as.role.rank
                        < ROLE_RANKING[PROJECT_ROLE_FINDER]
                    ):
                        return True
            return False
        return True

    def get(self, request, *args, **kwargs):
        parent_uuid = request.GET.get('parent', None)
        parent = (
            Project.objects.get(sodar_uuid=parent_uuid) if parent_uuid else None
        )
        if parent and parent.is_project():
            return Response(
                {
                    'detail': 'Querying for a project list under a project is '
                    'not allowed'
                },
                status=400,
            )
        public_stat_cats = [
            s.project
            for s in AppSetting.objects.filter(
                app_plugin=None, name='category_public_stats', value='1'
            )
        ]

        projects = self._get_projects(request.user, public_stat_cats, parent)
        # NOTE: Generally, manipulating AppSetting objects directly is not
        #       advised, but in this case it's pertinent for optimization :)
        blocked_projects = [
            s.project
            for s in AppSetting.objects.filter(
                app_plugin=None,
                name='project_access_block',
                value='1',
            )
        ]
        starred_projects = []
        finder_cats = []
        if request.user.is_authenticated:
            starred_projects = [
                s.project
                for s in AppSetting.objects.filter(
                    app_plugin=None,
                    name='project_star',
                    user=request.user,
                    value='1',
                )
            ]
            finder_cats = [
                a.project.full_title
                for a in RoleAssignment.objects.filter(
                    project__type=PROJECT_TYPE_CATEGORY,
                    role__rank=ROLE_RANKING[PROJECT_ROLE_FINDER],
                    user=request.user,
                )
            ]
        full_title_idx = (
            len(parent.full_title) + len(CAT_DELIMITER) if parent else 0
        )

        ret_projects = []
        for p in projects:
            p_depth = p.get_depth()
            p_access = self._get_access(
                p,
                request.user,
                finder_cats,
                p_depth,
                blocked_projects,
                public_stat_cats,
            )
            p_finder_url = None
            if not p_access and p.parent:
                p_finder_url = reverse(
                    'projectroles:roles',
                    kwargs={'project': p.parent.sodar_uuid},
                )
            p_stats = p.is_category() and p in public_stat_cats
            rp = {
                'type': p.type,
                'full_title': p.full_title[full_title_idx:],
                'public_access': p.public_access is not None,
                'public_stats': p_stats,
                'archive': p.archive,
                'remote': p.is_remote(),
                'revoked': p.is_revoked(),
                'starred': p in starred_projects,
                'access': p_access,
                'finder_url': p_finder_url,
                'uuid': str(p.sodar_uuid),
            }
            if p.is_project():
                rp['blocked'] = p in blocked_projects
            ret_projects.append(rp)
        ret = {
            'projects': ret_projects,
            'parent_depth': parent.get_depth() + 1 if parent else 0,
            'messages': {},
            'user': {
                'superuser': request.user.is_superuser,
                'highlight': app_settings.get(
                    APP_NAME, 'project_list_highlight', user=request.user
                ),
            },
        }

        if len(ret['projects']) == 0:
            np_prefix = 'No {} '.format(
                get_display_name(PROJECT_TYPE_PROJECT, plural=True)
            )
            if parent:
                np_msg = 'or {} available under this {}.'.format(
                    get_display_name(PROJECT_TYPE_CATEGORY, plural=True),
                    get_display_name(PROJECT_TYPE_CATEGORY),
                )
            elif not request.user.is_superuser:
                np_msg = (
                    'available: access must be granted by {} personnel or a '
                    'superuser.'.format(get_display_name(PROJECT_TYPE_PROJECT))
                )
            else:
                np_msg = 'have been created.'
            ret['messages']['no_projects'] = np_prefix + np_msg
        return Response(ret, status=200)


class ProjectListColumnAjaxView(SODARBaseAjaxView):
    """View to retrieve project list extra column data from the client"""

    allow_anonymous = True

    @classmethod
    def _get_column_value(
        cls,
        app_plugin: ProjectAppPluginPoint,
        column_id: str,
        project: Project,
        user: SODARUser,
    ) -> dict:
        """
        Return project list extra column value for a specific project and
        column.

        :param app_plugin: Project app plugin object
        :param column_id: Column ID string corresponding to
                          plugin.project_list_columns (string)
        :param project: Project object
        :param user: SODARUser object
        :return: Dict
        """
        try:
            val = app_plugin.get_project_list_value(column_id, project, user)
            return {'html': str(val) if val is not None else ''}
        except Exception as ex:
            logger.error(
                'Exception in {}.get_project_list_value(): "{}" '
                '(column_id={}; project={}; user={})'.format(
                    app_plugin.name,
                    ex,
                    column_id,
                    project.sodar_uuid,
                    user.username,
                )
            )
            return {'html': ''}

    def post(self, request, *args, **kwargs):
        ret = {}
        projects = Project.objects.filter(
            type=PROJECT_TYPE_PROJECT,
            sodar_uuid__in=request.data.get('projects'),
        )
        plugins = [
            ap
            for ap in plugin_api.get_active_plugins(plugin_type='project_app')
            if ap.project_list_columns
            and (
                ap.name != 'filesfolders'
                or getattr(settings, 'FILESFOLDERS_SHOW_LIST_COLUMNS', False)
            )
        ]
        for project in projects:
            # Only provide results for projects in which user has access
            if not request.user.has_perm('projectroles.view_project', project):
                logger.error(
                    f'ProjectListColumnAjaxView: User {request.user.username} '
                    f'not authorized to view project {project.get_log_title()}'
                )
                continue
            p_uuid = str(project.sodar_uuid)
            ret[p_uuid] = {}
            for app_plugin in plugins:
                ret[p_uuid][app_plugin.name] = {}
                for k, v in app_plugin.project_list_columns.items():
                    ret[p_uuid][app_plugin.name][k] = self._get_column_value(
                        app_plugin, k, project, request.user
                    )
        return Response(ret, status=200)


class ProjectListRoleAjaxView(SODARBaseAjaxView):
    """View to retrieve project list role data from the client"""

    allow_anonymous = True

    @classmethod
    def _get_user_role(cls, project: Project, user: SODARUser) -> dict:
        """Return user role for project"""
        ret = {'name': None, 'class': None}
        role_as = None
        if user.is_authenticated:
            role_as = project.get_role(user)
            if role_as:
                ret['name'] = role_as.role.name.split(' ')[1].capitalize()
        if project.public_access and not role_as:
            ret['name'] = project.public_access.name.split(' ')[1].capitalize()
        if not ret['name']:
            ret['name'] = 'N/A'
            ret['class'] = 'text-muted'
        return ret

    def post(self, request, *args, **kwargs):
        ret = {}
        projects = Project.objects.filter(
            sodar_uuid__in=request.data.get('projects'),
        )
        for project in projects:
            # Only provide results for projects in which user has access
            if not request.user.has_perm('projectroles.view_project', project):
                logger.error(
                    f'ProjectListRoleAjaxView: User {request.user.username} '
                    f'not authorized to view project {project.get_log_title()}'
                )
                continue
            ret[str(project.sodar_uuid)] = self._get_user_role(
                project, request.user
            )
        return Response(ret, status=200)


class CategoryStatisticsAjaxView(SODARBaseAjaxView):
    """View for retrieving category statistics"""

    allow_anonymous = True

    @classmethod
    def _get_pr_category_stats(
        cls, category: Project
    ) -> list[PluginCategoryStatistic]:
        """
        Return projectroles stats for category.

        :param category: Project object of CATEGORY type
        :return: List of PluginCategoryStatistic objects
        """
        ret = []
        # Project count
        title = get_display_name(PROJECT_TYPE_PROJECT, title=True, plural=True)
        val = Project.objects.filter(
            type=PROJECT_TYPE_PROJECT,
            full_title__startswith=category.full_title + CAT_DELIMITER,
        ).count()
        desc = '{} in this {}'.format(
            get_display_name(PROJECT_TYPE_PROJECT, plural=True, title=True),
            get_display_name(PROJECT_TYPE_CATEGORY),
        )
        ret.append(
            PluginCategoryStatistic(
                plugin=None,
                title=title,
                value=val,
                description=desc,
                icon='mdi:cube',
            )
        )
        # User count
        children = Project.objects.filter(
            full_title__startswith=category.full_title + CAT_DELIMITER,
        )
        title = 'Members'
        # NOTE: We need order_by() for distinct() to work
        val = (
            RoleAssignment.objects.filter(
                project__in=[category] + list(children)
            )
            .values_list('user', flat=True)
            .distinct()
            .order_by()
            .count()
        )
        desc = 'Users with roles in this {}'.format(
            get_display_name(PROJECT_TYPE_CATEGORY)
        )
        ret.append(
            PluginCategoryStatistic(
                plugin=None,
                title=title,
                value=val,
                description=desc,
                icon='mdi:account-multiple',
            )
        )
        return ret

    def get(self, request, *args, **kwargs):
        project = Project.objects.filter(
            sodar_uuid=kwargs.get('project')
        ).first()
        if not project:
            return Response({'detail': 'Project not found'}, status=404)
        if project.is_project():
            return Response(
                {'detail': 'Only allowed for categories'}, status=403
            )
        if (
            not request.user.is_superuser
            and request.user.is_authenticated
            and not request.user.has_perm('projectroles.view_project', project)
        ):
            return Response({'detail': 'Not authorized'}, status=403)
        if (
            request.user.is_anonymous
            and not project.has_public_children
            and not app_settings.get(
                APP_NAME, 'category_public_stats', project=project
            )
        ):
            return Response({'detail': 'Anonymous access denied'}, status=401)

        cat_stats = self._get_pr_category_stats(project)
        plugins = plugin_api.get_active_plugins(plugin_type='project_app')
        for p in plugins:
            try:
                cat_stats += p.get_category_stats(project)
            except Exception as ex:
                logger.error(
                    f'Exception calling get_category_stats() for plugin '
                    f'"{p.name}": {ex}'
                )
        ret = []
        for s in cat_stats:  # Convert objects to dicts
            ret.append({a: getattr(s, a) for a in CAT_STAT_ATTRS})
        return Response({'stats': ret}, status=200)


class ProjectStarringAjaxView(SODARBaseProjectAjaxView):
    """View to handle starring and unstarring a project"""

    permission_required = 'projectroles.star_project'

    def post(self, request, *args, **kwargs):
        # HACK: Manually refuse access to anonymous as this view is an exception
        if request.user.is_anonymous:
            return Response({'detail': 'Anonymous access denied'}, status=401)
        project = self.get_project()
        user = request.user
        project_star = app_settings.get(APP_NAME, 'project_star', project, user)
        value = False if project_star else True
        app_settings.set(
            plugin_name=APP_NAME,
            setting_name='project_star',
            value=value,
            project=project,
            user=user,
            validate=False,
        )
        return Response(1 if value else 0, status=200)


class HomeStarringAjaxView(SODARBaseAjaxView):
    """
    View to set default starred setting for user in HomeView project list.

    NOTE: Separate view needed as user is not allwoed to modify this setting
          via UserSettingSetAPIView
    """

    def post(self, request, *args, **kwargs):
        value = bool(int(request.data.get('value')))
        user = request.user
        starred_default = app_settings.get(
            APP_NAME, 'project_list_home_starred', user=user
        )
        if value != starred_default:
            app_settings.set(
                plugin_name=APP_NAME,
                setting_name='project_list_home_starred',
                value=value,
                user=user,
            )
        return Response(1 if value else 0, status=200)


class RemoteProjectAccessAjaxView(SODARBaseProjectAjaxView):
    """View to check whether a remote project has been accessed by sync"""

    permission_required = 'projectroles.view_project'

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        rp_uuids = request.GET.getlist('rp')
        ret = {}
        for u in rp_uuids:
            rp = RemoteProject.objects.filter(sodar_uuid=u).first()
            if not rp:
                return Response(
                    {'detail': 'RemoteProject not found'}, status=404
                )
            if (
                rp.project_uuid != project.sodar_uuid
                or rp.site.mode == SITE_MODE_SOURCE
            ):
                return Response({'detail': 'Invalid RemoteProject'}, status=400)
            ret[str(rp.sodar_uuid)] = rp.date_access is not None
        return Response(ret, status=200)


class SidebarContentAjaxView(SODARBaseProjectAjaxView):
    """
    Return sidebar and project dropdown links to be displayed in a client-side
    application. This can be used as an alternative to rendering server-side
    sidebar and project dropdonwn elements.

    All returned links are inactive by default. To get correct "active"
    attribute for each of the links, you must provide the app_name as GET
    parameter. The app_name refers to the current app name
    (request.resolver_match.app_name).

    Return data (for each link):

    - ``name``: Internal ID (string)
    - ``url``: View URL (string)
    - ``label``: Text label to be displayed for link (string)
    - ``icon``: Icon namespace and ID (string, example: "mdi:cube")
    - ``active``: Whether link is currently active (boolean)
    """

    permission_required = 'projectroles.view_project'

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        app_name = request.GET.get('app_name')
        # Get the content for the sidebar
        app_links = AppLinkAPI()
        sidebar_links = app_links.get_project_links(
            request.user, project, app_name=app_name
        )
        return JsonResponse({'links': sidebar_links})


class SiteReadOnlySettingAjaxView(SODARBaseAjaxView):
    """
    Return the current status of the site read-only mode setting.

    Return data:

    - ``site_read_only``: Boolean
    """

    allow_anonymous = True

    def get(self, request, *args, **kwargs):
        ret = app_settings.get(APP_NAME, 'site_read_only')
        return JsonResponse({'site_read_only': ret})


class CurrentUserRetrieveAjaxView(
    SODARBaseAjaxMixin, CurrentUserRetrieveAPIView
):
    """
    Return information of the requesting user for Ajax requests.
    """


class UserDropdownContentAjaxView(SODARBaseAjaxView):
    """
    Return user dropdown links to be displayed in a client-side application.
    This can be used as an alternative to rendering the server-side dropdown.

    All returned links are inactive by default. To get correct "active"
    attribute for each of the links, you must provide the app_name as GET
    parameter. The app_name refers to the current app name
    (request.resolver_match.app_name).

    Return data (for each link):

    - ``name``: Internal ID (string)
    - ``url``: View URL (string)
    - ``label``: Text label to be displayed for link (string)
    - ``icon``: Icon namespace and ID (string, example: "mdi:cube")
    - ``active``: Whether link is currently active (boolean)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        app_name = request.GET.get('app_name')
        # Get the content for the user dropdown
        app_links = AppLinkAPI()
        user_dropdown_links = app_links.get_user_links(
            request.user, app_name=app_name
        )
        return JsonResponse({'links': user_dropdown_links})


class UserAutocompleteAjaxView(autocomplete.Select2QuerySetView):
    """User autocompletion widget view"""

    def get_queryset(self):
        """
        Get a User queryset for SODARUserAutocompleteWidget.

        Optional values in self.forwarded:
        - "project": project UUID
        - "scope": string for expected scope (all/project/project_exclude)
        - "exclude": list of explicit User.sodar_uuid to exclude from queryset
        """
        current_user = self.request.user
        project_uuid = self.forwarded.get('project', None)
        exclude_uuids = self.forwarded.get('exclude', None)
        scope = self.forwarded.get('scope', 'all')
        qs = User.objects.exclude(is_active=False)

        # If project UUID is given, only show users that are in the project
        if scope in ['project', 'project_exclude'] and project_uuid:
            project = Project.objects.filter(sodar_uuid=project_uuid).first()
            # If user has no permission for the project, return None
            if not self.request.user.has_perm(
                'projectroles.view_project', project
            ):
                return User.objects.none()
            project_users = [a.user.pk for a in project.get_roles()]
            if scope == 'project':  # Limit choices to current project users
                qs = qs.filter(pk__in=project_users)
            elif scope == 'project_exclude':  # Exclude project users
                qs = qs.exclude(pk__in=project_users)

        # Exclude users in the system group unless local users are allowed
        allow_local = getattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS', False)
        if not allow_local and not current_user.is_superuser:
            qs = qs.exclude(groups__name=SYSTEM_USER_GROUP).exclude(
                groups__isnull=True
            )
        # Exclude UUIDs explicitly given
        if exclude_uuids:
            qs = qs.exclude(sodar_uuid__in=exclude_uuids)
        # Finally, filter by query
        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q)
                | Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
                | Q(name__icontains=self.q)
                | Q(email__icontains=self.q)
            )
        return qs.order_by('name')

    def get_result_label(self, user):
        """Display options with name, username and email address"""
        return user.get_form_label(email=True)

    def get_result_value(self, user):
        """Use sodar_uuid in the User model instead of pk"""
        return str(user.sodar_uuid)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        return super().get(request, *args, **kwargs)


class UserAutocompleteRedirectAjaxView(UserAutocompleteAjaxView):
    """
    SODARUserRedirectWidget view (user autocompletion) redirecting to
    the create invite page.
    """

    def get_create_option(self, context, q):
        """Form the correct email invite option to append to results"""
        validator = EmailValidator()
        display_create_option = False

        if self.create_field and q:
            page_obj = context.get('page_obj', None)
            if page_obj is None or page_obj.number == 1:
                # Only create invite if the email address is valid
                try:
                    validator(q)
                    display_create_option = True
                except ValidationError:
                    display_create_option = False
                # Prevent sending a duplicate invite
                existing_options = (
                    self.get_result_label(result).lower()
                    for result in context['object_list']
                )
                if q.lower() in existing_options:
                    display_create_option = False

        if display_create_option:
            create_option = {
                'id': q,
                'text': f'Send an invite to "{q}"',
                'create_id': True,
            }
            return [create_option]
        return []

    def post(self, request, *args, **kwargs):
        # Return JSON with redirect URL
        project_uuid = self.request.POST.get('project', None)
        project = Project.objects.filter(sodar_uuid=project_uuid).first()
        redirect_url = reverse(
            'projectroles:invite_create', kwargs={'project': project.sodar_uuid}
        )
        return JsonResponse({'success': True, 'redirect_url': redirect_url})
