"""UI views for the projectroles app"""

import json
import logging
import re

from ipaddress import ip_address, ip_network
from urllib.parse import unquote_plus, urlparse

from django.apps import apps
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import redirect
from django.urls import resolve, reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import (
    TemplateView,
    DetailView,
    UpdateView,
    CreateView,
    DeleteView,
    View,
)
from django.views.generic.edit import ModelFormMixin, FormView
from django.views.generic.detail import ContextMixin

from rules.contrib.views import PermissionRequiredMixin, redirect_to_login

from projectroles import email
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import (
    ProjectForm,
    RoleAssignmentForm,
    ProjectInviteForm,
    SiteAppSettingsForm,
    RemoteSiteForm,
    RoleAssignmentOwnerTransferForm,
    LocalUserForm,
)
from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    RemoteProject,
    SODAR_CONSTANTS,
    ROLE_RANKING,
)
from projectroles.plugins import (
    get_active_plugins,
    get_app_plugin,
    get_backend_api,
)
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.utils import get_display_name


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
User = auth.get_user_model()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_ROLE_FINDER = SODAR_CONSTANTS['PROJECT_ROLE_FINDER']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
REMOTE_LEVEL_NONE = SODAR_CONSTANTS['REMOTE_LEVEL_NONE']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
REMOTE_LEVEL_REVOKED = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
PROJECT_ACTION_CREATE = SODAR_CONSTANTS['PROJECT_ACTION_CREATE']
PROJECT_ACTION_UPDATE = SODAR_CONSTANTS['PROJECT_ACTION_UPDATE']

# Local constants
APP_NAME = 'projectroles'
SEND_EMAIL = settings.PROJECTROLES_SEND_EMAIL
LOGIN_MSG = 'Please log in.'
NO_AUTH_MSG = 'User not authorized for requested action.'
NO_AUTH_LOGIN_MSG = 'Authentication required, please log in.'
FORM_INVALID_MSG = 'Form submission failed, see the form for details.'
PROJECT_WELCOME_MSG = (
    'Welcome to {project_type} "{project_title}". You have been assigned the '
    'role of {role}.'
)
CAT_ARCHIVE_ERR_MSG = 'Setting archival is not allowed for {}.'.format(
    get_display_name(PROJECT_TYPE_CATEGORY, plural=True)
)
USER_PROFILE_UPDATE_MSG = 'User profile updated, please log in again.'
USER_PROFILE_LDAP_MSG = 'Profile editing not allowed for LDAP users.'
INVITE_NOT_FOUND_MSG = 'Invite not found.'
INVITE_LDAP_LOCAL_VIEW_MSG = (
    'Invite was issued for LDAP user, but local invite view was requested.'
)
INVITE_LOCAL_NOT_ALLOWED_MSG = 'Local users are not allowed.'

INVITE_LOGGED_IN_ACCEPT_MSG = (
    'Logged in user is not allowed to accept invites for other users.'
)
INVITE_USER_NOT_EQUAL_MSG = (
    'Invited user exists, but logged in user is not invited user.'
)
INVITE_USER_EXISTS_MSG = (
    'User with that email already exists. Please login to accept the invite.'
)
ROLE_CREATE_MSG = 'Membership granted with the role of "{role}".'
ROLE_UPDATE_MSG = 'Member role changed to "{role}".'
ROLE_DELETE_MSG = 'Your membership in this {project_type} has been removed.'
ROLE_LEAVE_MSG = 'Member {user_name} left the {project_type}.'
ROLE_LEAVE_INHERIT_MSG = 'Role inherited from parent {category_type}'
ROLE_LEAVE_OWNER_MSG = 'Owner role must be transferred to another user'
ROLE_LEAVE_REMOTE_MSG = (
    '{project_type} is remote, role must be changed on source site'
)
ROLE_FINDER_INFO = (
    'User can see nested {categories} and {projects}, but can not access them '
    'without having a role explicitly assigned.'
)
PROJECT_DELETE_MSG = (
    '{project_type} "{project_title}" deleted by user {user_name}.'
)
PROJECT_DELETE_CAT_ERR_MSG = (
    'Deletion not allowed for {project_type} with children. Delete the '
    'children before attempting deletion.'
)
PROJECT_DELETE_TARGET_ERR_MSG = (
    'Deletion not allowed for remote {project_type} with non-revoked access '
    'level. Revoke remote access on source site to enable deletion.'
)
PROJECT_DELETE_SOURCE_ERR_MSG = (
    'Non-revoked remotes of {project_type} found on target sites. Revoke '
    'access to the remotes to enable deletion.'
)
TARGET_CREATE_DISABLED_MSG = (
    'PROJECTROLES_TARGET_CREATE=False, creation not allowed.'
)
SITE_SETTING_UPDATE_MSG = 'Site app settings updated.'


# General UI view mixins -------------------------------------------------------


class LoginRequiredMixin(AccessMixin):
    """
    Override of Django LoginRequiredMixin to handle anonymous access and kiosk
    mode.
    """

    def is_login_required(self):
        if getattr(settings, 'PROJECTROLES_KIOSK_MODE', False) or getattr(
            settings, 'PROJECTROLES_ALLOW_ANONYMOUS', False
        ):
            return False
        return True

    def dispatch(self, request, *args, **kwargs):
        if self.is_login_required() and not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class LoggedInPermissionMixin(PermissionRequiredMixin):
    """
    Mixin for handling redirection for both unlogged users and authenticated
    users without permissions.
    """

    #: No permission message custom override
    no_perm_message = None

    #: No permission message Django messages level
    no_perm_message_level = 'error'

    def has_permission(self):
        """
        Override for this mixin also to work with admin users without a
        permission object.
        """
        if getattr(settings, 'PROJECTROLES_KIOSK_MODE', False):
            return True
        try:
            return super().has_permission()
        except AttributeError:
            if self.request.user.is_superuser:
                return True
        return False

    def add_no_perm_message(self):
        """
        Add Django in the UI if handle_no_permission() fails. This can be
        overridden to implement specific logic in a view if e.g. a different
        message should be displayed depending on the referring view.
        """
        level = self.no_perm_message_level.lower()
        msg_method = getattr(messages, level, None)
        if not msg_method:
            raise ValueError('Unknown message level "{}"'.format(level))
        if self.no_perm_message:
            msg = self.no_perm_message
        elif self.request.user.is_authenticated:
            msg = NO_AUTH_MSG
        else:
            msg = NO_AUTH_LOGIN_MSG
        msg_method(self.request, msg)

    def handle_no_permission(self):
        """
        Handle no permission and redirect user. If custom message is specified
        using self.login_message, it will be displayed.
        """
        self.add_no_perm_message()
        if self.request.user.is_authenticated:
            return redirect(reverse('home'))
        return redirect_to_login(self.request.get_full_path())


class ProjectAccessMixin:
    """Mixin for providing access to a Project object from request kwargs"""

    #: Model class to use for projects. Can be overridden by e.g. a proxy model
    project_class = Project

    def get_project(self, request=None, kwargs=None):
        """
        Return SODAR Project object based or None if not found, based on
        the current request and view kwargs. If arguments are not provided,
        uses self.request and/or self.kwargs.

        :param request: Request object (optional)
        :param kwargs: View kwargs (optional)
        :return: Object of project_class or None if not found
        """
        request = request or getattr(self, 'request')
        kwargs = kwargs or getattr(self, 'kwargs')
        if kwargs is None:
            raise ImproperlyConfigured('View kwargs are not accessible')

        # Project class object
        if 'project' in kwargs:
            return self.project_class.objects.filter(
                sodar_uuid=kwargs['project']
            ).first()

        # Other object types
        if not request:
            raise ImproperlyConfigured('Current HTTP request is not accessible')
        model = None
        uuid_val = None
        for k, v in kwargs.items():
            if not re.match(r'^[0-9a-f-]+$', str(v)):
                continue
            try:
                if '__' in k:  # Model from another app
                    ks = k.split('__')
                    model = apps.get_model(ks[0], ks[1])
                else:  # Model from the same app
                    app_name = resolve(request.path).app_name
                    if app_name.find('.') != -1:
                        app_name = app_name.split('.')[0]
                    model = apps.get_model(app_name, k)
                uuid_val = k
                break
            except LookupError:
                pass
        if not model:
            return None

        try:
            obj = model.objects.get(sodar_uuid=kwargs[uuid_val])
            if hasattr(obj, 'project'):
                return obj.project
            # Some objects may have a get_project() func instead of foreignkey
            elif hasattr(obj, 'get_project') and callable(
                getattr(obj, 'get_project', None)
            ):
                return obj.get_project()
        except model.DoesNotExist:
            return None


class ProjectPermissionMixin(PermissionRequiredMixin, ProjectAccessMixin):
    """
    Mixin for providing a Project object and queryset for permission
    checking.
    """

    def get_permission_object(self):
        return self.get_project()

    def has_permission(self):
        """Overrides for project permission access"""
        project = self.get_project()
        if not project:
            raise Http404

        # Override permissions for superuser, owner or delegate
        perm_override = (
            self.request.user.is_superuser
            or project.is_owner_or_delegate(self.request.user)
        )
        if not perm_override and app_settings.get(
            APP_NAME, 'ip_restrict', project
        ):
            for k in (
                'HTTP_X_FORWARDED_FOR',
                'X_FORWARDED_FOR',
                'FORWARDED',
                'REMOTE_ADDR',
            ):
                v = self.request.META.get(k)
                if v:
                    client_address = ip_address(v.split(',')[0])
                    break
            else:  # Can't fetch client ip address
                return False

            for record in app_settings.get(APP_NAME, 'ip_allowlist', project):
                if '/' in record:
                    if client_address in ip_network(record):
                        break
                elif client_address == ip_address(record):
                    break
            else:
                return False

        # Disable project app access for categories unless specifically enabled
        if project.type == PROJECT_TYPE_CATEGORY:
            request_url = resolve(self.request.get_full_path())
            if request_url.app_name != APP_NAME:
                app_plugin = get_app_plugin(request_url.app_name)
                if app_plugin and app_plugin.category_enable:
                    return True
                return False

        # Disable access for non-owner/delegate if remote project is revoked
        if project.is_revoked() and not perm_override:
            return False
        return super().has_permission()

    def get_queryset(self, *args, **kwargs):
        """
        Override get_queryset() to filter down to the currently selected object.
        """
        qs = super().get_queryset(*args, **kwargs)
        if qs.model == ProjectAccessMixin.project_class:
            return qs
        elif hasattr(qs.model, 'get_project_filter_key'):
            return qs.filter(
                **{qs.model.get_project_filter_key(): self.get_project()}
            )
        elif hasattr(qs.model, 'project') or hasattr(qs.model, 'get_project'):
            return qs.filter(project=self.get_project())
        raise AttributeError(
            'Model does not have "project" member, get_project() method or '
            'get_project_filter_key() method'
        )


class HTTPRefererMixin:
    """
    Mixin for updating a correct referer url in session cookie regardless of
    page reload.
    """

    def get(self, request, *args, **kwargs):
        if 'HTTP_REFERER' in request.META:
            referer = request.META['HTTP_REFERER']
            if (
                'real_referer' not in request.session
                or referer != request.build_absolute_uri()
            ):
                request.session['real_referer'] = referer
        return super().get(request, *args, **kwargs)


