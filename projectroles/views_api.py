"""REST API views for the projectroles app"""

import sys

from ipaddress import ip_address, ip_network
from packaging.version import parse as parse_version
from typing import Optional

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import (
    APIException,
    NotAcceptable,
    NotFound,
    PermissionDenied,
)
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    BasePermission,
    AllowAny,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, inline_serializer

from projectroles.app_settings import AppSettingAPI
from projectroles.forms import INVITE_EXISTS_MSG
from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    AppSetting,
    SODARUser,
    SODAR_CONSTANTS,
    CAT_DELIMITER,
    ROLE_RANKING,
    ROLE_PROJECT_TYPE_ERROR_MSG,
)
from projectroles.plugins import PluginAppSettingDef, PluginAPI
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.serializers import (
    ProjectSerializer,
    RoleAssignmentSerializer,
    ProjectInviteSerializer,
    AppSettingSerializer,
    SODARUserSerializer,
    REMOTE_MODIFY_MSG,
)
from projectroles.utils import get_display_name
from projectroles.views import (
    ProjectAccessMixin,
    ProjectDeleteMixin,
    ProjectDeleteAccessMixin,
    RoleAssignmentDeleteMixin,
    RoleAssignmentOwnerTransferMixin,
    ProjectInviteMixin,
    ProjectModifyPluginViewMixin,
    PROJECT_BLOCK_MSG,
)


app_settings = AppSettingAPI()
plugin_api = PluginAPI()
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
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]

# API constants for projectroles APIs
PROJECTROLES_API_MEDIA_TYPE = (
    'application/vnd.bihealth.sodar-core.projectroles+json'
)
PROJECTROLES_API_DEFAULT_VERSION = '2.0'
PROJECTROLES_API_ALLOWED_VERSIONS = ['1.0', '1.1', '2.0']
SYNC_API_MEDIA_TYPE = (
    'application/vnd.bihealth.sodar-core.projectroles.sync+json'
)
SYNC_API_DEFAULT_VERSION = '2.0'
SYNC_API_ALLOWED_VERSIONS = ['1.0', '2.0']

# Local constants
APP_NAME = 'projectroles'
INVALID_PROJECT_TYPE_MSG = (
    'Project type "{project_type}" not allowed for this API view'
)
USER_MODIFIABLE_MSG = 'Updating non-user modifiable settings is not allowed'
ANON_ACCESS_MSG = 'Anonymous access not allowed'
NO_VALUE_MSG = 'Value not set in request data'
VIEW_NOT_ACCEPTABLE_VERSION_MSG = (
    'This view is not available in the given API version'
)
USER_LIST_RESTRICT_MSG = (
    'User details access restricted: user does not have contributor access or '
    'above in any category or project '
    '(PROJECTROLES_API_USER_DETAIL_RESTRICT=True)'
)
USER_LIST_INCLUDE_VERSION_MSG = (
    'The include_system_users parameter is not available in API version <1.1'
)
CAT_PUBLIC_STATS_API_MSG = (
    'Setting category_public_stats is only allowed for top level categories'
)
VERSION_1_1 = parse_version('1.1')
VERSION_2_0 = parse_version('2.0')


# Permission / Versioning / Renderer Classes -----------------------------------


class SODARAPIProjectPermission(ProjectAccessMixin, BasePermission):
    """
    Mixin for providing basic project permission checking for API views with a
    single permission_required attribute. Also works with Knox token based
    views.

    This must be used in the ``permission_classes`` attribute in order for token
    authentication to work.

    Requires implementing either ``permission_required`` or
    ``get_permission_required()`` in the view.

    Project type can be restricted to ``PROJECT_TYPE_CATEGORY`` or
    ``PROJECT_TYPE_PROJECT``, as defined in SODAR constants, by setting the
    ``project_type`` attribute in the view.
    """

    def has_permission(self, request, view):
        """
        Override has_permission() for checking auth and project permission
        """
        if (not request.user or request.user.is_anonymous) and not getattr(
            settings, 'PROJECTROLES_ALLOW_ANONYMOUS', False
        ):
            return False
        project = self.get_project(request=request, kwargs=view.kwargs)
        if not project:
            raise NotFound()

        # Restrict project type
        project_type = getattr(view, 'project_type', None)
        p_types = [PROJECT_TYPE_CATEGORY, PROJECT_TYPE_PROJECT]
        if project_type and project_type not in p_types:
            raise ImproperlyConfigured(
                'Invalid value "{}" for project_type, accepted values: '
                '{}'.format(project_type, ', '.join(p_types))
            )
        elif project_type and project_type != project.type:
            raise PermissionDenied(
                INVALID_PROJECT_TYPE_MSG.format(project_type=project.type)
            )

        # Prohibit access if project_access_block is set
        if (
            not request.user.is_superuser
            and project.is_project()
            and app_settings.get(
                APP_NAME, 'project_access_block', project=project
            )
        ):
            raise PermissionDenied(
                PROJECT_BLOCK_MSG.format(
                    project_type=get_display_name(project.type)
                )
            )

        owner_or_delegate = project.is_owner_or_delegate(request.user)
        if not (
            request.user.is_superuser or owner_or_delegate
        ) and app_settings.get(APP_NAME, 'ip_restrict', project):
            for k in (
                'HTTP_X_FORWARDED_FOR',
                'X_FORWARDED_FOR',
                'FORWARDED',
                'REMOTE_ADDR',
            ):
                v = request.META.get(k)
                if v:
                    client_address = ip_address(v.split(',')[0])
                    break
            else:  # Can't fetch client IP address
                return False

            ips = app_settings.get(APP_NAME, 'ip_allow_list', project)
            if not ips:
                return False
            for ip in [s.strip() for s in ips.split(',')]:
                if '/' in ip:
                    if client_address in ip_network(ip):
                        break
                elif client_address == ip_address(ip):
                    break
            else:
                return False

        if not hasattr(view, 'permission_required') and (
            not hasattr(view, 'get_permission_required')
            or not callable(getattr(view, 'get_permission_required', None))
        ):
            raise ImproperlyConfigured(
                '{0} is missing the permission_required attribute. '
                'Define {0}.permission_required, or override '
                '{0}.get_permission_required().'.format(view.__class__.__name__)
            )
        elif hasattr(view, 'permission_required'):
            perm = view.permission_required
        else:
            perm = view.get_permission_required()

        # This may return an iterable, but we are only interested in one perm
        if isinstance(perm, (list, tuple)) and len(perm) > 0:
            # TODO: TBD: Raise exception / log warning if given multiple perms?
            perm = perm[0]
        return request.user.has_perm(perm, project)