class PluginContextMixin(ContextMixin):
    """Mixin for adding plugin list to context data"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['app_plugins'] = get_active_plugins(
            plugin_type='project_app', custom_order=True
        )
        return context


class ProjectContextMixin(
    HTTPRefererMixin, PluginContextMixin, ProjectAccessMixin
):
    """
    Mixin for adding context data to Project base view and other views
    extending it. Includes HTTPRefererMixin for correct referer URL.
    """

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # Project
        if hasattr(self, 'object') and isinstance(self.object, Project):
            context['project'] = self.get_object()
        elif hasattr(self, 'object') and hasattr(self.object, 'project'):
            context['project'] = self.object.project
        else:
            context['project'] = self.get_project()
        # Project tagging/starring
        if 'project' in context and not getattr(
            settings, 'PROJECTROLES_KIOSK_MODE', False
        ):
            context['project_starred'] = app_settings.get(
                APP_NAME,
                'project_star',
                context['project'],
                self.request.user,
            )
        return context


class CurrentUserFormMixin:
    """Mixin for passing current user to form as current_user"""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'current_user': self.request.user})
        return kwargs


class InvalidFormMixin:
    """
    Mixin for UI improvements in invalid form failure. Recommended to be used
    with long forms spanning multiple screen heights.
    """

    def form_invalid(self, form, **kwargs):
        """Override form_invalid() to add Django message on form failure"""
        messages.error(self.request, FORM_INVALID_MSG)
        return super().form_invalid(form, **kwargs)


# Projectroles Internal UI view mixins -----------------------------------------


class ProjectModifyPermissionMixin(
    LoggedInPermissionMixin, ProjectPermissionMixin
):
    """
    Mixin for handling access to project modifying views, denying access even
    for local superusers if the project is remote and thus immutable.
    """

    def has_permission(self):
        """Override has_permission() to check remote project status"""
        perm = super().has_permission()
        project = self.get_project()
        return (
            False
            if project.is_remote() and not self._get_allow_remote_edit()
            else perm
        )

    def _get_allow_remote_edit(self):
        return getattr(self, 'allow_remote_edit', False)

    def handle_no_permission(self):
        """Override handle_no_permission to redirect user"""
        project = self.get_project()
        if project and project.is_remote():
            messages.error(
                self.request,
                'Modifications are not allowed for remote {}.'.format(
                    get_display_name(PROJECT_TYPE_PROJECT, plural=True)
                ),
            )
            return redirect(reverse('home'))
        elif self.request.user.is_authenticated:
            messages.error(self.request, NO_AUTH_MSG)
            return redirect(reverse('home'))
        else:
            messages.error(self.request, NO_AUTH_LOGIN_MSG)
            return redirect_to_login(self.request.get_full_path())


class RolePermissionMixin(ProjectModifyPermissionMixin):
    """
    Mixin to ensure permissions for RoleAssignment according to user role in
    project.
    """

    def has_permission(self):
        """Override has_permission to check perms depending on role"""
        if not super().has_permission():
            return False
        try:
            obj = RoleAssignment.objects.get(
                sodar_uuid=self.kwargs['roleassignment']
            )
            if obj.role.name == PROJECT_ROLE_OWNER:
                return False
            elif obj.role.name == PROJECT_ROLE_DELEGATE:
                return self.request.user.has_perm(
                    'projectroles.update_project_delegate',
                    self.get_permission_object(),
                )
            else:
                return self.request.user.has_perm(
                    'projectroles.update_project_members',
                    self.get_permission_object(),
                )
        except RoleAssignment.DoesNotExist:
            return False

    def get_permission_object(self):
        """Override get_permission_object for checking Project permission"""
        return self.get_project()


class ProjectListContextMixin:
    """Mixin for adding context data for displaying the project list."""

    def _get_custom_cols(self, user):
        """
        Return list of custom columns for projects including project data.

        :param user: User object
        """
        i = 0
        cols = []
        for app_plugin in [
            ap
            for ap in get_active_plugins(plugin_type='project_app')
            if ap.project_list_columns
        ]:
            # HACK for filesfolders columns (see issues #737 and #738)
            if app_plugin.name == 'filesfolders' and not getattr(
                settings, 'FILESFOLDERS_SHOW_LIST_COLUMNS', False
            ):
                continue
            for k, v in app_plugin.project_list_columns.items():
                if not v['active']:
                    continue
                v['app_plugin'] = app_plugin
                v['column_id'] = k
                v['ordering'] = v.get('ordering') or i
                cols.append(v)
                i += 1
        return sorted(cols, key=lambda x: x['ordering'])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['project_custom_cols'] = self._get_custom_cols(
            self.request.user
        )
        base_col_count = 1 if self.request.user.is_superuser else 2
        context['project_col_count'] = base_col_count + len(
            context['project_custom_cols']
        )
        context['page_options_default'] = app_settings.get(
            APP_NAME, 'project_list_pagination', user=self.request.user
        )
        return context


# General Views ----------------------------------------------------------------


class HomeView(
    LoginRequiredMixin,
    PluginContextMixin,
    ProjectListContextMixin,
    TemplateView,
):
    """Home view"""

    template_name = 'projectroles/home.html'


# General Project Views --------------------------------------------------------


class ProjectDetailView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectListContextMixin,
    ProjectContextMixin,
    DetailView,
):
    """Project details view"""

    permission_required = 'projectroles.view_project'
    model = Project
    slug_url_kwarg = 'project'
    slug_field = 'sodar_uuid'

    def add_no_perm_message(self):
        """
        Override add_login_message() to display a different message when
        redirected from invite accept view as a new user.
        """
        referer_url = self.request.META.get('HTTP_REFERER')
        if not referer_url:
            super().add_no_perm_message()
            return
        referer_path = urlparse(referer_url).path
        resolved_path = resolve(referer_path)
        if resolved_path.url_name.startswith('invite_process_'):
            messages.info(self.request, LOGIN_MSG)
            return
        super().add_no_perm_message()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_superuser:
            context['role'] = None
        elif self.request.user.is_authenticated:
            try:
                role_as = RoleAssignment.objects.get(
                    user=self.request.user, project=self.object
                )
                context['role'] = role_as.role
            except RoleAssignment.DoesNotExist:
                context['role'] = None
        elif self.object.public_guest_access:
            context['role'] = Role.objects.filter(
                name=PROJECT_ROLE_GUEST
            ).first()
        else:
            context['role'] = None

        # Remote projects
        q_kwargs = {
            'project_uuid': self.object.sodar_uuid,
            'level': REMOTE_LEVEL_READ_ROLES,
        }
        if not self.request.user.has_perm(
            'projectroles.view_hidden_projects', self.object
        ):
            q_kwargs['site__user_display'] = True
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            context['target_projects'] = RemoteProject.objects.filter(
                site__mode=SITE_MODE_TARGET, **q_kwargs
            ).order_by('site__name')
        elif settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET:
            context['peer_projects'] = RemoteProject.objects.filter(
                site__mode=SITE_MODE_PEER, **q_kwargs
            ).order_by('site__name')
        return context


# Search Views -----------------------------------------------------------------


class ProjectSearchMixin:
    """Common functionalities for search views"""

    def _get_app_results(
        self, user, search_terms, search_type, search_keywords
    ):
        """
        Return app plugin search results.

        :param search_terms: Search terms (list of strings)
        :param search_type: Optional type keyword for search (string or None)
        :param search_keywords: Optional keywords (list of strings or None)
        :return: List
        """
        plugins = get_active_plugins(plugin_type='project_app')
        ret = []
        omit_apps_list = getattr(settings, 'PROJECTROLES_SEARCH_OMIT_APPS', [])

        search_apps = sorted(
            [
                p
                for p in plugins
                if (p.search_enable and p.name not in omit_apps_list)
            ],
            key=lambda x: x.plugin_ordering,
        )
        if search_type:
            search_apps = [
                p for p in search_apps if search_type in p.search_types
            ]
        for plugin in search_apps:
            search_kwargs = {
                'user': user,
                'search_type': search_type,
                'search_terms': search_terms,
                'keywords': search_keywords,
            }
            search_res = {
                'plugin': plugin,
                'results': None,
                'error': None,
                'has_results': False,
            }
            try:
                search_res['results'] = plugin.search(**search_kwargs)
                for r in search_res['results']:
                    if r.items and (
                        (isinstance(r.items, QuerySet) and r.items.count() > 0)
                        or (isinstance(r.items, list) and len(r.items) > 0)
                    ):
                        search_res['has_results'] = True
                        break
                # Build results into dict for easier use in templates
                search_res['results'] = {
                    r.category: r for r in search_res['results']
                }
            except Exception as ex:
                if settings.DEBUG:
                    raise ex
                search_res['error'] = str(ex)
                logger.error(
                    'Exception raised by search() in {}: "{}" ({})'.format(
                        plugin.name,
                        ex,
                        '; '.join(
                            [
                                '{}={}'.format(k, v)
                                for k, v in search_kwargs.items()
                            ]
                        ),
                    )
                )
            ret.append(search_res)
        return ret

    def _get_not_found(self, search_type, project_results, app_results):
        """
        Return list of apps for which objects were search for but not returned.

        :param search_type: Type keyword for search if set
        :param project_results: Results for projectroles search
        :param app_results: Results for app plugin search
        :return: List
        """
        ret = []
        if len(project_results) == 0 and (
            not search_type or search_type == 'project'
        ):
            ret.append('Projects')
        for results in [a['results'] for a in app_results]:
            if not results:
                continue
            for k, r in results.items():
                type_match = True if search_type else False
                if not type_match and search_type in r.search_types:
                    type_match = True
                if (type_match or not search_type) and (not r.items):
                    ret.append(r.title)
        return ret

    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, 'PROJECTROLES_ENABLE_SEARCH', False):
            messages.error(request, 'Search is not enabled.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class ProjectSearchResultsView(
    LoginRequiredMixin, ProjectSearchMixin, TemplateView
):
    """View for displaying results of search within projects"""

    template_name = 'projectroles/search_results.html'

    def _handle_context(self, request, *args, **kwargs):
        """Handle context and render to response in GET/POST requests"""
        context = self.get_context_data(*args, **kwargs)
        if not context['search_terms']:
            messages.error(request, 'No search terms provided.')
            return redirect(reverse('home'))
        return super().render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        search_input = ''
        search_terms = []
        search_type = None
        keyword_input = []
        search_keywords = {}

        if self.request.POST.get('m'):  # Multi search
            search_terms = [
                t.strip()
                for t in self.request.POST['m'].strip().split('\r\n')
                if len(t.strip()) >= 3
            ]
            if self.request.POST.get('k'):
                keyword_input = self.request.POST['k'].strip().split(' ')
        elif self.request.GET.get('s'):  # Single search
            search_input = self.request.GET.get('s').strip()
            search_split = search_input.split(' ')
            search_term = search_split[0].strip()
            for i in range(1, len(search_split)):
                s = search_split[i].strip()
                if ':' in s:
                    keyword_input.append(s)
                elif s != '':
                    search_term += ' ' + s.lower()
            if search_term:
                search_terms = [search_term]
        search_terms = list(dict.fromkeys(search_terms))  # Remove dupes

        for s in keyword_input:
            kw = s.split(':')[0].lower().strip()
            val = s.split(':')[1].lower().strip()
            if kw == 'type':
                search_type = val
            else:
                search_keywords[kw] = val

        context['search_input'] = search_input
        context['search_terms'] = search_terms
        context['search_type'] = search_type
        context['search_keywords'] = search_keywords
        # Get project results
        if not search_type or search_type == 'project':
            context['project_results'] = []
            for p in Project.objects.find(search_terms, project_type='PROJECT'):
                if p.public_guest_access or self.request.user.has_perm(
                    'projectroles.view_project', p
                ):
                    context['project_results'].append(p)
                elif self.request.user.is_authenticated and p.parent:
                    parent_as = p.parent.get_role(self.request.user)
                    if (
                        parent_as
                        and parent_as.role.rank
                        >= ROLE_RANKING[PROJECT_ROLE_FINDER]
                    ):
                        context['project_results'].append(p)
        # Get app results
        context['app_results'] = self._get_app_results(
            self.request.user, search_terms, search_type, search_keywords
        )
        # List apps for which no results were found
        context['not_found'] = self._get_not_found(
            search_type,
            context.get('project_results') or [],
            context['app_results'],
        )
        return context

    def get(self, request, *args, **kwargs):
        return self._handle_context(request, *args, *kwargs)

    def post(self, request, *args, **kwargs):
        return self._handle_context(request, *args, *kwargs)


class ProjectAdvancedSearchView(
    LoginRequiredMixin, ProjectSearchMixin, TemplateView
):
    """View for displaying advanced search form"""

    template_name = 'projectroles/search_advanced.html'

    def post(self, request, *args, **kwargs):
        return ProjectSearchResultsView.as_view()(request)


# Project Modifying Views ------------------------------------------------------


class ProjectModifyPluginViewMixin:
    """Helpers for project modify API"""

    @classmethod
    def call_project_modify_api(cls, method_name, revert_name, method_args):
        """
        Call project modify API for a specific method and parameters. This
        method Will run reversion methods for all plugins if execution for one
        fails.

        :param method_name: Name of execution method in plugin (string)
        :param revert_name: Name of revert method in plugin (string or None)
        :param method_args: Arguments to be passed for the methods (list)
        :raise: Exception if execution for a plugin fails.
        """
        modify_api_apps = getattr(settings, 'PROJECTROLES_MODIFY_API_APPS', [])
        app_plugins = []
        if modify_api_apps:
            for a in modify_api_apps:
                plugin = get_app_plugin(a)
                if not plugin:
                    msg = 'Unable to find active plugin "{}"'.format(a)
                    logger.error(msg)
                    raise ImproperlyConfigured(msg)
                app_plugins.append(plugin)
        else:
            app_plugins = get_active_plugins('backend') + get_active_plugins(
                'project_app'
            )

        called_plugins = []
        for p in app_plugins:
            if not hasattr(p, method_name):
                continue  # Only there if using ProjectModifyPluginAPIMixin
            logger.debug(
                'Calling {}() in plugin "{}"'.format(method_name, p.name)
            )
            try:
                getattr(p, method_name)(*method_args)
                called_plugins.append(p)
            except Exception as ex:
                logger.error(
                    'Exception in {}() for plugin "{}": {}'.format(
                        method_name, p.name, ex
                    )
                )
                if revert_name:
                    for cp in called_plugins:
                        try:
                            cp.getattr(revert_name)(*method_args)
                        except Exception as ex_revert:
                            logger.error(
                                'Exception in {}() for plugin "{}": {}'.format(
                                    method_name, cp.name, ex_revert
                                )
                            )
                raise ex


class ProjectModifyMixin(ProjectModifyPluginViewMixin):
    """Mixin for Project creation/updating in UI and API views"""

    #: Remote site fields
    site_fields = {}

    @staticmethod
    def _get_old_project_data(project):
        """Get existing data from project fields"""
        return {
            'title': project.title,
            'parent': project.parent,
            'description': project.description,
            'readme': project.readme.raw,
            'owner': project.get_owner().user,
            'public_guest_access': project.public_guest_access,
        }

    @classmethod
    def _get_remote_project_data(cls, project):
        """Return existing remote project data"""
        ret = {}
        existing_sites = []
        for rp in RemoteProject.objects.filter(project=project):
            ret[str(rp.site.sodar_uuid)] = rp.level == REMOTE_LEVEL_READ_ROLES
            existing_sites.append(rp.site.sodar_uuid)
        # Sites not yet added
        for rs in RemoteSite.objects.filter(
            mode=SITE_MODE_TARGET, user_display=True, owner_modifiable=True
        ).exclude(sodar_uuid__in=existing_sites):
            ret[str(rs.sodar_uuid)] = False
        return ret

    @staticmethod
    def _get_app_settings(data, instance, user):
        """
        Return a dictionary of project app settings and their values.

        :param data: Cleaned form data
        :param instance: Existing Project object or None
        :param user: User initiating the project update
        :return: Dict
        """
        app_plugins = [p for p in get_active_plugins() if p.app_settings]
        project_settings = {}
        p_kwargs = {}
        # Show unmodifiable settings to superusers
        if user and not user.is_superuser:
            p_kwargs['user_modifiable'] = True

        for plugin in app_plugins + [None]:
            if plugin:
                name = plugin.name
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_PROJECT, plugin=plugin, **p_kwargs
                )
            else:
                name = APP_NAME
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_PROJECT, plugin_name=name, **p_kwargs
                )

            for s_def in p_settings.values():
                s_name = 'settings.{}.{}'.format(name, s_def.name)
                s_data = data.get(s_name)

                if instance.type not in s_def.project_types:
                    continue
                if s_data is None and not instance:
                    s_data = app_settings.get_default(name, s_def.name)
                if s_def.type == APP_SETTING_TYPE_JSON:
                    if s_data is None:
                        s_data = {}
                    project_settings[s_name] = json.dumps(s_data)
                elif s_data is not None:
                    project_settings[s_name] = s_data
        return project_settings

    def _get_project_update_data(
        self, old_data, project, old_sites, sites, project_settings
    ):
        extra_data = {}
        upd_fields = []
        if old_data['title'] != project.title:
            extra_data['title'] = project.title
            upd_fields.append('title')
        if old_data['parent'] != project.parent:
            extra_data['parent'] = project.parent
            upd_fields.append('parent')
        if old_data['description'] != project.description:
            extra_data['description'] = project.description
            upd_fields.append('description')
        if old_data['readme'] != project.readme.raw:
            extra_data['readme'] = project.readme.raw
            upd_fields.append('readme')
        if old_data['public_guest_access'] != project.public_guest_access:
            extra_data['public_guest_access'] = project.public_guest_access
            upd_fields.append('public_guest_access')

        # Remote projects
        if (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE
            and project.type == PROJECT_TYPE_PROJECT
        ):
            for s in [f.split('.')[1] for f in self.site_fields]:
                if 'remote_sites' not in upd_fields and (
                    s not in old_sites or bool(old_sites[s]) != bool(sites[s])
                ):
                    upd_fields.append('remote_sites')
            if 'remote_sites' in upd_fields:
                extra_data['remote_sites'] = {
                    k: bool(v) for k, v in sites.items()
                }

        # Settings
        for k, v in project_settings.items():
            p_name = k.split('.')[1]
            s_name = k.split('.')[2]
            s_def = app_settings.get_definition(s_name, plugin_name=p_name)
            old_v = app_settings.get(p_name, s_name, project)
            if s_def.type == APP_SETTING_TYPE_JSON:
                v = json.loads(v)
            if old_v != v:
                extra_data[k] = v
                upd_fields.append(k)
        return extra_data, upd_fields

    @staticmethod
    def _get_timeline_ok_status():
        timeline = get_backend_api('timeline_backend')
        if not timeline:
            raise ImproperlyConfigured('Timeline backend not found')
        else:
            return timeline.TL_STATUS_OK

    def _update_remote_sites(self, project, data):
        """Update project for remote sites"""
        ret = {}
        for f in self.site_fields:
            site_uuid = f.split('.')[1]
            site = RemoteSite.objects.filter(sodar_uuid=site_uuid).first()
            # TODO: Validate site here
            value = data[f]
            rp = RemoteProject.objects.filter(
                site=site, project=project
            ).first()
            modify = None
            if rp and (
                (value and rp.level != REMOTE_LEVEL_READ_ROLES)
                or (not value and rp.level == REMOTE_LEVEL_READ_ROLES)
            ):
                rp.level = (
                    REMOTE_LEVEL_READ_ROLES if value else REMOTE_LEVEL_REVOKED
                )
                rp.save()
                modify = 'Updated'
            elif not rp and value:  # Only create if value is True
                rp = RemoteProject.objects.create(
                    project_uuid=project.sodar_uuid,
                    project=project,
                    site=site,
                    level=REMOTE_LEVEL_READ_ROLES,
                )
                modify = 'Created'
            if modify:
                logger.debug(
                    '{} RemoteProject for site "{}" ({}): {}'.format(
                        modify, site.name, site.sodar_uuid, rp.level
                    )
                )
            ret[site_uuid] = rp and rp.level == REMOTE_LEVEL_READ_ROLES
        return ret

    @classmethod
    def _update_settings(cls, project, project_settings):
        """Update project settings"""
        is_remote = project.is_remote()
        for k, v in project_settings.items():
            _, plugin_name, setting_name = k.split('.', 3)
            # Skip updating global settings on target site
            if is_remote:
                # TODO: Optimize (this can require a lot of queries)
                s_def = app_settings.get_definition(
                    setting_name, plugin_name=plugin_name
                )
                if s_def.global_edit:
                    continue
            app_settings.set(
                plugin_name=k.split('.')[1],
                setting_name=k.split('.')[2],
                value=v,
                project=project,
                validate=True,
            )

    def _create_timeline_event(
        self,
        project,
        action,
        owner,
        old_data,
        old_sites,
        sites,
        project_settings,
        request,
    ):
        timeline = get_backend_api('timeline_backend')
        if not timeline:
            return None
        type_str = project.type.capitalize()

        if action == PROJECT_ACTION_CREATE:
            tl_desc = 'create ' + type_str.lower() + ' with {owner} as owner'
            extra_data = {
                'title': project.title,
                'owner': owner.username,
                'description': project.description,
                'readme': project.readme.raw,
            }
            # Add settings to extra data
            for k, v in project_settings.items():
                p_name = k.split('.')[1]
                s_name = k.split('.')[2]
                s_def = app_settings.get_definition(s_name, plugin_name=p_name)
                if s_def.type == APP_SETTING_TYPE_JSON:
                    v = json.loads(v)
                extra_data[k] = v

        else:  # Update
            tl_desc = 'update ' + type_str.lower()
            extra_data, upd_fields = self._get_project_update_data(
                old_data, project, old_sites, sites, project_settings
            )
            if extra_data.get('parent'):  # Convert parent object into UUID
                extra_data['parent'] = str(extra_data['parent'].sodar_uuid)
            if len(upd_fields) > 0:
                tl_desc += ' (' + ', '.join(x for x in upd_fields) + ')'

        tl_event = timeline.add_event(
            project=project,
            app_name=APP_NAME,
            user=request.user,
            event_name='project_{}'.format(action.lower()),
            description=tl_desc,
            extra_data=extra_data,
        )
        if action == PROJECT_ACTION_CREATE:
            tl_event.add_object(owner, 'owner', owner.username)
        return tl_event

    @classmethod
    def _notify_users(cls, project, action, owner, old_parent, request):
        """
        Notify users about project creation and update. Displays app alerts
        and/or sends emails depending on the site configuration.
        """
        app_alerts = get_backend_api('appalerts_backend')
        # Create alerts and send emails
        owner_as = RoleAssignment.objects.filter(
            project=project, user=owner
        ).first()
        # Owner change notification
        if request.user != owner and action == PROJECT_ACTION_CREATE:
            if app_alerts:
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='role_create',
                    user=owner,
                    message=ROLE_CREATE_MSG.format(
                        project=project.title, role=owner_as.role.name
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
            if SEND_EMAIL and app_settings.get(
                APP_NAME, 'notify_email_role', user=owner
            ):
                email.send_role_change_mail(
                    action.lower(),
                    project,
                    owner,
                    owner_as.role,
                    request,
                )
        # Project creation/moving for parent category owner
        if (
            project.parent
            and project.parent.get_owner().user != owner_as.user
            and project.parent.get_owner().user != request.user
        ):
            parent_owner = project.parent.get_owner().user
            parent_owner_email = app_settings.get(
                APP_NAME, 'notify_email_project', user=parent_owner
            )

            if action == PROJECT_ACTION_CREATE and request.user != parent_owner:
                if app_alerts:
                    app_alerts.add_alert(
                        app_name=APP_NAME,
                        alert_name='project_create_parent',
                        user=parent_owner,
                        message='New {} created under category '
                        '"{}": "{}".'.format(
                            project.type.lower(),
                            project.parent.title,
                            project.title,
                        ),
                        url=reverse(
                            'projectroles:detail',
                            kwargs={'project': project.sodar_uuid},
                        ),
                        project=project,
                    )
                if SEND_EMAIL and parent_owner_email:
                    email.send_project_create_mail(project, request)

            elif old_parent and request.user != parent_owner:
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='project_move_parent',
                    user=parent_owner,
                    message='{} moved under category '
                    '"{}": "{}".'.format(
                        project.type.capitalize(),
                        project.parent.title,
                        project.title,
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
                if SEND_EMAIL and parent_owner_email:
                    email.send_project_move_mail(project, request)

    @transaction.atomic
    def modify_project(self, data, request, instance=None):
        """
        Create or update a Project. This method should be called either in
        form_valid() in a Django form view or save() in a DRF serializer.

        :param data: Cleaned data from a form or serializer
        :param request: Request initiating the action
        :param instance: Existing Project object or None
        :return: Created or updated Project object
        """
        action = PROJECT_ACTION_UPDATE if instance else PROJECT_ACTION_CREATE
        old_data = {}
        old_project = None

        if instance:
            project = instance
            # In case of a PATCH request, get existing obj to fill out fields
            old_project = Project.objects.get(sodar_uuid=instance.sodar_uuid)
            old_data = self._get_old_project_data(old_project)  # Store old data

            project.title = data.get('title') or old_project.title
            project.description = (
                data.get('description') or old_project.description
            )
            project.type = data.get('type') or old_project.type
            project.readme = data.get('readme') or old_project.readme
            # NOTE: Must do this as parent can exist but be None
            project.parent = (
                data['parent'] if 'parent' in data else old_project.parent
            )
            project.public_guest_access = (
                data.get('public_guest_access') or False
            )
        else:
            project = Project(
                title=data.get('title'),
                description=data.get('description'),
                type=data.get('type'),
                readme=data.get('readme'),
                parent=data.get('parent'),
                public_guest_access=data.get('public_guest_access') or False,
            )
            project.save()

        owner = data.get('owner')
        if not owner and old_project:  # In case of a PATCH request
            owner = old_project.get_owner().user

        # Create/update RemoteProject objects
        old_sites = {}
        sites = {}
        if (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE
            and project.type == PROJECT_TYPE_PROJECT
        ):
            self.site_fields = [f for f in data if f.startswith('remote_site.')]
            old_sites = self._get_remote_project_data(project)
            sites = self._update_remote_sites(project, data)

        # Get app settings, store old settings
        project_settings = self._get_app_settings(data, project, request.user)
        old_settings = None
        if action == PROJECT_ACTION_UPDATE:
            old_settings = json.loads(json.dumps(project_settings))  # Copy

        # Create timeline event
        tl_event = self._create_timeline_event(
            project,
            action,
            owner,
            old_data,
            old_sites,
            sites,
            project_settings,
            request,
        )
        # Get old parent for project moving
        old_parent = (
            old_project.parent
            if old_project
            and old_project.parent
            and old_project.parent != project.parent
            else None
        )

        # Update owner and settings
        if action == PROJECT_ACTION_CREATE:
            RoleAssignment.objects.create(
                project=project,
                user=owner,
                role=Role.objects.get(name=PROJECT_ROLE_OWNER),
            )
        self._update_settings(project, project_settings)
        project.save()  # TODO: Is this required anymore?

        # Call for additional actions for project creation/update in plugins
        if getattr(settings, 'PROJECTROLES_ENABLE_MODIFY_API', False):
            args = [project, action, project_settings]
            if action == PROJECT_ACTION_UPDATE:
                args += [old_data, old_settings]
            else:
                args += [None, None]
            args.append(request)
            self.call_project_modify_api(
                'perform_project_modify', 'revert_project_modify', args
            )

        # If public access was updated, update has_public_children for parents
        if (
            old_project
            and project.parent
            and old_project.public_guest_access != project.public_guest_access
        ):
            try:
                project._update_public_children()
            except Exception as ex:
                logger.error(
                    'Exception in updating has_public_children(): {}'.format(ex)
                )

        # Once all is done, update timeline event, create alerts and emails
        if tl_event:
            tl_event.set_status(self._get_timeline_ok_status())
        self._notify_users(project, action, owner, old_parent, request)
        return project


class ProjectModifyFormMixin(ProjectModifyMixin):
    """Mixin for Project creation/updating in Django form views"""

    def form_valid(self, form):
        """Handle project updating if form is valid"""
        instance = form.instance if form.instance.pk else None
        action = PROJECT_ACTION_UPDATE if instance else PROJECT_ACTION_CREATE

        if instance and instance.parent:
            redirect_url = reverse(
                'projectroles:detail',
                kwargs={'project': instance.parent.sodar_uuid},
            )
        else:
            redirect_url = reverse('home')

        try:
            project = self.modify_project(
                data=form.cleaned_data,
                request=self.request,
                instance=form.instance if instance else None,
            )
            messages.success(
                self.request,
                '{} {}d.'.format(
                    get_display_name(project.type, title=True), action.lower()
                ),
            )
            redirect_url = reverse(
                'projectroles:detail', kwargs={'project': project.sodar_uuid}
            )
        except Exception as ex:
            messages.error(
                self.request,
                'Unable to {} {}: {}'.format(
                    action.lower(), form.cleaned_data['type'].lower(), ex
                ),
            )
            if settings.DEBUG:
                raise ex
        return redirect(redirect_url)


class ProjectDeleteAccessMixin:
    """
    Mixin to check special access permissions for project deletion.

    Also used for ProjectUpdateView to control access to view link, hence a
    separate mixin.

    We want to provide an informative message to the end user and also prevent
    superuser access if needed, hence we're not implementing this in rules.
    """

    @classmethod
    def check_delete_permission(cls, project):
        """
        Check delete permission. Also applies to superusers.

        :param project: Project object
        :return: Boolean, string (in case of error) or None
        """
        p_type = get_display_name(project.type)
        if (
            project.type == PROJECT_TYPE_CATEGORY
            and project.get_children().count() > 0
        ):
            return False, PROJECT_DELETE_CAT_ERR_MSG.format(project_type=p_type)
        # Disallow for remote projects which haven't been revoked
        if project.is_remote():
            rp = RemoteProject.objects.filter(
                project_uuid=project.sodar_uuid,
                site__mode=SITE_MODE_SOURCE,
            ).first()
            if rp.level != REMOTE_LEVEL_REVOKED:
                return (
                    False,
                    PROJECT_DELETE_TARGET_ERR_MSG.format(project_type=p_type),
                )
        # Disallow for source projects with non-revoked remote projects
        # NOTE: Categories can be deleted
        elif project.type == PROJECT_TYPE_PROJECT:
            rps = RemoteProject.objects.filter(
                project_uuid=project.sodar_uuid, site__mode=SITE_MODE_TARGET
            ).exclude(level__in=[REMOTE_LEVEL_NONE, REMOTE_LEVEL_REVOKED])
            if rps.count() > 0:
                return (
                    False,
                    PROJECT_DELETE_SOURCE_ERR_MSG.format(project_type=p_type),
                )
        return True, None


class ProjectDeleteMixin(ProjectModifyPluginViewMixin):
    """Mixin for Project deletion in UI and API views"""

    @classmethod
    def _create_timeline_event(cls, project, request):
        """
        Create timeline summary event for project deletion. Created as a
        classified site-wide event only viewable by superusers.

        :param project: Project object
        :param request: HttpRequest object
        """
        timeline = get_backend_api('timeline_backend')
        if not timeline:
            return
        local_users = {
            a.user.username: a.role.name
            for a in project.local_roles.order_by(
                'role__rank', 'user__username'
            )
        }
        parent = str(project.parent.sodar_uuid) if project.parent else None
        extra_data = {
            'title': project.title,
            'type': project.type,
            'parent': parent,
            'description': project.description,
            'readme': project.readme.raw,
            'public_guest_access': project.public_guest_access,
            'archive': project.archive,
            'full_title': project.full_title,
            'sodar_uuid': str(project.sodar_uuid),
            'local_roles': local_users,
        }
        timeline.add_event(
            project=None,  # No project as it has been deleted
            app_name=APP_NAME,
            user=request.user,
            event_name='project_delete',
            description=f'delete {project.type.lower()} '
            f'{project.get_log_title()}',
            extra_data=extra_data,
            classified=True,
            status_type=timeline.TL_STATUS_OK,
        )

    @classmethod
    def get_redirect_url(cls, project):
        if project.parent:
            return reverse(
                'projectroles:detail',
                kwargs={'project': project.parent.sodar_uuid},
            )
        else:
            return reverse('home')

    def handle_delete(self, project, request):
        """
        Handle project deletion. Deletes the object, creates a summary timeline
        event and sends out alerts and emails to project members.

        :param project: Project object of project to be deleted
        :param request: HttpRequest object
        """
        app_alerts = get_backend_api('appalerts_backend')
        # Call project modify API plugin
        if getattr(settings, 'PROJECTROLES_ENABLE_MODIFY_API', False):
            self.call_project_modify_api(
                'perform_project_delete', None, [project]
            )
        # Create timeline event
        self._create_timeline_event(project, request)
        # Create app alerts
        if app_alerts:
            users = [
                a.user for a in project.get_roles() if a.user != request.user
            ]
            app_alerts.add_alerts(
                app_name=APP_NAME,
                alert_name='project_delete',
                users=users,
                message=PROJECT_DELETE_MSG.format(
                    project_type=get_display_name(project.type, title=True),
                    project_title=project.title,
                    user_name=request.user.username,
                ),
            )
        # Send email
        if SEND_EMAIL:
            email.send_project_delete_mail(project, request)
        # Actually delete project object
        project.delete()


class ProjectCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectModifyFormMixin,
    ProjectContextMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    CreateView,
):
    """Project creation view"""

    permission_required = 'projectroles.create_project'
    model = Project
    form_class = ProjectForm

    def has_permission(self):
        """
        Override has_permission() to ensure even superuser can't create
        project under a remote category as target
        """
        if not self.kwargs.get('project'):
            if self.request.user.is_superuser:
                return True  # Allow top level project creation for superuser
            return False  # Disallow for other users
        elif (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and self.kwargs.get('project')
        ):
            parent = Project.objects.filter(
                sodar_uuid=self.kwargs['project']
            ).first()
            if parent and parent.is_remote():
                return False
        return super().has_permission()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if 'project' in self.kwargs:
            context['parent'] = Project.objects.get(
                sodar_uuid=self.kwargs['project']
            )
        return context

    def get_form_kwargs(self):
        """Pass URL arguments to form"""
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch() for target site check"""
        # If site is in target mode and target creation is not allowed, redirect
        if (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and not settings.PROJECTROLES_TARGET_CREATE
        ):
            messages.error(request, TARGET_CREATE_DISABLED_MSG)
            return redirect(reverse('home'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Override get() to limit project creation under other projects"""
        if 'project' in self.kwargs:
            project = Project.objects.get(sodar_uuid=self.kwargs['project'])
            if project.type != PROJECT_TYPE_CATEGORY:
                messages.error(
                    self.request,
                    'Creating nested {} is not allowed.'.format(
                        get_display_name(PROJECT_TYPE_PROJECT, plural=True)
                    ),
                )
                return redirect(
                    reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    )
                )
        return super().get(request, *args, **kwargs)


class ProjectUpdateView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    ProjectModifyFormMixin,
    ProjectDeleteAccessMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    UpdateView,
):
    """Project updating view"""

    permission_required = 'projectroles.update_project'
    model = Project
    form_class = ProjectForm
    slug_url_kwarg = 'project'
    slug_field = 'sodar_uuid'
    allow_remote_edit = True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        access, msg = self.check_delete_permission(self.get_object())
        context['project_delete_access'] = access
        context['project_delete_msg'] = msg or ''
        return context


class ProjectArchiveView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    ProjectModifyPluginViewMixin,
    TemplateView,
):
    """Project archiving/unarchiving view"""

    template_name = 'projectroles/project_archive_confirm.html'
    permission_required = 'projectroles.update_project'

    def _alert_users(self, project, action, user):
        """
        Alert users on project archiving/unarchiving.

        :param project: Project object
        :param action: String ("archive" or "unarchive")
        :param user: User initiating project archiving/unarchiving
        """
        app_alerts = get_backend_api('appalerts_backend')
        if not app_alerts:
            return
        alert_p = get_display_name(PROJECT_TYPE_PROJECT, title=True)
        if action == 'archive':
            alert_msg = '{} data is now read-only.'.format(alert_p)
        else:
            alert_msg = '{} data can be modified.'.format(alert_p)
        users = [a.user for a in project.get_roles() if a.user != user]
        users = list(set(users))  # Remove possible dupes (see issue #710)
        if not users:
            return
        else:
            app_alerts.add_alerts(
                app_name=APP_NAME,
                alert_name='project_{}'.format(action),
                users=users,
                message='{} {}d by {}. {}'.format(
                    alert_p, action, user.get_full_name(), alert_msg
                ),
                url=reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                ),
                project=project,
            )

    def get(self, request, *args, **kwargs):
        """Override get() to check project type"""
        project = self.get_project()
        if project.type != PROJECT_TYPE_PROJECT:
            messages.error(request, CAT_ARCHIVE_ERR_MSG)
            return redirect(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                )
            )
        return super().render_to_response(
            self.get_context_data(*args, **kwargs)
        )

    def post(self, request, **kwargs):
        """Override post() to handle POST from confirmation template"""
        timeline = get_backend_api('timeline_backend')
        project = self.get_project()
        redirect_url = reverse(
            'projectroles:detail', kwargs={'project': project.sodar_uuid}
        )
        if project.type == PROJECT_TYPE_CATEGORY:
            messages.error(request, CAT_ARCHIVE_ERR_MSG)
            return redirect(redirect_url)

        status = request.POST.get('status')
        if status is None:
            messages.error(request, 'Status not set, unable to set archival.')
            return redirect(redirect_url)
        status = True if status.lower() in ['1', 'true'] else False
        action = 'unarchive' if not status else 'archive'
        if project.archive == status:
            messages.warning(
                request,
                '{} is already {}d.'.format(
                    get_display_name(project.type, title=True), action
                ),
            )
            return redirect(redirect_url)

        try:
            project.set_archive(status)
            # Call for additional actions for archive/unarchive in plugins
            if getattr(settings, 'PROJECTROLES_ENABLE_MODIFY_API', False):
                self.call_project_modify_api(
                    'perform_project_archive',
                    'revert_project_archive',
                    [project],
                )
            messages.success(
                request,
                '{} {}d.'.format(
                    get_display_name(project.type, title=True), action
                ),
            )
        except Exception as ex:
            messages.error(
                request,
                'Failed to {} {}: {}'.format(
                    action, get_display_name(project.type), ex
                ),
            )
            return redirect(redirect_url)

        try:
            if timeline:
                timeline.add_event(
                    project=project,
                    app_name=APP_NAME,
                    user=request.user,
                    event_name='project_{}'.format(action),
                    description='{} project'.format(action),
                    status_type=timeline.TL_STATUS_OK,
                )
            # Alert users and send email
            self._alert_users(project, action, request.user)
            if SEND_EMAIL:  # NOTE: Opt-out settings checked in email method
                email.send_project_archive_mail(project, action, request)
        except Exception as ex:
            messages.error(request, 'Failed to alert users: {}'.format(ex))
        return redirect(redirect_url)


class ProjectDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectDeleteMixin,
    ProjectDeleteAccessMixin,
    ProjectModifyPluginViewMixin,
    DeleteView,
):
    """Project deletion view"""

    model = Project
    permission_required = 'projectroles.delete_project'
    slug_field = 'sodar_uuid'
    slug_url_kwarg = 'project'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        project = self.get_object()
        # Prevent access in certain conditions, even for superusers
        access, msg = self.check_delete_permission(project)
        if not access:
            messages.error(self.request, msg)
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        project = self.get_object()
        redirect_url = reverse(
            'projectroles:update', kwargs={'project': project.sodar_uuid}
        )

        # Don't allow deletion unless user has input the host name
        host_confirm = self.request.POST.get('delete_host_confirm')
        actual_host = self.request.get_host().split(':')[0]
        if not host_confirm or host_confirm != actual_host:
            msg = (
                f'Incorrect host name for confirming sheet deletion: '
                f'"{host_confirm}"'
            )
            logger.error(msg + ' (correct={})'.format(actual_host))
            messages.error(
                self.request, 'Host name input incorrect, deletion cancelled.'
            )
            return redirect(redirect_url)

        # Proceed with deletion
        try:
            with transaction.atomic():
                self.handle_delete(project, self.request)
            p_type = get_display_name(project.type, title=True)
            messages.success(self.request, f'{p_type} deleted.')
            redirect_url = self.get_redirect_url(project)
        except Exception as ex:
            if settings.DEBUG:
                raise ex
            p_type = get_display_name(project.type, title=False)
            messages.error(self.request, f'Failed to delete {p_type}: {ex}')
        return redirect(redirect_url)


# RoleAssignment Views ---------------------------------------------------------


class ProjectRoleView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    TemplateView,
):
    """View for displaying project roles"""

    permission_required = 'projectroles.view_project_roles'
    template_name = 'projectroles/project_roles.html'
    model = Project

    def get_context_data(self, *args, **kwargs):
        project = self.get_project()
        project_remote = project.is_remote()
        context = super().get_context_data(*args, **kwargs)
        context['roles'] = sorted(
            project.get_roles(), key=lambda x: [x.role.rank, x.user.username]
        )
        owner_rank = ROLE_RANKING[PROJECT_ROLE_OWNER]
        context['enable_owner_transfer'] = any(
            [r.role.rank >= owner_rank for r in context['roles']]
        )
        if project.is_remote():
            context[
                'remote_roles_url'
            ] = project.get_source_site().url + reverse(
                'projectroles:roles', kwargs={'project': project.sodar_uuid}
            )
        context['finder_info'] = ROLE_FINDER_INFO.format(
            categories=get_display_name(PROJECT_TYPE_CATEGORY, plural=True),
            projects=get_display_name(PROJECT_TYPE_PROJECT, plural=True),
        )
        if self.request.user.is_authenticated:
            own_local_as = RoleAssignment.objects.filter(
                project=project, user=self.request.user
            ).first()
            context['own_local_as'] = own_local_as
            context['project_leave_access'] = (
                own_local_as is not None
                and own_local_as.role.rank > ROLE_RANKING[PROJECT_ROLE_OWNER]
                and not project_remote
            )
            leave_msg = ''
            if not own_local_as:
                leave_msg = ROLE_LEAVE_INHERIT_MSG.format(
                    category_type=get_display_name(PROJECT_TYPE_CATEGORY)
                )
            elif own_local_as.role.rank == ROLE_RANKING[PROJECT_ROLE_OWNER]:
                leave_msg = ROLE_LEAVE_OWNER_MSG
            elif project_remote:
                leave_msg = ROLE_LEAVE_REMOTE_MSG.format(
                    project_type=get_display_name(project.type, title=True)
                )
            context['project_leave_msg'] = leave_msg
        return context


class RoleAssignmentModifyMixin(ProjectModifyPluginViewMixin):
    """Mixin for RoleAssignment creation/updating in UI and API views"""

    @transaction.atomic
    def modify_assignment(
        self, data, request, project, instance=None, promote=False
    ):
        """
        Create or update a RoleAssignment. This method should be called either
        in form_valid() in a Django form view or save() in a DRF serializer.
        The method calls related ProjectModifyPluginAPIMixin methods if enabled
        in your plugin.

        :param data: Cleaned data from a form or serializer
        :param request: Request initiating the action
        :param project: Project object
        :param instance: Existing RoleAssignment object or None
        :param promote: Promoting an inherited user (boolean, default=False)
        :return: Created or updated RoleAssignment object
        """
        app_alerts = get_backend_api('appalerts_backend')
        timeline = get_backend_api('timeline_backend')
        tl_event = None
        action = PROJECT_ACTION_UPDATE if instance else PROJECT_ACTION_CREATE
        user = data.get('user')
        role = data.get('role')

        # Init Timeline event
        if timeline:
            tl_desc = '{} role {}"{}" for {{{}}}'.format(
                action.lower(),
                'to ' if action == PROJECT_ACTION_UPDATE else '',
                role.name,
                'user',
            )
            tl_event = timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name='role_{}'.format(action.lower()),
                description=tl_desc,
            )
            tl_event.add_object(user, 'user', user.username)

        if action == PROJECT_ACTION_CREATE:
            role_as = RoleAssignment(project=project, user=user, role=role)
            old_role = None
        else:
            role_as = RoleAssignment.objects.get(project=project, user=user)
            old_role = role_as.role
            role_as.role = role
        role_as.save()

        # Call for additional actions for role creation/update in plugins
        if getattr(settings, 'PROJECTROLES_ENABLE_MODIFY_API', False):
            args = [role_as, action, old_role, request]
            self.call_project_modify_api(
                'perform_role_modify', 'revert_role_modify', args
            )

        if tl_event:
            tl_event.set_status('OK')

        if request.user != user:
            if app_alerts:
                if action == PROJECT_ACTION_CREATE:
                    alert_msg = ROLE_CREATE_MSG
                else:  # Update
                    alert_msg = ROLE_UPDATE_MSG
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='role_' + action.lower(),
                    user=user,
                    message=alert_msg.format(
                        project=project.title, role=role.name
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
            if SEND_EMAIL and app_settings.get(
                APP_NAME, 'notify_email_role', user=user
            ):
                email.send_role_change_mail(
                    'update' if promote else action.lower(),
                    project,
                    user,
                    role,
                    request,
                )
        return role_as


class RoleAssignmentModifyFormMixin(RoleAssignmentModifyMixin, ModelFormMixin):
    """Mixin for RoleAssignment creation and updating in Django form views"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.kwargs.get('promote_as'):
            change_type = 'update'  # If promoting inherited role
        else:
            change_type = self.request.resolver_match.url_name.split('_')[1]
        project = self.get_project()
        if change_type != 'delete':
            context['preview_subject'] = email.get_role_change_subject(
                change_type, project
            )
            context['preview_body'] = email.get_role_change_body(
                change_type=change_type,
                project=project,
                user_name='{user_name}',
                issuer=self.request.user,
                role_name='{role_name}',
                request=self.request,
            ).replace('\n', '\\n')
        return context

    def form_valid(self, form):
        """Handle RoleAssignment updating if form is valid"""
        instance = form.instance if form.instance.pk else None
        action = 'update' if instance else 'create'
        project = self.get_project()
        try:
            self.object = self.modify_assignment(
                data=form.cleaned_data,
                request=self.request,
                project=project,
                instance=form.instance if instance else None,
                promote=True if form.cleaned_data.get('promote') else False,
            )
            messages.success(
                self.request,
                'Membership {} for {} with the role of {}.'.format(
                    'added' if action == 'create' else 'updated',
                    self.object.user.username,
                    self.object.role.name,
                ),
            )
        except Exception as ex:
            messages.error(
                self.request, 'Membership updating failed: {}'.format(ex)
            )
        return redirect(
            reverse(
                'projectroles:roles',
                kwargs={'project': project.sodar_uuid},
            )
        )


class RoleAssignmentDeleteMixin(ProjectModifyPluginViewMixin):
    """Mixin for RoleAssignment deletion/destroying in UI and API views"""

    @classmethod
    def _add_user_alert(cls, app_alerts, project, user, inh_as=None):
        """
        Create app alert for user on role assignment deletion. Creates a new
        alert as appropriate and dismisses alerts in projects the user can no
        longer access.

        :param app_alerts: AppAlertAPI object
        :param project: Project object
        :param user: SODARUser object
        :param inh_as: RoleAssignment object for inherited assignment or None
        """
        if inh_as:
            message = ROLE_UPDATE_MSG.format(
                project=project.title, role=inh_as.role.name
            )
        else:
            message = ROLE_DELETE_MSG.format(
                project_type=get_display_name(project.type)
            )
        app_alerts.add_alert(
            app_name=APP_NAME,
            alert_name='role_{}'.format('update' if inh_as else 'delete'),
            user=user,
            message=message,
            project=project,
        )

    @classmethod
    def _add_leave_alerts(cls, app_alerts, project, user):
        """
        Send alerts to project owners and delegates about user leaving.

        :param app_alerts: AppAlertAPI object
        :param project: Project object
        :param user: SODARUser object
        """
        recipients = [
            a.user
            for a in project.get_roles(
                max_rank=ROLE_RANKING[PROJECT_ROLE_DELEGATE]
            )
            if a.user != user
        ]
        for r in recipients:
            app_alerts.add_alert(
                app_name=APP_NAME,
                alert_name='role_delete_own',
                user=r,
                message=ROLE_LEAVE_MSG.format(
                    user_name=user.username,
                    project_type=get_display_name(project.type),
                ),
                project=project,
            )

    @classmethod
    @transaction.atomic
    def _dismiss_user_alerts(cls, app_alerts, project, user):
        """
        Dismiss user alerts in project and children without local role.

        :param app_alerts: AppAlertAPI object
        :param project: Project object
        :param user: SODARUser object
        """
        AppAlert = app_alerts.get_model()
        dis_projects = [project]
        if project.type == PROJECT_TYPE_CATEGORY:
            for c in project.get_children(flat=True):
                if not c.has_role(user):
                    dis_projects.append(c)
        for a in AppAlert.objects.filter(
            user=user, project__in=dis_projects, active=True
        ):
            a.active = False
            a.save()

    def delete_assignment(self, role_as, request=None, notify=True):
        """
        Delete RoleAssignment. Calls the modify API for additional actions,
        raises app alerts and sends email notifications about the deletion.

        :param role_as: RoleAssingment object
        :param request: HttpRequest object or None
        :param notify: Add app alerts and send email if True
        """
        app_alerts = get_backend_api('appalerts_backend')
        timeline = get_backend_api('timeline_backend')
        tl_event = None
        project = role_as.project
        user = role_as.user
        role = role_as.role

        # Init Timeline event
        if timeline:
            tl_event = timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user if request else None,
                event_name='role_delete',
                description='delete role "{}" from {{{}}}'.format(
                    role.name, 'user'
                ),
            )
            tl_event.add_object(user, 'user', user.username)

        # Call the project plugin modify API for additional actions
        if getattr(settings, 'PROJECTROLES_ENABLE_MODIFY_API', False):
            self.call_project_modify_api(
                'perform_role_delete', 'revert_role_delete', [role_as, request]
            )
        # Delete object itself
        role_as.delete()

        # Delete corresponding PROJECT_USER settings
        if (
            not project.get_role(user)
            and project.type == PROJECT_TYPE_CATEGORY
            and not RoleAssignment.objects.filter(
                project__in=project.get_children(flat=True), user=user
            ).exists()
        ):
            app_settings.delete_by_scope(
                APP_SETTING_SCOPE_PROJECT_USER, project, user
            )

        if tl_event:
            tl_event.set_status(timeline.TL_STATUS_OK)
        if not notify:
            return role_as

        inh_as = project.get_role(user, inherited_only=True)
        if app_alerts:
            if request and request.user == user:
                self._add_leave_alerts(app_alerts, project, user)
            else:
                self._add_user_alert(app_alerts, project, user, inh_as)
            if not inh_as:
                self._dismiss_user_alerts(app_alerts, project, user)
        if SEND_EMAIL and request:
            if request and request.user == user:
                email.send_project_leave_mail(project, user, request)
            elif app_settings.get(APP_NAME, 'notify_email_role', user=user):
                if inh_as:
                    email.send_role_change_mail(
                        'update', project, user, inh_as.role, request
                    )
                else:
                    email.send_role_change_mail(
                        'delete', project, user, None, request
                    )
        return role_as


class RoleAssignmentCreateView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    CurrentUserFormMixin,
    RoleAssignmentModifyFormMixin,
    InvalidFormMixin,
    CreateView,
):
    """RoleAssignment creation view"""

    permission_required = 'projectroles.update_project_members'
    model = RoleAssignment
    form_class = RoleAssignmentForm

    #: Promote assignment
    promote_as = None

    def get_form_kwargs(self):
        """Pass URL arguments and current user to form"""
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['promote_as'] = self.promote_as  # Queried in get()
        return context

    def get(self, request, *args, **kwargs):
        # Validate inherited role promotion if set
        if self.kwargs.get('promote_as'):
            project = self.get_project()
            redirect_url = reverse(
                'projectroles:roles', kwargs={'project': project.sodar_uuid}
            )
            self.promote_as = RoleAssignment.objects.filter(
                sodar_uuid=self.kwargs['promote_as']
            ).first()

            # Check for reached delegate limit
            del_count = RoleAssignment.objects.filter(
                project=project, role__name=PROJECT_ROLE_DELEGATE
            ).count()
            del_limit = settings.PROJECTROLES_DELEGATE_LIMIT
            if (
                self.promote_as
                and self.promote_as.role.rank
                >= ROLE_RANKING[PROJECT_ROLE_CONTRIBUTOR]
                and del_count >= del_limit
            ):
                messages.warning(
                    request,
                    'Local delegate limit ({}) reached, no available roles for '
                    'promotion.'.format(del_limit),
                )
                return redirect(redirect_url)

            # Check for invalid roles
            if (
                not self.promote_as
                or self.promote_as.role.rank
                <= ROLE_RANKING[PROJECT_ROLE_DELEGATE]
                or self.promote_as.project == project
                or self.promote_as.project not in project.get_parents()
            ):
                messages.error(
                    request, 'Invalid role assignment for promotion.'
                )
                return redirect(redirect_url)
        return super().get(request, *args, **kwargs)