# Base API View Mixins ---------------------------------------------------------


class SODARAPIBaseProjectMixin(ProjectAccessMixin):
    """
    API view mixin for the base DRF ``APIView`` class with project permission
    checking, but without serializers and other generic view functionality.

    Project type can be restricted to ``PROJECT_TYPE_CATEGORY`` or
    ``PROJECT_TYPE_PROJECT``, as defined in SODAR constants, by setting the
    ``project_type`` attribute in the view.
    """

    permission_classes = [SODARAPIProjectPermission]
    project_type = None


class APIProjectContextMixin(ProjectAccessMixin):
    """
    Mixin to provide project context and queryset for generic API views. Can
    be used both in SODAR and SODAR Core API base views.

    If your model doesn't have a direct "project" relation, set
    ``queryset_project_field`` in the implementing class to query based on e.g.
    a nested foreignkey relation.
    """

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        if sys.argv[1:2] == ['generateschema']:
            return context
        context['project'] = self.get_project(request=context['request'])
        return context

    def get_queryset(self):
        project_field = getattr(self, 'queryset_project_field', 'project')
        return self.__class__.serializer_class.Meta.model.objects.filter(
            **{project_field: self.get_project()}
        )


class SODARAPIGenericProjectMixin(
    APIProjectContextMixin, SODARAPIBaseProjectMixin
):
    """
    API view mixin for generic DRF API views with serializers, SODAR project
    context and permission checkin.

    Unless overriding ``permission_classes`` with their own implementation, the
    user MUST supply a ``permission_required`` attribute.

    Replace ``lookup_url_kwarg`` with your view's url kwarg (SODAR project
    compatible model name in lowercase).

    If the lookup is done via a foreign key, change the ``lookup_field``
    attribute of your class into ``foreignkey__sodar_uuid``, e.g.
    ``project__sodar_uuid`` for lists.

    If your object(s) don't have a direct ``project`` relation, update the
    ``queryset_project_field`` to point to the field, e.g.
    ``someothermodel__project``.
    """

    lookup_field = 'sodar_uuid'  # Use project__sodar_uuid for lists
    lookup_url_kwarg = 'project'  # Replace with relevant model
    queryset_project_field = 'project'  # Replace if no direct project relation


class ProjectQuerysetMixin:
    """
    Mixin for overriding the default queryset with one which allows us to lookup
    a Project object directly.
    """

    def get_queryset(self):
        return Project.objects.all()


class SODARPageNumberPagination(PageNumberPagination):
    """
    Override of PageNumberPagination to provide optional pagination.

    If the "page" query string is not present, results will be provided as a
    full unpaginated list.

    If the "page" query string is included, results will be presented in the
    default ``PageNumberPagination`` dict format.

    See: https://www.django-rest-framework.org/api-guide/pagination/#pagenumberpagination
    """

    def paginate_queryset(self, queryset, request, view=None):
        if not request.query_params.get('page'):
            return None
        return super().paginate_queryset(queryset, request, view)


# SODAR Core Base Views and Mixins ---------------------------------------------


class ProjectrolesAPIVersioningMixin:
    """
    Projectroles API view versioning mixin for overriding media type
    and accepted versions.
    """

    class ProjectrolesAPIVersioning(AcceptHeaderVersioning):
        allowed_versions = PROJECTROLES_API_ALLOWED_VERSIONS
        default_version = PROJECTROLES_API_DEFAULT_VERSION

    class ProjectrolesAPIRenderer(JSONRenderer):
        media_type = PROJECTROLES_API_MEDIA_TYPE

    renderer_classes = [ProjectrolesAPIRenderer]
    versioning_class = ProjectrolesAPIVersioning


class RemoteSyncAPIVersioningMixin:
    """
    Projectroles remote sync API view versioning mixin for overriding media type
    and accepted versions.
    """

    class RemoteSyncAPIRenderer(JSONRenderer):
        media_type = SYNC_API_MEDIA_TYPE

    class RemoteSyncAPIVersioning(AcceptHeaderVersioning):
        allowed_versions = SYNC_API_ALLOWED_VERSIONS
        default_version = SYNC_API_DEFAULT_VERSION

    renderer_classes = [RemoteSyncAPIRenderer]
    versioning_class = RemoteSyncAPIVersioning


class ProjectCreatePermission(ProjectAccessMixin, BasePermission):
    """Permission class specific to Project creation"""

    def has_permission(self, request, view):
        """Override has_permission() to check for project creation permission"""
        parent_uuid = request.data.get('parent')
        parent = (
            Project.objects.filter(sodar_uuid=parent_uuid).first()
            if parent_uuid
            else None
        )
        if (
            parent
            and settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            and (not settings.PROJECTROLES_TARGET_CREATE or parent.is_remote())
        ):
            return False
        if not parent and not request.user.is_superuser:
            return False
        return request.user.has_perm('projectroles.create_project', parent)


# API Views --------------------------------------------------------------------