class RoleAssignmentUpdateView(
    LoginRequiredMixin,
    RolePermissionMixin,
    ProjectContextMixin,
    RoleAssignmentModifyFormMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    UpdateView,
):
    """RoleAssignment updating view"""

    permission_required = 'projectroles.update_project_members'
    model = RoleAssignment
    form_class = RoleAssignmentForm
    slug_url_kwarg = 'roleassignment'
    slug_field = 'sodar_uuid'


class RoleAssignmentDeleteView(
    LoginRequiredMixin,
    RolePermissionMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    RoleAssignmentDeleteMixin,
    DeleteView,
):
    """RoleAssignment deletion view"""

    permission_required = 'projectroles.update_project_members'
    model = RoleAssignment
    slug_url_kwarg = 'roleassignment'
    slug_field = 'sodar_uuid'

    def _get_inherited_children(self, project, user, ret):
        for child in project.get_children():
            if not RoleAssignment.objects.filter(project=child, user=user):
                ret.append(child)
            else:
                ret = self._get_inherited_children(child, user, ret)
        return ret

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project = self.get_project()
        user = self.object.user
        context['inherited_as'] = project.get_role(user, inherited_only=True)
        context['inherited_children'] = None
        if (
            not context['inherited_as']
            and self.object.role.rank < ROLE_RANKING[PROJECT_ROLE_FINDER]
        ):
            context['inherited_children'] = sorted(
                self._get_inherited_children(project, user, []),
                key=lambda x: x.full_title,
            )
        return context

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        project = self.object.project

        # Override perms for owner/delegate
        if self.object.role.name == PROJECT_ROLE_OWNER or (
            self.object.role.name == PROJECT_ROLE_DELEGATE
            and not self.request.user.has_perm(
                'projectroles.update_project_delegate', project
            )
        ):
            messages.error(
                self.request,
                'You do not have permission to remove the '
                'membership of {}.'.format(self.object.role.name),
            )
        else:
            try:
                self.object = self.delete_assignment(
                    role_as=self.object, request=self.request
                )
                messages.success(
                    self.request,
                    'Membership of {} removed.'.format(user.username),
                )
            except Exception as ex:
                messages.error(
                    self.request,
                    'Failed to remove membership of {}: {}'.format(
                        user.username, ex
                    ),
                )
        return redirect(
            reverse(
                'projectroles:roles', kwargs={'project': project.sodar_uuid}
            )
        )


class RoleAssignmentOwnDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    RoleAssignmentDeleteMixin,
    DeleteView,
):
    """RoleAssignment deletion view for leaving project"""

    model = RoleAssignment
    # Perm overridden in has_permission()
    permission_required = 'projectroles.view_project'
    slug_url_kwarg = 'roleassignment'
    slug_field = 'sodar_uuid'
    template_name = 'projectroles/roleassignment_confirm_delete_own.html'

    def has_permission(self):
        """
        Override has_permission() for one time check for view perms.

        NOTE: Single use case so we're not writing a common rules perm
        """
        role_as = self.get_object()
        user = self.request.user
        if (
            app_settings.get(APP_NAME, 'site_read_only')
            or role_as.user != user
            or role_as.role.rank < ROLE_RANKING[PROJECT_ROLE_DELEGATE]
        ):
            return False
        return True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        role_as = self.get_object()
        user = role_as.user
        children = role_as.project.get_children(flat=True)
        local_child_projects = [
            a.project
            for a in RoleAssignment.objects.filter(
                user=user, project__in=children
            )
        ]
        context['inh_child_projects'] = [
            p for p in children if p not in local_child_projects
        ]
        return context

    def post(self, *args, **kwargs):
        role_as = self.get_object()
        project = role_as.project
        try:
            self.object = self.delete_assignment(
                role_as=role_as, request=self.request
            )
            messages.success(
                self.request, 'Successfully left {}.'.format(project.title)
            )
            return redirect(reverse('home'))
        except Exception as ex:
            messages.error(
                self.request, 'Failed to leave {}: {}'.format(project.title, ex)
            )
            return redirect(
                reverse(
                    'projectroles:roles', kwargs={'project': project.sodar_uuid}
                )
            )