class ProjectListAPIView(ProjectrolesAPIVersioningMixin, ListAPIView):
    """
    List all projects and categories for which the requesting user has access.

    Supports optional pagination by providing the ``page`` query string. This
    will return results in the Django Rest Framework ``PageNumberPagination``
    format.

    **URL:** ``/project/api/list``

    **Methods:** ``GET``

    **Parameters:**

    - ``page``: Page number for paginated results (int, optional)

    **Returns:**

    List of ``Project`` objects (see ``ProjectRetrieveAPIView``). For project
    finder role, only lists title and UUID of projects.
    """

    pagination_class = SODARPageNumberPagination
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        """
        Override get_queryset() to return categories and projects to which the
        user has access. NOTE: Returns a list, not a QuerySet.

        :return: List of Project objects
        """
        projects_all = Project.objects.all().order_by('full_title')
        if self.request.user.is_superuser:
            qs = projects_all
        else:
            qs = []
            role_cats = []
            projects_local = [
                a.project
                for a in RoleAssignment.objects.filter(user=self.request.user)
            ]
            for p in projects_all:
                local_role = p in projects_local
                if (
                    local_role
                    or p.public_access
                    or any(p.full_title.startswith(c) for c in role_cats)
                ):
                    qs.append(p)
                if local_role and p.is_category():
                    role_cats.append(p.full_title + CAT_DELIMITER)
        return qs


class ProjectRetrieveAPIView(
    ProjectQuerysetMixin,
    ProjectrolesAPIVersioningMixin,
    SODARAPIGenericProjectMixin,
    RetrieveAPIView,
):
    """
    Retrieve a project or category by its UUID.

    **URL:** ``/project/api/retrieve/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``archive``: Project archival status (boolean)
    - ``children``: Category children (list of UUIDs, only returned for categories)
    - ``description``: Project description (string)
    - ``full_title``: Full project title with parent categories (string)
    - ``parent``: Parent category UUID (string or null)
    - ``readme``: Project readme (string, supports markdown)
    - ``public_access``: Read-only access for all users (role name as string or None)
    - ``roles``: Project role assignments (dict, assignment UUID as key)
    - ``sodar_uuid``: Project UUID (string)
    - ``title``: Project title (string)
    - ``type``: Project type (string, options: ``PROJECT`` or ``CATEGORY``)

    **Version Changes:**

    - ``2.0``
        * Replace ``roles`` field user serializer with user UUID
        * Replace ``public_guest_access`` field with ``public_access``
    - ``1.1``
        * Add ``children`` field
    """

    permission_required = 'projectroles.view_project'
    serializer_class = ProjectSerializer


class ProjectCreateAPIView(
    ProjectrolesAPIVersioningMixin, ProjectAccessMixin, CreateAPIView
):
    """
    Create a project or a category.

    If setting public read-only access for users, provide role name ("project
    guest" or "project viewer") or None for no access.

    **URL:** ``/project/api/create``

    **Methods:** ``POST``

    **Parameters:**

    - ``title``: Project title (string)
    - ``type``: Project type (string, options: ``PROJECT`` or ``CATEGORY``)
    - ``parent``: Parent category UUID (string)
    - ``description``: Project description (string, optional)
    - ``readme``: Project readme (string, optional, supports markdown)
    - ``public_access``: Public read-only access for all users (string or None)
    - ``owner``: User UUID of the project owner (string)

    **Version Changes:**

    - ``2.0``
        * Replace ``public_guest_access`` field with ``public_access``
    """

    permission_classes = [ProjectCreatePermission]
    serializer_class = ProjectSerializer


class ProjectUpdateAPIView(
    ProjectQuerysetMixin,
    ProjectrolesAPIVersioningMixin,
    SODARAPIGenericProjectMixin,
    UpdateAPIView,
):
    """
    Update the metadata of a project or a category.

    Note that the project owner can not be updated here. Instead, use the
    dedicated API view ``RoleAssignmentOwnerTransferAPIView``.

    The project type can not be updated once a project has been created. The
    parameter is still required for non-partial updates via the ``PUT`` method.

    If setting public read-only access for users, provide role name ("project
    guest" or "project viewer") or None for no access.

    **URL:** ``/project/api/update/{Project.sodar_uuid}``

    **Methods:** ``PUT``, ``PATCH``

    **Parameters:**

    - ``title``: Project title (string)
    - ``type``: Project type (string, can not be modified)
    - ``parent``: Parent category UUID (string)
    - ``description``: Project description (string, optional)
    - ``readme``: Project readme (string, optional, supports markdown)
    - ``public_access``: Public read-only access for all users (string or None)

    - ``2.0``
        * Replace ``public_guest_access`` field with ``public_access``
    """

    permission_required = 'projectroles.update_project'
    serializer_class = ProjectSerializer

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        if sys.argv[1:2] == ['generateschema']:
            return context
        project = self.get_project(request=context['request'])
        context['parent'] = (
            str(project.parent.sodar_uuid) if project.parent else None
        )
        return context


class ProjectDestroyAPIView(
    ProjectQuerysetMixin,
    ProjectrolesAPIVersioningMixin,
    SODARAPIGenericProjectMixin,
    ProjectDeleteMixin,
    ProjectDeleteAccessMixin,
    DestroyAPIView,
):
    """
    Destroy a project and all associated data.

    Deletion is prohibited if called on a category with children or a project
    with non-revoked remote projects.

    NOTE: This operation can not be undone!

    **URL:** ``/project/api/destroy/{Project.sodar_uuid}``

    **Methods:** ``DELETE``

    **Version Changes:**

    - ``1.1``: Add view
    """

    permission_required = 'projectroles.delete_project'
    serializer_class = ProjectSerializer

    def perform_destroy(self, instance):
        """Override perform_destroy() to handle Project deletion"""
        if parse_version(self.request.version) < VERSION_1_1:
            raise NotAcceptable(VIEW_NOT_ACCEPTABLE_VERSION_MSG)
        access, msg = self.check_delete_permission(instance)
        if not access:
            raise PermissionDenied(msg)
        with transaction.atomic():
            self.handle_delete(instance, self.request)