class RoleAssignmentOwnerTransferMixin(ProjectModifyPluginViewMixin):
    """Mixin for owner RoleAssignment transfer in UI and API views"""

    #: Owner role object
    role_owner = None

    def _get_timeline_ok_status(self):
        timeline = get_backend_api('timeline_backend')
        return timeline.TL_STATUS_OK if timeline else None

    def _get_timeline_failed_status(self):
        timeline = get_backend_api('timeline_backend')
        return timeline.TL_STATUS_FAILED if timeline else None

    def _create_timeline_event(
        self, project, old_owner, new_owner, old_owner_role=None, issuer=None
    ):
        """
        Create timeline event for ownership transfer.

        :param project: Project object
        :param old_owner: User object for old owner
        :param new_owner: User object for new_owner
        :param old_owner_role: Role object for old owner's new role or None
        :param issuer: User who initiated ownership transfer or None
        """
        timeline = get_backend_api('timeline_backend')
        if not timeline:
            return None
        tl_desc = 'transfer ownership from {prev_owner} to {new_owner}, '
        if old_owner_role:
            tl_desc += 'set old owner as "{}"'.format(old_owner_role.name)
        else:
            tl_desc += 'remove old owner role'
        tl_event = timeline.add_event(
            project=project,
            app_name=APP_NAME,
            user=issuer,
            event_name='role_owner_transfer',
            description=tl_desc,
            extra_data={
                'prev_owner': old_owner.username,
                'new_owner': new_owner.username,
                'old_owner_role': (
                    old_owner_role.name if old_owner_role else None
                ),
            },
        )
        tl_event.add_object(old_owner, 'prev_owner', old_owner.username)
        tl_event.add_object(new_owner, 'new_owner', new_owner.username)
        return tl_event

    @transaction.atomic
    def _handle_transfer(
        self,
        project,
        old_owner_as,
        new_owner,
        old_inh_owner,
        old_owner_role=None,
        request=None,
    ):
        """
        Handle ownership transfer with atomic rollback.

        :param project: Project object
        :param old_owner_as: RoleAssignment object for old owner
        :param new_owner: User object for new user
        :param old_inh_owner: Whether old owner is inherited owner (boolean)
        :param old_owner_role: Role object to set for old owner or None
        :param request: HttpRequest object or None
        """
        # Inherited owner or no new role for old owner: delete local role
        if old_inh_owner or not old_owner_role:
            old_owner_as.delete()
        # Update old owner role
        else:
            old_owner_as.role = old_owner_role
            old_owner_as.save()
        # Update or create new owner role
        new_role_as = RoleAssignment.objects.filter(
            project=project, user=new_owner
        ).first()
        if new_role_as:
            new_role_as.role = self.role_owner
            new_role_as.save()
        else:
            RoleAssignment.objects.create(
                project=project, user=new_owner, role=self.role_owner
            )
        # Call for additional actions for role creation/update in plugins
        if getattr(settings, 'PROJECTROLES_ENABLE_MODIFY_API', False):
            args = [
                project,
                new_owner,
                old_owner_as.user,
                old_owner_role,
                request,
            ]
            self.call_project_modify_api(
                'perform_owner_transfer', 'revert_owner_transfer', args
            )
        return True

    def transfer_owner(
        self,
        project,
        new_owner,
        old_owner_as,
        old_owner_role=None,
        request=None,
        notify_old=True,
    ):
        """
        Transfer project ownership to a new user and assign a new role to the
        previous owner.

        :param project: Project object
        :param new_owner: User object
        :param old_owner_as: RoleAssignment object
        :param old_owner_role: Role object for old owner's new role or None
        :param request: HttpRequest object or None
        :param notify_old: Notify old owner (boolean, default=True)
        """
        app_alerts = get_backend_api('appalerts_backend')
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        old_owner = old_owner_as.user
        # Old owner inheritance
        old_inh_as = project.get_role(old_owner, inherited_only=True)
        old_inh_owner = (
            True if old_inh_as and old_inh_as.role == self.role_owner else False
        )
        # New owner inheritance
        new_inh_as = project.get_role(new_owner, inherited_only=True)
        new_inh_owner = (
            True if new_inh_as and new_inh_as.role == self.role_owner else False
        )
        issuer = request.user if request else None
        tl_event = self._create_timeline_event(
            project, old_owner, new_owner, old_owner_role, issuer
        )

        try:
            self._handle_transfer(
                project,
                old_owner_as,
                new_owner,
                old_inh_owner,
                old_owner_role,
                request,
            )
        except Exception as ex:
            if tl_event:
                tl_event.set_status(self._get_timeline_failed_status(), str(ex))
            raise ex

        if tl_event:
            tl_event.set_status(self._get_timeline_ok_status())
        # Notify old owner
        if notify_old and not old_inh_owner and issuer != old_owner:
            if app_alerts:
                if old_owner_role:
                    alert_name = 'role_update'
                    message = ROLE_UPDATE_MSG.format(
                        project=project.title, role=old_owner_role.name
                    )
                    alert_url = reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    )
                else:
                    alert_name = 'role_delete'
                    message = ROLE_DELETE_MSG.format(
                        project_type=get_display_name(project.type)
                    )
                    alert_url = None
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name=alert_name,
                    user=old_owner,
                    message=message,
                    url=alert_url,
                    project=project,
                )
            if (
                SEND_EMAIL
                and request
                and app_settings.get(
                    APP_NAME, 'notify_email_role', user=old_owner
                )
            ):
                # NOTE: Request is needed here
                email.send_role_change_mail(
                    'update' if old_owner_role else 'delete',
                    project,
                    old_owner,
                    old_owner_role,
                    request,
                )
        # Notify new owner
        if not new_inh_owner and issuer != new_owner:
            if app_alerts:
                app_alerts.add_alert(
                    app_name=APP_NAME,
                    alert_name='role_update',
                    user=new_owner,
                    message=ROLE_UPDATE_MSG.format(
                        project=project.title, role=self.role_owner.name
                    ),
                    url=reverse(
                        'projectroles:detail',
                        kwargs={'project': project.sodar_uuid},
                    ),
                    project=project,
                )
            if (
                SEND_EMAIL
                and request
                and app_settings.get(
                    APP_NAME, 'notify_email_role', user=new_owner
                )
            ):
                # NOTE: Request is needed here
                email.send_role_change_mail(
                    'update',
                    project,
                    new_owner,
                    self.role_owner,
                    request,
                )