class RoleAssignmentCreateAPIView(
    ProjectrolesAPIVersioningMixin, SODARAPIGenericProjectMixin, CreateAPIView
):
    """
    Create a role assignment in a project.

    **URL:** ``/project/api/roles/create/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``role``: Desired role for user (string, e.g. "project contributor")
    - ``user``: User UUID (string)
    """

    permission_required = 'projectroles.update_project_members'
    serializer_class = RoleAssignmentSerializer


class RoleAssignmentUpdateAPIView(
    ProjectrolesAPIVersioningMixin, SODARAPIGenericProjectMixin, UpdateAPIView
):
    """
    Update the role assignment for a user in a project.

    The user can not be changed in this API view.

    **URL:** ``/project/api/roles/update/{RoleAssignment.sodar_uuid}``

    **Methods:** ``PUT``, ``PATCH``

    **Parameters:**

    - ``role``: Desired role for user (string, e.g. "project contributor")
    - ``user``: User UUID (string)
    """

    lookup_url_kwarg = 'roleassignment'
    permission_required = 'projectroles.update_project_members'
    serializer_class = RoleAssignmentSerializer


class RoleAssignmentDestroyAPIView(
    RoleAssignmentDeleteMixin,
    ProjectrolesAPIVersioningMixin,
    SODARAPIGenericProjectMixin,
    DestroyAPIView,
):
    """
    Destroy a role assignment.

    The owner role can not be destroyed using this view.

    **URL:** ``/project/api/roles/destroy/{RoleAssignment.sodar_uuid}``

    **Methods:** ``DELETE``
    """

    lookup_url_kwarg = 'roleassignment'
    permission_required = 'projectroles.update_project_members'
    serializer_class = RoleAssignmentSerializer

    def perform_destroy(self, instance):
        """
        Override perform_destroy() to handle RoleAssignment deletion.
        """
        project = self.get_project()
        # Validation for remote sites and projects
        if project.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)
        # Do not allow editing owner here
        if instance.role.name == PROJECT_ROLE_OWNER:
            raise serializers.ValidationError(
                'Use project updating API to update owner'
            )
        # Check delegate perms
        if (
            instance.role.name == PROJECT_ROLE_DELEGATE
            and not self.request.user.has_perm(
                'projectroles.update_project_delegate', project
            )
        ):
            raise PermissionDenied('User lacks permission to assign delegates')
        self.delete_assignment(role_as=instance, request=self.request)


class RoleAssignmentOwnerTransferAPIView(
    RoleAssignmentOwnerTransferMixin,
    ProjectrolesAPIVersioningMixin,
    SODARAPIBaseProjectMixin,
    APIView,
):
    """
    Trensfer project ownership to another user with a role in the project.
    Reassign a different role to the previous owner.

    The new owner must already have a role assigned in the project.

    NOTE: Barring any inherited role, if no value is given for
    ``old_owner_role``, the old owner's access to the project will be removed.

    **URL:** ``/project/api/roles/owner-transfer/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``new_owner``: User name of new owner (string)
    - ``old_owner_role``: Role for old owner (string or None, e.g. "project delegate")

    **Version Changes:**

    - ``1.1``: Allow empty value for ``old_owner_role``
    """

    permission_required = 'projectroles.update_project_owner'
    serializer_class = RoleAssignmentSerializer

    def post(self, request, *args, **kwargs):
        """Handle ownership transfer in a POST request"""
        d_new_owner = request.data.get('new_owner')
        d_old_owner_role = request.data.get('old_owner_role')
        # Validate input
        if not d_new_owner:
            raise serializers.ValidationError(
                'Field "new_owner" must be present'
            )
        # Prevent old_owner_role=None if v1.0
        if (
            parse_version(request.version) < VERSION_1_1
            and not d_old_owner_role
        ):
            raise serializers.ValidationError(
                'Field "old_owner_role" must be present'
            )

        project = self.get_project()
        # Validation for remote sites and projects
        if project.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)

        new_owner = User.objects.filter(username=d_new_owner).first()
        old_owner_role = None
        if d_old_owner_role:
            old_owner_role = Role.objects.filter(name=d_old_owner_role).first()
        old_owner_as = project.get_owner()
        old_owner = old_owner_as.user

        if d_old_owner_role and not old_owner_role:
            raise serializers.ValidationError(
                f'Unknown role "{d_old_owner_role}"'
            )
        if old_owner_role and project.type not in old_owner_role.project_types:
            raise serializers.ValidationError(
                ROLE_PROJECT_TYPE_ERROR_MSG.format(
                    project_type=project.type, role_name=old_owner_role.name
                )
            )
        if not old_owner_as:
            raise serializers.ValidationError('Existing owner role not found')
        if not new_owner:
            raise serializers.ValidationError(f'User "{d_new_owner}" not found')
        if new_owner == old_owner:
            raise serializers.ValidationError('Owner role already set for user')
        if not project.has_role(new_owner):
            raise serializers.ValidationError(
                f'User {new_owner.username} is not a member of the project'
            )
        # Validate existing inherited role for old owner, do not allow demoting
        inh_roles = RoleAssignment.objects.filter(
            user=old_owner, project__in=project.get_parents()
        ).order_by('role__rank')
        if inh_roles and old_owner_role.rank > inh_roles.first().role.rank:
            raise serializers.ValidationError(
                f'User {old_owner.username} has inherited role '
                f'"{inh_roles.first().role.name}", demoting is not allowed'
            )

        try:  # All OK, transfer owner
            self.transfer_owner(
                project,
                new_owner,
                old_owner_as,
                old_owner_role,
                request=request,
            )
        except Exception as ex:
            raise APIException(f'Unable to transfer owner: {ex}')
        return Response(
            {
                'detail': 'Ownership transferred from {} to {} in '
                'project "{}"'.format(
                    old_owner_as.user.username,
                    new_owner.username,
                    project.title,
                )
            },
            status=200,
        )