class RoleAssignmentOwnerTransferView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    CurrentUserFormMixin,
    ProjectContextMixin,
    RoleAssignmentOwnerTransferMixin,
    InvalidFormMixin,
    FormView,
):
    """Project owner RoleAssignment transfer view"""

    permission_required = 'projectroles.update_project_owner'
    template_name = 'projectroles/roleassignment_owner_transfer.html'
    form_class = RoleAssignmentOwnerTransferForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project = self.get_project()
        owner_as = RoleAssignment.objects.filter(
            project=project, role__name=PROJECT_ROLE_OWNER
        )[0]
        kwargs.update({'project': project, 'current_owner': owner_as.user})
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        owner_as = RoleAssignment.objects.filter(
            project=self.get_project(), role__name=PROJECT_ROLE_OWNER
        )[0]
        context.update({'current_owner': owner_as.user})
        return context

    def form_valid(self, form):
        project = form.project
        old_owner = form.current_owner
        old_owner_as = project.get_owner()
        new_owner = form.cleaned_data['new_owner']
        old_owner_role = form.cleaned_data['old_owner_role']
        redirect_url = reverse(
            'projectroles:roles', kwargs={'project': project.sodar_uuid}
        )
        try:
            self.transfer_owner(
                project,
                new_owner,
                old_owner_as,
                old_owner_role,
                request=self.request,
            )
        except Exception as ex:
            # TODO: Add logging
            messages.error(
                self.request, 'Unable to transfer ownership: {}'.format(ex)
            )
            if settings.DEBUG:
                raise ex
            return redirect(redirect_url)
        if old_owner.username != new_owner.username:
            success_msg = (
                'Successfully transferred ownership from '
                '{} to {}.'.format(old_owner.username, new_owner.username)
            )
            old_owner_email = app_settings.get(
                APP_NAME, 'notify_email_role', user=old_owner
            )
            new_owner_email = app_settings.get(
                APP_NAME, 'notify_email_role', user=new_owner
            )
            if SEND_EMAIL and (old_owner_email or new_owner_email):
                success_msg += ' Notification(s) have been sent by email.'
            messages.success(self.request, success_msg)
        return redirect(redirect_url)


# ProjectInvite Views ----------------------------------------------------------


class ProjectInviteMixin:
    """Mixin for ProjectInvite helpers"""

    @classmethod
    def handle_invite(cls, invite, request, resend=False, add_message=True):
        """
        Handle invite creation, email sending/resending and logging to timeline.

        :param invite: ProjectInvite object
        :param request: Django request object
        :param resend: Send or resend (bool)
        :param add_message: Add Django message on success/failure (bool)
        """
        timeline = get_backend_api('timeline_backend')
        send_str = 'resend' if resend else 'send'
        status_type = timeline.TL_STATUS_OK
        status_desc = None

        if SEND_EMAIL:
            sent_mail = email.send_invite_mail(invite, request)
            if sent_mail == 0:
                status_type = timeline.TL_STATUS_FAILED
                status_desc = 'Email sending failed'
        else:
            status_type = timeline.TL_STATUS_FAILED
            status_desc = 'PROJECTROLES_SEND_EMAIL not True'
        if status_type != timeline.TL_STATUS_OK and not resend:
            status_desc += ', invite not created'

        # Add event in Timeline
        if timeline:
            timeline.add_event(
                project=invite.project,
                app_name=APP_NAME,
                user=request.user,
                event_name='invite_{}'.format(send_str),
                description='{} project invite with role "{}" to {}'.format(
                    send_str, invite.role.name, invite.email
                ),
                status_type=status_type,
                status_desc=status_desc,
            )

        if add_message and status_type == timeline.TL_STATUS_OK:
            messages.success(
                request,
                'Invite for "{}" role in {} sent to {}, expires on {}.'.format(
                    invite.role.name,
                    invite.project.title,
                    invite.email,
                    timezone.localtime(invite.date_expire).strftime(
                        '%Y-%m-%d %H:%M'
                    ),
                ),
            )
        elif add_message and not resend:  # NOTE: Delete invite if send fails
            invite.delete()
            messages.error(request, status_desc)

    @classmethod
    def revoke_invite(cls, invite, project, request):
        timeline = get_backend_api('timeline_backend')
        if invite:
            invite.active = False
            invite.save()
        # Add event in Timeline
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name='invite_revoke',
                description='revoke invite sent to "{}"'.format(
                    invite.email if invite else 'N/A'
                ),
                status_type=(
                    timeline.TL_STATUS_OK
                    if invite
                    else timeline.TL_STATUS_FAILED
                ),
            )
        return invite


class ProjectInviteView(
    LoginRequiredMixin,
    ProjectContextMixin,
    ProjectModifyPermissionMixin,
    TemplateView,
):
    """View for displaying and modifying project invites"""

    permission_required = 'projectroles.invite_users'
    template_name = 'projectroles/project_invites.html'
    model = ProjectInvite

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['invites'] = ProjectInvite.objects.filter(
            project=context['project'],
            active=True,
            date_expire__gt=timezone.now(),
        )
        return context


class ProjectInviteCreateView(
    LoginRequiredMixin,
    ProjectContextMixin,
    ProjectModifyPermissionMixin,
    ProjectInviteMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    CreateView,
):
    """ProjectInvite creation view"""

    model = ProjectInvite
    form_class = ProjectInviteForm
    permission_required = 'projectroles.invite_users'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project = self.get_permission_object()
        context['preview_subject'] = email.get_invite_subject(project)
        context['preview_body'] = email.get_invite_body(
            project=project,
            issuer=self.request.user,
            role_name='{role_name}',
            invite_url='http://XXXXXXXXXXXXXXXXXXXXXXX',
            date_expire_str='YYYY-MM-DD HH:MM',
        ).replace('\n', '\\n')
        context['preview_message'] = email.get_invite_message(
            '{message}'
        ).replace('\n', '\\n')
        context['preview_footer'] = email.get_email_footer(
            self.request
        ).replace('\n', '\\n')
        return context

    def get_form_kwargs(self):
        """Pass current user and optional email/role to form"""
        kwargs = super().get_form_kwargs()
        kwargs.update({'project': self.get_permission_object().sodar_uuid})
        email = self.request.GET.get('e', None)
        kwargs.update({'mail': unquote_plus(email) if email else None})
        kwargs.update({'role': self.request.GET.get('r', None)})
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        # Send mail and add to timeline
        self.handle_invite(invite=self.object, request=self.request)
        return redirect(
            reverse(
                'projectroles:invites',
                kwargs={'project': self.object.project.sodar_uuid},
            )
        )


class ProjectInviteProcessMixin(ProjectModifyPluginViewMixin):
    """Mixin for accepting and processing project invites"""

    @classmethod
    def revoke_invite(
        cls, invite, user=None, failed=True, fail_desc='', timeline=None
    ):
        """Set invite.active to False and save the invite"""
        invite.active = False
        invite.save()
        if failed and timeline and user:
            # Add event in Timeline
            timeline.add_event(
                project=invite.project,
                app_name=APP_NAME,
                user=user,
                event_name='invite_accept',
                description='accept project invite',
                status_type=timeline.TL_STATUS_FAILED,
                status_desc=fail_desc,
            )

    def get_invite(self, secret):
        """Get invite, display message if not found"""
        try:
            return ProjectInvite.objects.get(secret=secret)
        except ProjectInvite.DoesNotExist:
            messages.error(self.request, 'Invite does not exist.')

    def user_role_exists(self, invite, user):
        """
        Display message if user already has roles in project. Also revoke the
        invite if necessary.
        """
        if invite.project.has_role(user):
            messages.warning(
                self.request,
                mark_safe(
                    'You are already a member of this {project}. '
                    '<a href="{url}">Please use this URL to access the '
                    '{project}</a>.'.format(
                        project=get_display_name(invite.project.type),
                        url=reverse(
                            'projectroles:detail',
                            kwargs={'project': invite.project.sodar_uuid},
                        ),
                    )
                ),
            )
            if invite.active:  # Only revoke if active
                self.revoke_invite(invite, user)
            return True
        return False

    def is_invite_expired(self, invite, user=None):
        """Display message and send email to issuer if invite is expired"""
        if invite.date_expire < timezone.now():
            messages.error(
                self.request,
                'Your invite has expired. Please contact the inviter: '
                '{} ({})'.format(invite.issuer.name, invite.issuer.email),
            )
            # Send notification of expiry to issuer
            if SEND_EMAIL and app_settings.get(
                APP_NAME, 'notify_email_role', user=invite.issuer
            ):
                email.send_expiry_note(
                    invite,
                    self.request,
                    user_name=user.get_full_name() if user else invite.email,
                )
            self.revoke_invite(
                invite, user, failed=True, fail_desc='Invite expired'
            )
            return True
        return False

    # TODO: Combine with RoleAssignmentModifyMixin.modify_assignment?
    @transaction.atomic
    def create_assignment(self, invite, user, timeline=None):
        """Create role assignment for invited user"""
        app_alerts = get_backend_api('appalerts_backend')
        tl_event = None
        if timeline:
            tl_event = timeline.add_event(
                project=invite.project,
                app_name=APP_NAME,
                user=user,
                event_name='invite_accept',
                description='accept project invite with role of "{}"'.format(
                    invite.role.name
                ),
            )

        # Create the assignment
        role_as = RoleAssignment(
            user=user, project=invite.project, role=invite.role
        )
        # Call for additional actions for role creation/update in plugins
        if getattr(settings, 'PROJECTROLES_ENABLE_MODIFY_API', False):
            args = [role_as, PROJECT_ACTION_CREATE, None, self.request]
            self.call_project_modify_api(
                'perform_role_modify', 'revert_role_modify', args
            )
        role_as.save()
        if tl_event:
            tl_event.set_status(timeline.TL_STATUS_OK)

        # Notify the issuer by alert and email
        if app_alerts:
            app_alerts.add_alert(
                app_name=APP_NAME,
                alert_name='invite_accept',
                user=invite.issuer,
                message='Invitation sent to "{}" for project "{}" with the '
                'role "{}" was accepted.'.format(
                    user.email, invite.project.title, invite.role.name
                ),
                url=reverse(
                    'projectroles:detail',
                    kwargs={'project': invite.project.sodar_uuid},
                ),
                project=invite.project,
            )
        if SEND_EMAIL and app_settings.get(
            APP_NAME, 'notify_email_role', user=invite.issuer
        ):
            email.send_accept_note(invite, self.request, user)

        # Deactivate the invite
        self.revoke_invite(invite, user, failed=False, timeline=timeline)
        # Finally, redirect user to the project front page
        messages.success(
            self.request,
            PROJECT_WELCOME_MSG.format(
                project_type=get_display_name(invite.project.type),
                project_title=invite.project.title,
                role=invite.role.name,
            ),
        )

    def redirect_error(self, msg=None):
        if msg:
            messages.error(self.request, msg)
        return redirect(reverse('home'))


class ProjectInviteAcceptView(ProjectInviteProcessMixin, View):
    """View to handle accepting a project invite"""

    def _redirect_process(self, login=True):
        """Redirect to the proper process view"""
        url = 'projectroles:invite_process_{}'.format(
            'login' if login else 'new_user'
        )
        kw = {'secret': self.kwargs.get('secret')}
        return redirect(reverse(url, kwargs=kw))

    def get(self, *args, **kwargs):
        invite = self.get_invite(secret=kwargs['secret'])
        if not invite:
            return self.redirect_error(INVITE_NOT_FOUND_MSG)
        user = self.request.user
        if (
            not user.is_anonymous
            and user.is_authenticated
            and user.email == invite.email
            and self.user_role_exists(invite, user)
        ):
            return redirect(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': invite.project.sodar_uuid},
                )
            )
        if (settings.ENABLE_LDAP and invite.is_ldap()) or (
            settings.ENABLE_OIDC and not settings.PROJECTROLES_ALLOW_LOCAL_USERS
        ):
            return self._redirect_process()
        elif settings.PROJECTROLES_ALLOW_LOCAL_USERS:
            return self._redirect_process(False)
        return self.redirect_error(
            'Local or OIDC users are not enabled on this site.'
        )


class ProjectInviteProcessLoginView(
    LoginRequiredMixin, ProjectInviteProcessMixin, View
):
    """
    View for processing project invite with a logged in LDAP/OIDC user. Requires
    login and then creates project assignment for the invited user.
    """

    def get(self, *args, **kwargs):
        invite = self.get_invite(kwargs['secret'])
        if not invite:
            return self.redirect_error(INVITE_NOT_FOUND_MSG)
        timeline = get_backend_api('timeline_backend')
        # Check if user has already accepted the invite
        if self.user_role_exists(invite, self.request.user):
            # NOTE: No message, simply redirect
            return redirect(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': invite.project.sodar_uuid},
                )
            )
        # Check if invite expired
        if self.is_invite_expired(invite, self.request.user):
            return self.redirect_error()
        # Create RoleAssignment
        try:
            self.create_assignment(invite, self.request.user, timeline=timeline)
        except Exception as ex:
            return self.redirect_error(ex)
        return redirect(
            reverse(
                'projectroles:detail',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )


class ProjectInviteProcessNewUserView(ProjectInviteProcessMixin, FormView):
    """
    View for processing a local/OIDC project invite as a newly created user.
    Also provides an OIDC login element to login instead of creating a local
    user account.
    """

    form_class = LocalUserForm
    template_name = 'projectroles/user_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invite'] = self.get_invite(self.kwargs['secret'])
        return context

    def get(self, *args, **kwargs):
        invite = self.get_invite(self.kwargs['secret'])
        if not invite:
            return self.redirect_error(INVITE_NOT_FOUND_MSG)
        timeline = get_backend_api('timeline_backend')
        # Redirect to login process view if OIDC is enabled but local isn't
        if settings.ENABLE_OIDC and not settings.PROJECTROLES_ALLOW_LOCAL_USERS:
            return redirect(
                reverse(
                    'projectroles:invite_process_login',
                    kwargs={'secret': invite.secret},
                )
            )
        # If local users are not allowed but OIDC is, redirect to home
        elif not settings.PROJECTROLES_ALLOW_LOCAL_USERS:
            return self.redirect_error(INVITE_LOCAL_NOT_ALLOWED_MSG)
        # Check invite for correct type
        if invite.is_ldap():
            return self.redirect_error(INVITE_LDAP_LOCAL_VIEW_MSG)
        # Check if invited user exists
        user = User.objects.filter(email=invite.email).first()
        # Check if invite has expired
        if self.is_invite_expired(invite, user):
            return self.redirect_error()  # Error message already added

        # A user is not logged in
        if self.request.user.is_anonymous:
            # Redirect to login if user exists
            if user:
                messages.info(self.request, INVITE_USER_EXISTS_MSG)
                return redirect(
                    reverse('login')
                    + '?next='
                    + reverse(
                        'projectroles:invite_process_new_user',
                        kwargs={'secret': invite.secret},
                    )
                )
            # Show form if user doesn't exist and no user is logged in
            return super().get(*args, **kwargs)
        # Logged in but the invited user does not exist yet
        if not user:
            return self.redirect_error(INVITE_LOGGED_IN_ACCEPT_MSG)
        # Logged in user is not invited user
        if self.request.user != user:
            return self.redirect_error(INVITE_USER_NOT_EQUAL_MSG)
        # User exists but is not local
        if not user.is_local():
            return self.redirect_error('User exists, but is not local.')
        # Create RoleAssignment
        try:
            self.create_assignment(invite, self.request.user, timeline=timeline)
        except Exception as ex:
            return self.redirect_error(ex)
        return redirect(
            reverse(
                'projectroles:detail',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )

    def get_initial(self):
        """Returns the initial data for the form."""
        initial = super().get_initial()
        try:
            invite = ProjectInvite.objects.get(secret=self.kwargs['secret'])
        except ProjectInvite.DoesNotExist:
            return initial
        username_base = invite.email.split('@')[0]
        i = 0
        while True:
            username = username_base + str(i if i else '')
            try:
                User.objects.get(username=username)
                i += 1
            except User.DoesNotExist:
                break
        initial.update({'email': invite.email, 'username': username})
        return initial

    def form_valid(self, form):
        invite = self.get_invite(self.kwargs['secret'])
        if not invite:
            return redirect(reverse('home'))
        timeline = get_backend_api('timeline_backend')

        # Check if local users are allowed
        if not settings.PROJECTROLES_ALLOW_LOCAL_USERS:
            return self.redirect_error(
                'Invite was issued to non-LDAP user, but local users are not '
                'allowed.'
            )
        # Check invite for correct type
        if invite.is_ldap():
            return self.redirect_error(
                'Invite was issued for LDAP user, but local invite view was '
                'requested.'
            )
        # Check if invite is expired
        if self.is_invite_expired(invite):
            return self.redirect_error()

        # Create user and RoleAssignment
        user = User.objects.create_user(
            form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
        )
        if self.user_role_exists(invite, user):
            return redirect(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': invite.project.sodar_uuid},
                )
            )
        try:
            self.create_assignment(invite, user, timeline=timeline)
        except Exception as ex:
            user.delete()
            return self.redirect_error(ex)
        return redirect(
            reverse(
                'projectroles:detail',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )


class ProjectInviteResendView(
    LoginRequiredMixin, ProjectModifyPermissionMixin, ProjectInviteMixin, View
):
    """View to handle resending a project invite"""

    permission_required = 'projectroles.invite_users'

    def get(self, *args, **kwargs):
        try:
            invite = ProjectInvite.objects.get(
                sodar_uuid=self.kwargs['projectinvite'], active=True
            )
        except ProjectInvite.DoesNotExist:
            messages.error(self.request, INVITE_NOT_FOUND_MSG)
            return redirect(
                reverse(
                    'projectroles:invites',
                    kwargs={'project': self.get_project()},
                )
            )
        # Reset invite expiration date
        invite.reset_date_expire()
        # Resend mail and add to timeline
        self.handle_invite(invite=invite, request=self.request, resend=True)
        return redirect(
            reverse(
                'projectroles:invites',
                kwargs={'project': invite.project.sodar_uuid},
            )
        )


class ProjectInviteRevokeView(
    LoginRequiredMixin,
    ProjectModifyPermissionMixin,
    ProjectContextMixin,
    ProjectInviteMixin,
    TemplateView,
):
    """Batch delete/move confirm view"""

    template_name = 'projectroles/invite_revoke_confirm.html'
    permission_required = 'projectroles.invite_users'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['project'] = self.get_project()
        if 'projectinvite' in self.kwargs:
            try:
                context['invite'] = ProjectInvite.objects.get(
                    sodar_uuid=self.kwargs['projectinvite']
                )
            except ProjectInvite.DoesNotExist:
                pass
        return context

    def post(self, request, **kwargs):
        """Override post() to handle POST from confirmation template"""
        project = self.get_project()
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()
        if (
            invite
            and invite.role.name == PROJECT_ROLE_DELEGATE
            and not request.user.has_perm(
                'projectroles.update_project_delegate', project
            )
        ):
            # Causes revoke_failed_invite() to add failed timeline event
            invite = None
            messages.error(
                self.request, 'No permissions for updating delegate invite.'
            )
        elif invite:
            messages.success(self.request, 'Invite revoked.')
        else:
            messages.error(self.request, 'Invite not found.')
        self.revoke_invite(invite, project, request)
        return redirect(
            reverse(
                'projectroles:invites', kwargs={'project': project.sodar_uuid}
            )
        )


# User management views --------------------------------------------------------


class UserUpdateView(
    LoginRequiredMixin, HTTPRefererMixin, InvalidFormMixin, UpdateView
):
    """Display and process the user update view"""

    form_class = LocalUserForm
    template_name = 'projectroles/user_form.html'
    success_url = reverse_lazy('home')

    def get_object(self, **kwargs):
        return self.request.user

    def get(self, *args, **kwargs):
        if not self.request.user.is_local():
            messages.error(self.request, USER_PROFILE_LDAP_MSG)
            return redirect(reverse('home'))
        return super().get(*args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, USER_PROFILE_UPDATE_MSG)
        return reverse('home')


# Site App Setting management --------------------------------------------------


class SiteAppSettingsView(
    LoginRequiredMixin, LoggedInPermissionMixin, InvalidFormMixin, FormView
):
    """Site app settings form view"""

    form_class = SiteAppSettingsForm
    permission_required = 'projectroles.update_site_settings'
    success_url = reverse_lazy('projectroles:site_app_settings')
    template_name = 'projectroles/siteappsettings_form.html'

    def form_valid(self, form):
        result = super().form_valid(form)
        for k, v in form.cleaned_data.items():
            if k.startswith('settings.'):
                _, plugin_name, setting_name = k.split('.', 3)
                app_settings.set(plugin_name, setting_name, v)
        messages.success(self.request, SITE_SETTING_UPDATE_MSG)
        return result


# Remote site and project views ------------------------------------------------


class RemoteSiteListView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """Main view for displaying remote site list"""

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remote_sites.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        site_mode = (
            SITE_MODE_TARGET
            if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE
            else SITE_MODE_SOURCE
        )
        sites = RemoteSite.objects.filter(mode=site_mode).order_by('name')
        if (
            sites.count() > 0
            and settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
        ):
            sites = sites[:1]
        context['sites'] = sites
        return context

    # TODO: Remove this once implementing #76
    def get(self, request, *args, **kwargs):
        if getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False):
            messages.warning(
                request,
                '{} {} and nesting disabled, '
                'remote {} sync disabled.'.format(
                    get_display_name(PROJECT_TYPE_PROJECT, title=True),
                    get_display_name(PROJECT_TYPE_CATEGORY, plural=True),
                    get_display_name(PROJECT_TYPE_PROJECT),
                ),
            )
            return redirect('home')
        return super().get(request, *args, **kwargs)