class ProjectInviteAPIMixin:
    """Validation helpers for project invite modification via API"""

    def validate(
        self, invite: Optional[ProjectInvite], request: HttpRequest, **kwargs
    ):
        if not invite:
            raise NotFound(
                'Invite not found (uuid={})'.format(kwargs['projectinvite'])
            )
        if (
            invite.role.name == PROJECT_ROLE_DELEGATE
            and not request.user.has_perm(
                'projectroles.update_project_delegate', invite.project
            )
        ):
            raise PermissionDenied(
                'User lacks permission to modify delegate invites'
            )
        if not invite.active:
            raise serializers.ValidationError('Invite is not active')


class ProjectInviteListAPIView(
    ProjectrolesAPIVersioningMixin, SODARAPIBaseProjectMixin, ListAPIView
):
    """
    List user invites for a project.

    Supports optional pagination by providing the ``page`` query string. This
    will return results in the Django Rest Framework ``PageNumberPagination``
    format.

    **URL:** ``/project/api/invites/list/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Parameters:**

    - ``page``: Page number for paginated results (int, optional)

    **Returns:** List or paginated dict of project invite details

    **Version Changes:**

    - ``2.0``: Replace ``issuer`` field user serializer with user UUID
    """

    pagination_class = SODARPageNumberPagination
    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer

    def get_queryset(self):
        return ProjectInvite.objects.filter(
            project=self.get_project(), active=True
        ).order_by('pk')


class ProjectInviteRetrieveAPIView(
    ProjectrolesAPIVersioningMixin, SODARAPIGenericProjectMixin, RetrieveAPIView
):
    """
    Retrieve a project invite.

    **URL:** ``/project/api/invites/retrieve/{ProjectInvite.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``date_created``: Creation datetime string (YYYY-MM-DDThh:mm:ssZ)
    - ``date_expire``: Expiry datetime string (YYYY-MM-DDThh:mm:ssZ)
    - ``message``: Optional invite message (string)
    - ``issuer``: UUID of issuing user (string)
    - ``email``: Email of invited user (string)
    - ``project``: Project UUID (string)
    - ``role``: Role for invided user (string, e.g. "project contributor")
    - ``sodar_uuid``: Invite UUID (string)

    **Version Changes:**

    - ``2.0``: Add view
    """

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'projectinvite'
    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer

    def get(self, request, *args, **kwargs):
        """Override get() to check for API version"""
        if parse_version(request.version) < VERSION_2_0:
            raise NotAcceptable(VIEW_NOT_ACCEPTABLE_VERSION_MSG)
        return super().get(request, *args, **kwargs)


class ProjectInviteCreateAPIView(
    ProjectrolesAPIVersioningMixin, SODARAPIGenericProjectMixin, CreateAPIView
):
    """
    Create a project invite.

    **URL:** ``/project/api/invites/create/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``email``: User email (string)
    - ``role``: Desired role for user (string, e.g. "project contributor")
    """

    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer

    def perform_create(self, serializer):
        project = self.get_project()
        user_email = self.request.data.get('email')
        existing_inv = ProjectInvite.objects.filter(
            project=project,
            email=user_email,
            active=True,
            date_expire__gt=timezone.now(),
        ).first()
        if existing_inv:
            raise serializers.ValidationError(
                INVITE_EXISTS_MSG.format(
                    user_email=user_email, project_title=project.get_log_title()
                )
            )
        if project.parent:
            parent_inv = ProjectInvite.objects.filter(
                email=user_email,
                active=True,
                date_expire__gt=timezone.now(),
                project__in=project.get_parents(),
            ).first()
            if parent_inv:
                raise serializers.ValidationError(
                    INVITE_EXISTS_MSG.format(
                        user_email=user_email,
                        project_title=parent_inv.project.get_log_title(),
                    )
                )
        return super().perform_create(serializer)


class ProjectInviteRevokeAPIView(
    ProjectInviteMixin,
    ProjectInviteAPIMixin,
    ProjectrolesAPIVersioningMixin,
    SODARAPIBaseProjectMixin,
    APIView,
):
    """
    Revoke a project invite.

    **URL:** ``/project/api/invites/revoke/{ProjectInvite.sodar_uuid}``

    **Methods:** ``POST``
    """

    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer

    def post(self, request, *args, **kwargs):
        """Handle invite revoking in a POST request"""
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()
        self.validate(invite, request, **kwargs)
        invite = self.revoke_invite(invite, invite.project, request)
        return Response(
            {
                'detail': f'Invite revoked from email {invite.email} in '
                f'project "{invite.project.title}"'
            },
            status=200,
        )


class ProjectInviteResendAPIView(
    ProjectInviteMixin,
    ProjectInviteAPIMixin,
    ProjectrolesAPIVersioningMixin,
    SODARAPIBaseProjectMixin,
    APIView,
):
    """
    Resend email for a project invite.

    **URL:** ``/project/api/invites/resend/{ProjectInvite.sodar_uuid}``

    **Methods:** ``POST``
    """

    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer

    def post(self, request, *args, **kwargs):
        """Handle invite resending in a POST request"""
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()
        self.validate(invite, request, **kwargs)
        self.handle_invite(invite, request, resend=True, add_message=False)
        return Response(
            {
                'detail': f'Invite resent from email {invite.email} in project '
                f'"{invite.project.title}"'
            },
            status=200,
        )


class AppSettingMixin:
    """Helpers for app setting API views"""

    @classmethod
    def get_and_validate_def(
        cls, plugin_name: str, setting_name: str, allowed_scopes: list[str]
    ) -> PluginAppSettingDef:
        """
        Return settings definition or raise a validation error.

        :param plugin_name: Name of app plugin for the setting (string)
        :param setting_name: Setting name (string)
        :param allowed_scopes: Allowed scopes for the setting (list)
        :return
        """
        try:
            s_def = app_settings.get_definition(
                name=setting_name, plugin_name=plugin_name
            )
        except Exception as ex:
            raise serializers.ValidationError(ex)
        if s_def.scope not in allowed_scopes:
            raise serializers.ValidationError('Invalid setting scope')
        return s_def

    @classmethod
    def get_request_value(cls, request: HttpRequest) -> str:
        """
        Return setting value from request.

        :param request: HTTPRequest object
        :return: String or None
        :raise: ValidationError if value is not set
        """
        if 'value' not in request.data:
            raise serializers.ValidationError(NO_VALUE_MSG)
        return request.data['value']

    @classmethod
    def check_project_perms(
        cls,
        setting_def: PluginAppSettingDef,
        project: Project,
        request: HttpRequest,
        setting_user: Optional[SODARUser],
    ):
        """
        Check permissions for project settings.

        :param setting_def: PluginAppSettingDef object
        :param project: Project object
        :param request: HttpRequest object
        :param setting_user: User object for the setting user or None
        """
        if setting_def.scope == APP_SETTING_SCOPE_PROJECT:
            if request.method == 'GET':
                perm = 'projectroles.view_project_settings'
            else:
                perm = 'projectroles.update_project_settings'
            if not request.user.has_perm(perm, project):
                raise PermissionDenied(
                    'User lacks permission to access PROJECT scope app '
                    'settings in this project'
                )
        elif setting_def.scope == APP_SETTING_SCOPE_PROJECT_USER:
            if not setting_user:
                raise serializers.ValidationError(
                    'No user given for PROJECT_USER setting'
                )
            if request.user != setting_user and not request.user.is_superuser:
                raise PermissionDenied(
                    'User is not allowed to update settings for other users'
                )
            if (
                request.method == 'POST'
                and not request.user.is_superuser
                and app_settings.get(APP_NAME, 'site_read_only')
            ):
                raise PermissionDenied(
                    'Site in read-only mode, operation not allowed'
                )

    @classmethod
    def _get_setting_obj(
        cls,
        plugin_name: Optional[str],
        setting_name: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ) -> AppSetting:
        """
        Return the database object for a setting. Returns None if not available.

        :param plugin_name: Name of the app plugin (string or None)
        :param setting_name: Setting name (string)
        :param project: Project object or None
        :param user: User object or None
        :return: AppSetting object
        :raise: AppSetting.DoesNotExist if not found
        :raise: AppSetting.MultipleObjectsReturned if the arguments are invalid
        """
        q_kwargs = {
            'name': setting_name,
            'project': project,
            'user': user,
        }
        if plugin_name == APP_NAME:
            q_kwargs['app_plugin'] = None
        else:
            q_kwargs['app_plugin__name'] = plugin_name
        return AppSetting.objects.get(**q_kwargs)

    @classmethod
    def get_setting_for_api(
        cls,
        plugin_name: Optional[str],
        setting_name: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ) -> AppSetting:
        """
        Return the database object for a setting for API serving. Will create
        the object if not yet created.

        :param plugin_name: Name of the app plugin (string or None)
        :param setting_name: Setting name (string)
        :param project: Project object or None
        :param user: User object or None
        :return: AppSetting object
        """
        try:
            return cls._get_setting_obj(
                plugin_name, setting_name, project, user
            )
        except AppSetting.DoesNotExist:
            try:
                app_settings.set(
                    plugin_name=plugin_name,
                    setting_name=setting_name,
                    value=app_settings.get_default(
                        plugin_name, setting_name, project=project, user=user
                    ),
                    project=project,
                    user=user,
                )
                return cls._get_setting_obj(
                    plugin_name, setting_name, project, user
                )
            except Exception as ex:
                raise serializers.ValidationError(ex)


class ProjectSettingRetrieveAPIView(
    ProjectrolesAPIVersioningMixin,
    SODARAPIBaseProjectMixin,
    AppSettingMixin,
    RetrieveAPIView,
):
    """
    API view for retrieving an app setting with the PROJECT or PROJECT_USER
    scope.

    **URL:** ``project/api/settings/retrieve/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Parameters:**

    - ``plugin_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)
    - ``user``: User UUID for a PROJECT_USER setting (string or None, optional)

    **Returns:**

    - ``plugin_name``: Name of app plugin for the setting (string)
    - ``project``: Project UUID or None
    - ``user``: User UUID or None
    - ``name``: Setting name (string)
    - ``type``: Setting type (string)
    - ``value``: Setting value
    - ``user_modifiable``: Modifiable by user (boolean)

    **Version Changes:**

    - ``2.0``: Replace ``user`` field user serializer with user UUID
    """

    # NOTE: Update project settings perm is checked manually
    permission_required = 'projectroles.view_project'
    serializer_class = AppSettingSerializer

    def get_object(self):
        plugin_name = self.request.GET.get('plugin_name')
        setting_name = self.request.GET.get('setting_name')

        # Get and validate definition
        s_def = self.get_and_validate_def(
            plugin_name,
            setting_name,
            [APP_SETTING_SCOPE_PROJECT, APP_SETTING_SCOPE_PROJECT_USER],
        )

        # Get project and user, check perms
        project = self.get_project()
        setting_user = None
        if self.request.GET.get('user'):
            setting_user = User.objects.filter(
                sodar_uuid=self.request.GET['user']
            ).first()
        self.check_project_perms(s_def, project, self.request, setting_user)

        # Return new object with default setting if not set
        return self.get_setting_for_api(
            plugin_name, setting_name, project, setting_user
        )