class RemoteSiteModifyMixin(ModelFormMixin):
    """Helpers for remote site modification"""

    def _create_timeline_event(self, remote_site, user, form_action):
        """
        Create timeline event for remote site creation/update.

        :param remote_site: RemoteSite object
        :param user: SODARUser object
        :param form_action: String
        :param form_action:
        """
        timeline = get_backend_api('timeline_backend')
        if not timeline:
            return
        status = form_action if form_action == 'set' else form_action[0:-1]
        if remote_site.mode == SITE_MODE_SOURCE:
            event_name = 'source_site_{}'.format(status)
        else:
            event_name = 'target_site_{}'.format(status)

        tl_desc = '{} remote {} site {{{}}}'.format(
            status,
            remote_site.mode.lower(),
            'remote_site',
        )
        tl_event = timeline.add_event(
            project=None,
            app_name=APP_NAME,
            user=user,
            event_name=event_name,
            description=tl_desc,
            classified=True,
            extra_data={
                'name': remote_site.name,
                'url': remote_site.url,
                'description': remote_site.description,
                'mode': remote_site.mode,
                'user display': remote_site.user_display,
                'secret': remote_site.secret,
            },
            status_type=timeline.TL_STATUS_OK,
        )
        tl_event.add_object(
            obj=remote_site, label='remote_site', name=remote_site.name
        )

    def form_valid(self, form):
        """Override form_valid() to save timeline event and handle UI"""
        if self.object:
            form_action = 'updated'
        elif settings.PROJECTROLES_SITE_MODE == 'TARGET':
            form_action = 'set'
        else:
            form_action = 'created'
        self.object = form.save()
        # Create timeline event
        self._create_timeline_event(self.object, self.request.user, form_action)
        messages.success(
            self.request,
            '{} site "{}" {}.'.format(
                self.object.mode.capitalize(), self.object.name, form_action
            ),
        )
        return redirect(reverse('projectroles:remote_sites'))


class RemoteSiteCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    RemoteSiteModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    CreateView,
):
    """RemoteSite creation view"""

    model = RemoteSite
    form_class = RemoteSiteForm
    permission_required = 'projectroles.update_remote'

    def get(self, request, *args, **kwargs):
        """
        Override get() to disallow rendering this view if current site is
        in TARGET mode and a source site already exists.
        """
        if (
            settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and RemoteSite.objects.filter(mode=SITE_MODE_SOURCE).count() > 0
        ):
            messages.error(request, 'Source site has already been set')
            return redirect(reverse('projectroles:remote_sites'))
        return super().get(request, args, kwargs)


class RemoteSiteUpdateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    RemoteSiteModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    UpdateView,
):
    """RemoteSite updating view"""

    model = RemoteSite
    form_class = RemoteSiteForm
    permission_required = 'projectroles.update_remote'
    slug_url_kwarg = 'remotesite'
    slug_field = 'sodar_uuid'


class RemoteSiteDeleteView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    DeleteView,
):
    """RemoteSite deletion view"""

    model = RemoteSite
    permission_required = 'projectroles.update_remote'
    slug_url_kwarg = 'remotesite'
    slug_field = 'sodar_uuid'

    def get_success_url(self):
        timeline = get_backend_api('timeline_backend')
        if timeline:
            event_name = '{}_site_delete'.format(
                'source' if self.object.mode == SITE_MODE_SOURCE else 'target'
            )
            tl_desc = 'delete remote site {remote_site}'
            tl_event = timeline.add_event(
                project=None,
                app_name=APP_NAME,
                user=self.request.user,
                event_name=event_name,
                description=tl_desc,
                classified=True,
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=self.object, label='remote_site', name=self.object.name
            )
        messages.success(
            self.request,
            '{} site "{}" deleted'.format(
                self.object.mode.capitalize(), self.object.name
            ),
        )
        return reverse('projectroles:remote_sites')


class RemoteProjectListView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """View for displaying the project lsit for remote site sync"""

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remote_projects.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        site = RemoteSite.objects.get(sodar_uuid=self.kwargs['remotesite'])
        context['site'] = site
        # Projects in SOURCE mode: all local projects of type PROJECT
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            projects = Project.objects.filter(type=PROJECT_TYPE_PROJECT)
        # Projects in TARGET mode: retrieve from source
        else:  # SITE_MODE_TARGET
            remote_uuids = [p.project_uuid for p in site.projects.all()]
            projects = Project.objects.filter(
                type=PROJECT_TYPE_PROJECT, sodar_uuid__in=remote_uuids
            )
        if projects:
            context['projects'] = projects.order_by('full_title')
        return context


class RemoteProjectBatchUpdateView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """
    Manually created form view for updating project access in batch for a
    remote target site.
    """

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remoteproject_update.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # Current site
        context['site'] = RemoteSite.objects.filter(
            sodar_uuid=kwargs['remotesite']
        ).first()
        return context

    def post(self, request, *args, **kwargs):
        timeline = get_backend_api('timeline_backend')
        post_data = request.POST
        context = self.get_context_data(*args, **kwargs)
        site = context['site']
        confirmed = True if 'update-confirmed' in post_data else False
        redirect_url = reverse(
            'projectroles:remote_projects',
            kwargs={'remotesite': site.sodar_uuid},
        )
        # Ensure site is in SOURCE mode
        if settings.PROJECTROLES_SITE_MODE != SITE_MODE_SOURCE:
            messages.error(
                request,
                'Site in TARGET mode, cannot update {} access'.format(
                    get_display_name(PROJECT_TYPE_PROJECT)
                ),
            )
            return redirect(redirect_url)
        access_fields = {
            k: v for k, v in post_data.items() if k.startswith('remote_access')
        }

        # Confirmation needed
        if not confirmed:
            # Pass on (only) changed projects to confirmation form
            modifying_access = []
            for k, v in access_fields.items():
                project_uuid = k.split('_')[2]
                remote_obj = RemoteProject.objects.filter(
                    site=site, project_uuid=project_uuid
                ).first()
                if (not remote_obj and v != REMOTE_LEVEL_NONE) or (
                    remote_obj and remote_obj.level != v
                ):
                    modifying_access.append(
                        {
                            'project': Project.objects.get(
                                sodar_uuid=project_uuid
                            ),
                            'old_level': (
                                REMOTE_LEVEL_NONE
                                if not remote_obj
                                else remote_obj.level
                            ),
                            'new_level': v,
                        }
                    )
            if not modifying_access:
                messages.warning(
                    request,
                    'No changes to {} access detected'.format(
                        get_display_name(PROJECT_TYPE_PROJECT)
                    ),
                )
                return redirect(redirect_url)
            context['modifying_access'] = modifying_access
            return super().render_to_response(context)

        # Confirmed
        modifying_access = []
        old_level = REMOTE_LEVEL_NONE

        for k, v in access_fields.items():
            project_uuid = k.split('_')[2]
            project = Project.objects.filter(sodar_uuid=project_uuid).first()
            # Update or create a RemoteProject object
            try:
                rp = RemoteProject.objects.get(
                    site=site, project_uuid=project_uuid
                )
                old_level = rp.level
                rp.level = v
            except RemoteProject.DoesNotExist:
                rp = RemoteProject(
                    site=site,
                    project_uuid=project_uuid,
                    project=project,
                    level=v,
                )
            rp.save()

            modifying_access.append(
                {
                    'project': project.get_log_title(),
                    'old_level': (
                        REMOTE_LEVEL_NONE if not old_level else old_level
                    ),
                    'new_level': v,
                }
            )

            if timeline and project:
                tl_desc = 'update remote access on site {{{}}} to "{}"'.format(
                    'remote_site',
                    SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'][v].lower(),
                )
                tl_event = timeline.add_event(
                    project=project,
                    app_name=APP_NAME,
                    user=request.user,
                    event_name='remote_project_update',
                    description=tl_desc,
                    classified=True,
                    status_type=timeline.TL_STATUS_OK,
                )
                tl_event.add_object(site, 'remote_site', site.name)

        if timeline:
            tl_desc = 'update remote projects for {remote_site}'
            tl_event = timeline.add_event(
                project=None,
                app_name=APP_NAME,
                user=request.user,
                event_name='remote_batch_update',
                description=tl_desc,
                extra_data={'modifying_access': modifying_access},
                classified=True,
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(obj=site, label='remote_site', name=site.name)

        # All OK
        messages.success(
            request,
            'Access level updated for {} {} in site "{}"'.format(
                len(access_fields.items()),
                get_display_name(
                    PROJECT_TYPE_PROJECT, count=len(access_fields.items())
                ),
                context['site'].name,
            ),
        )
        return redirect(redirect_url)


class RemoteProjectSyncView(
    LoginRequiredMixin, LoggedInPermissionMixin, TemplateView
):
    """Target site view for synchronizing remote projects from a source site"""

    permission_required = 'projectroles.update_remote'
    template_name = 'projectroles/remoteproject_sync.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # Current site
        context['site'] = RemoteSite.objects.filter(
            sodar_uuid=kwargs['remotesite']
        ).first()
        return context

    def get(self, request, *args, **kwargs):
        """Override get() for a confirmation view"""
        redirect_url = reverse('projectroles:remote_sites')
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            messages.error(
                request, 'Site in SOURCE mode, remote sync not allowed'
            )
            return redirect(redirect_url)

        timeline = get_backend_api('timeline_backend')
        remote_api = RemoteProjectAPI()
        context = self.get_context_data(*args, **kwargs)
        source_site = context['site']

        try:
            remote_data = remote_api.get_remote_data(source_site)
        except Exception as ex:
            messages.error(
                request,
                'Unable to synchronize {}: {}'.format(
                    get_display_name(PROJECT_TYPE_PROJECT, plural=True), ex
                ),
            )
            return redirect(redirect_url)

        # Sync data
        try:
            update_data = remote_api.sync_remote_data(
                source_site, remote_data, request
            )
        except Exception as ex:
            messages.error(
                request, 'Remote sync cancelled with exception: {}'.format(ex)
            )
            if settings.DEBUG:
                raise ex
            return redirect(redirect_url)

        # Check for updates
        user_count = len(
            [v for v in update_data['users'].values() if 'status' in v]
        )
        project_count = len(
            [v for v in update_data['projects'].values() if 'status' in v]
        )
        app_settings_count = len(
            [
                v
                for v in update_data['app_settings'].values()
                if 'status' in v and v['status'] != 'skipped'
            ]
        )
        role_count = 0
        for p in [p for p in update_data['projects'].values() if 'roles' in p]:
            for _ in [r for r in p['roles'].values() if 'status' in r]:
                role_count += 1

        # Redirect if no changes were detected
        if (
            user_count == 0
            and project_count == 0
            and role_count == 0
            and app_settings_count == 0
        ):
            messages.warning(
                request,
                'No changes in remote site detected, nothing to synchronize.',
            )
            return redirect(redirect_url)

        context['update_data'] = update_data
        context['user_count'] = user_count
        context['project_count'] = project_count
        context['role_count'] = role_count
        context['app_settings_count'] = app_settings_count

        # Create timeline events for projects
        if timeline:
            tl_desc = 'synchronize remote site {remote_site}'
            tl_event = timeline.add_event(
                project=None,
                app_name=APP_NAME,
                user=request.user,
                event_name='remote_project_sync',
                description=tl_desc,
                classified=True,
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=source_site, label='remote_site', name=source_site.name
            )

        messages.success(
            request,
            '{} data updated according to source site.'.format(
                get_display_name(PROJECT_TYPE_PROJECT, title=True)
            ),
        )
        return super().render_to_response(context)