class ProjectSettingSetAPIView(
    ProjectrolesAPIVersioningMixin,
    SODARAPIBaseProjectMixin,
    AppSettingMixin,
    ProjectModifyPluginViewMixin,
    APIView,
):
    """
    API view for setting the value of an app setting with the PROJECT or
    PROJECT_USER scope.

    **URL:** ``project/api/settings/set/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``plugin_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)
    - ``value``: Setting value (string, may contain JSON for JSON settings)
    - ``user``: User UUID for a PROJECT_USER setting (string or None, optional)
    """

    http_method_names = ['post']
    # NOTE: Update project settings perm is checked manually
    permission_required = 'projectroles.view_project'
    serializer_class = AppSettingSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        timeline = plugin_api.get_backend_api('timeline_backend')
        plugin_name = request.data.get('plugin_name')
        setting_name = request.data.get('setting_name')

        # Get and validate definition
        s_def = self.get_and_validate_def(
            plugin_name,
            setting_name,
            [APP_SETTING_SCOPE_PROJECT, APP_SETTING_SCOPE_PROJECT_USER],
        )
        if (
            s_def.scope == APP_SETTING_SCOPE_PROJECT
            and not s_def.user_modifiable
        ):
            raise PermissionDenied(USER_MODIFIABLE_MSG)
        # Get value
        value = self.get_request_value(request)

        # Get project and user, check perms
        project = self.get_project()
        setting_user = None
        if request.data.get('user'):
            setting_user = User.objects.filter(
                sodar_uuid=request.data['user']
            ).first()
        self.check_project_perms(s_def, project, request, setting_user)

        # Custom projectroles validation
        if (
            plugin_name == APP_NAME
            and setting_name == 'ip_allow_list'
            and value
        ):
            ips = [s.strip() for s in value.split(',')]
            for ip in ips:
                try:
                    if '/' in ip:
                        ip_network(ip)
                    else:
                        ip_address(ip)
                except ValueError as ex:
                    raise serializers.ValidationError(ex)
        if (
            plugin_name == APP_NAME
            and setting_name == 'category_public_stats'
            and (project.parent or project.is_project())
        ):
            raise serializers.ValidationError(CAT_PUBLIC_STATS_API_MSG)

        # Set setting value with validation, return possible errors
        try:
            old_value = app_settings.get(
                plugin_name, setting_name, project=project, user=setting_user
            )
            app_settings.set(
                plugin_name=plugin_name,
                setting_name=setting_name,
                value=value,
                project=project,
                user=setting_user,
            )
            # Call for additional actions for project creation/update in plugins
            if s_def.scope == APP_SETTING_SCOPE_PROJECT and (
                settings,
                'PROJECTROLES_ENABLE_MODIFY_API',
                False,
            ):
                args = [
                    plugin_name,
                    setting_name,
                    value,
                    old_value,
                    project,
                    setting_user,
                ]
                self.call_project_modify_api(
                    'perform_project_setting_update',
                    'revert_project_setting_update',
                    args,
                )
        except Exception as ex:
            raise serializers.ValidationError(ex)

        if timeline:
            tl_desc = f'set value of {plugin_name}.settings.{setting_name}'
            if setting_user:
                tl_desc += ' for user {{{}}}'.format('user')
            setting_obj = self._get_setting_obj(
                plugin_name, setting_name, project, setting_user
            )
            tl_extra_data = {'value': setting_obj.get_value()}
            tl_event = timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=request.user,
                event_name='app_setting_set_api',
                description=tl_desc,
                classified=True,
                extra_data=tl_extra_data,
                status_type=timeline.TL_STATUS_OK,
            )
            if setting_user:
                tl_event.add_object(setting_user, 'user', setting_user.username)
        return Response(
            {
                'detail': 'Set value of {}.settings.{} '
                '(project={}; user={})'.format(
                    plugin_name,
                    setting_name,
                    project.sodar_uuid,
                    setting_user.sodar_uuid if setting_user else None,
                )
            },
            status=200,
        )


class UserSettingRetrieveAPIView(
    ProjectrolesAPIVersioningMixin, AppSettingMixin, RetrieveAPIView
):
    """
    API view for retrieving an app setting with the USER scope.

    **URL:** ``project/api/settings/retrieve/user``

    **Methods:** ``GET``

    **Parameters:**

    - ``plugin_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)

    **Returns:**

    - ``plugin_name``: Name of app plugin for the setting (string)
    - ``project``: None
    - ``user``: User UUID
    - ``name``: Setting name (string)
    - ``type``: Setting type (string)
    - ``value``: Setting value
    - ``user_modifiable``: Modifiable by user (boolean)

    **Version Changes:**

    - ``2.0``: Replace ``user`` field user serializer with user UUID
    """

    serializer_class = AppSettingSerializer

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied(ANON_ACCESS_MSG)
        plugin_name = self.request.GET.get('plugin_name')
        setting_name = self.request.GET.get('setting_name')
        # Get and validate definition
        self.get_and_validate_def(
            plugin_name, setting_name, [APP_SETTING_SCOPE_USER]
        )
        # Return new object with default setting if not set
        return self.get_setting_for_api(
            plugin_name, setting_name, user=self.request.user
        )


class UserSettingSetAPIView(
    ProjectrolesAPIVersioningMixin, AppSettingMixin, APIView
):
    """
    API view for setting the value of an app setting with the USER scope. Only
    allows the user to set the value of their own settings.

    **URL:** ``project/api/settings/set/user``

    **Methods:** ``POST``

    **Parameters:**

    - ``plugin_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)
    - ``value``: Setting value (string, may contain JSON for JSON settings)
    """

    http_method_names = ['post']
    serializer_class = AppSettingSerializer

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied(ANON_ACCESS_MSG)
        plugin_name = request.data.get('plugin_name')
        setting_name = request.data.get('setting_name')
        s_def = self.get_and_validate_def(
            plugin_name, setting_name, [APP_SETTING_SCOPE_USER]
        )
        if not s_def.user_modifiable:
            raise PermissionDenied(USER_MODIFIABLE_MSG)
        value = self.get_request_value(request)

        try:
            app_settings.set(
                plugin_name=plugin_name,
                setting_name=setting_name,
                value=value,
                user=request.user,
            )
        except Exception as ex:
            raise serializers.ValidationError(ex)
        return Response(
            {'detail': f'Set value of {plugin_name}.settings.{setting_name}'},
            status=200,
        )


class UserListAPIView(ProjectrolesAPIVersioningMixin, ListAPIView):
    """
    Return a list of all users on the site. Excludes system users, unless called
    with superuser access.

    Supports optional pagination by providing the ``page`` query string. This
    will return results in the Django Rest Framework ``PageNumberPagination``
    format.

    If ``PROJECTROLES_API_USER_DETAIL_RESTRICT`` is set True on the server, this
    view is only accessible by users who have a contributor role or above in at
    least one category or project.

    **URL:** ``/project/api/users/list``

    **Methods:** ``GET``

    **Parameters:**

    - ``include_system_users``: Include system users if True (bool, optional)
    - ``page``: Page number for paginated results (int, optional)

    **Returns:** List or paginated dict of serializers users (see ``CurrentUserRetrieveAPIView``)

    **Version Changes:**

    - ``1.1``: Add ``include_system_users`` parameter
    """

    lookup_field = 'project__sodar_uuid'
    pagination_class = SODARPageNumberPagination
    permission_classes = [IsAuthenticated]
    serializer_class = SODARUserSerializer

    def get_queryset(self):
        """
        Override get_queryset() to return users according to requesting user
        access.
        """
        inc_system = self.request.GET.get('include_system_users')
        version = parse_version(self.request.version)
        if inc_system and version < VERSION_1_1:
            raise NotAcceptable(USER_LIST_INCLUDE_VERSION_MSG)
        qs = User.objects.all().order_by('pk')
        if self.request.user.is_superuser or inc_system:
            return qs
        return qs.exclude(groups__name=SODAR_CONSTANTS['SYSTEM_USER_GROUP'])

    def get(self, request, *args, **kwargs):
        """Override get() to restrict access if set on server"""
        role_kw = {
            'user': request.user,
            'role__rank__lte': ROLE_RANKING[PROJECT_ROLE_CONTRIBUTOR],
        }
        if (
            getattr(settings, 'PROJECTROLES_API_USER_DETAIL_RESTRICT', False)
            and not request.user.is_superuser
            and RoleAssignment.objects.filter(**role_kw).count() == 0
        ):
            raise PermissionDenied(USER_LIST_RESTRICT_MSG)
        return super().get(request, *args, **kwargs)


class UserRetrieveAPIView(ProjectrolesAPIVersioningMixin, RetrieveAPIView):
    """
    Return user details for user with the given UUID.

    If ``PROJECTROLES_API_USER_DETAIL_RESTRICT`` is set True on the server, this
    view is only accessible by users who have a finder role or above in at least
    one category or project.

    **URL:** ``/project/api/users/{SODARUser.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``additional_emails``: Additional verified email addresses for user (list of strings)
    - ``auth_type``: User authentication type (string)
    - ``email``: Email address of the user (string)
    - ``is_superuser``: Superuser status (boolean)
    - ``name``: Full name of the user (string)
    - ``sodar_uuid``: User UUID (string)
    - ``username``: Username of the user (string)

    **Version Changes:**

    - ``1.1``: Add view
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SODARUserSerializer

    def get_object(self):
        try:
            return User.objects.get(sodar_uuid=self.kwargs.get('user'))
        except User.DoesNotExist:
            raise NotFound()

    def get(self, request, *args, **kwargs):
        if parse_version(request.version) < VERSION_1_1:
            raise NotAcceptable(VIEW_NOT_ACCEPTABLE_VERSION_MSG)
        if (
            getattr(settings, 'PROJECTROLES_API_USER_DETAIL_RESTRICT', False)
            and not request.user.is_superuser
            and RoleAssignment.objects.filter(user=request.user).count() == 0
        ):
            raise PermissionDenied(USER_LIST_RESTRICT_MSG)
        return super().get(request, *args, **kwargs)


class CurrentUserRetrieveAPIView(
    ProjectrolesAPIVersioningMixin, RetrieveAPIView
):
    """
    Return user details for user performing the request.

    **URL:** ``/project/api/users/current``

    **Methods:** ``GET``

    **Returns:**

    User details, see ``UserRetrieveAPIView``.

    **Version Changes:**

    - ``1.1``: Add ``auth_type`` field
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SODARUserSerializer

    def get_object(self):
        return self.request.user


# TODO: Update this for new API base classes
@extend_schema(
    responses={
        '200': inline_serializer(
            'RemoteProjectGetResponse',
            fields={
                'users': serializers.JSONField(),
                'projects': serializers.JSONField(),
                'peer_sites': serializers.JSONField(),
                'app_settings': serializers.JSONField(),
            },
        )
    }
)
class RemoteProjectGetAPIView(RemoteSyncAPIVersioningMixin, APIView):
    """API view for retrieving remote projects from a source site"""

    permission_classes = (AllowAny,)  # We check the secret in get()

    def get(self, request, *args, **kwargs):
        remote_api = RemoteProjectAPI()
        secret = kwargs['secret']
        try:
            target_site = RemoteSite.objects.get(
                mode=SITE_MODE_TARGET, secret=secret
            )
        except RemoteSite.DoesNotExist:
            return Response('Remote site not found, unauthorized', status=401)
        # Pass request version to get_source_data()
        accept_header = request.headers.get('Accept')
        if accept_header and 'version=' in accept_header:
            req_version = accept_header[accept_header.find('version=') + 8 :]
        else:
            req_version = SYNC_API_DEFAULT_VERSION
        sync_data = remote_api.get_source_data(target_site, req_version)
        # Update access date for target site remote projects
        target_site.projects.all().update(date_access=timezone.now())
        return Response(sync_data, status=200)
