"""REST API views for the projectroles app"""

import re

from ipaddress import ip_address, ip_network

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import (
    APIException,
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
from rest_framework.permissions import (
    BasePermission,
    AllowAny,
    IsAuthenticated,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.views import APIView

from projectroles import __version__ as core_version
from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    AppSetting,
    SODAR_CONSTANTS,
    CAT_DELIMITER,
    ROLE_PROJECT_TYPE_ERROR_MSG,
)
from projectroles.plugins import get_backend_api
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.serializers import (
    ProjectSerializer,
    RoleAssignmentSerializer,
    ProjectInviteSerializer,
    AppSettingSerializer,
    SODARUserSerializer,
    REMOTE_MODIFY_MSG,
)
from projectroles.views import (
    ProjectAccessMixin,
    RoleAssignmentDeleteMixin,
    RoleAssignmentOwnerTransferMixin,
    ProjectInviteMixin,
    ProjectModifyPluginViewMixin,
    SITE_MODE_TARGET,
)


app_settings = AppSettingAPI()
User = auth.get_user_model()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_ROLE_FINDER = SODAR_CONSTANTS['PROJECT_ROLE_FINDER']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]

# API constants for external SODAR Core sites
SODAR_API_MEDIA_TYPE = getattr(
    settings, 'SODAR_API_MEDIA_TYPE', 'application/UNDEFINED+json'
)
SODAR_API_DEFAULT_VERSION = getattr(
    settings, 'SODAR_API_DEFAULT_VERSION', '0.1'
)
SODAR_API_ALLOWED_VERSIONS = getattr(
    settings, 'SODAR_API_ALLOWED_VERSIONS', [SODAR_API_DEFAULT_VERSION]
)
CORE_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar-core+json'
CORE_API_DEFAULT_VERSION = re.match(
    r'^([0-9.]+)(?:[+|\-][\S]+)?$', core_version
)[1]
CORE_API_ALLOWED_VERSIONS = ['0.13.0', '0.13.1', '0.13.2', '0.13.3', '0.13.4']

# Local constants
INVALID_PROJECT_TYPE_MSG = (
    'Project type "{project_type}" not allowed for this API view'
)
USER_MODIFIABLE_MSG = 'Updating non-user modifiable settings is not allowed'
ANON_ACCESS_MSG = 'Anonymous access not allowed'
NO_VALUE_MSG = 'Value not set in request data'


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

        owner_or_delegate = project.is_owner_or_delegate(request.user)
        if not (
            request.user.is_superuser or owner_or_delegate
        ) and app_settings.get('projectroles', 'ip_restrict', project):
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
            else:  # Can't fetch client ip address
                return False

            for record in app_settings.get(
                'projectroles', 'ip_allowlist', project
            ):
                if '/' in record:
                    if client_address in ip_network(record):
                        break
                else:
                    if client_address == ip_address(record):
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


class SODARAPIVersioning(AcceptHeaderVersioning):
    """Accept header versioning class for SODAR API views"""

    allowed_versions = SODAR_API_ALLOWED_VERSIONS
    default_version = SODAR_API_DEFAULT_VERSION
    version_param = 'version'


class SODARAPIRenderer(JSONRenderer):
    """
    SODAR API JSON renderer with a site-specific media type retrieved from
    Django settings.
    """

    media_type = SODAR_API_MEDIA_TYPE


# Base API View Mixins ---------------------------------------------------------


class SODARAPIBaseMixin:
    """Base SODAR API mixin to be used by external SODAR Core based sites"""

    renderer_classes = [SODARAPIRenderer]
    versioning_class = SODARAPIVersioning


class SODARAPIBaseProjectMixin(ProjectAccessMixin, SODARAPIBaseMixin):
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


# SODAR Core Base Views and Mixins ---------------------------------------------


class CoreAPIVersioning(AcceptHeaderVersioning):
    allowed_versions = CORE_API_ALLOWED_VERSIONS
    default_version = CORE_API_DEFAULT_VERSION
    version_param = 'version'


class CoreAPIRenderer(JSONRenderer):
    media_type = CORE_API_MEDIA_TYPE


class CoreAPIBaseMixin:
    """
    SODAR Core API view mixin, which overrides versioning and renderer classes
    with ones intended for use with internal SODAR Core API views.
    """

    renderer_classes = [CoreAPIRenderer]
    versioning_class = CoreAPIVersioning


class CoreAPIBaseProjectMixin(ProjectAccessMixin, CoreAPIBaseMixin):
    """
    SODAR Core API view mixin for the base DRF ``APIView`` class with project
    permission checking, but without serializers and other generic view
    functionality.
    """

    permission_classes = [SODARAPIProjectPermission]


class CoreAPIGenericProjectMixin(
    APIProjectContextMixin, CoreAPIBaseProjectMixin
):
    """Generic API view mixin for internal SODAR Core API views"""

    lookup_field = 'sodar_uuid'  # Use project__sodar_uuid for lists
    lookup_url_kwarg = 'project'  # Replace with relevant model
    queryset_project_field = 'project'  # Replace if no direct project relation


# Projectroles Specific Base Views and Mixins ----------------------------------


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


class ProjectListAPIView(APIView):
    """
    List all projects and categories for which the requesting user has access.

    **URL:** ``/project/api/list``

    **Methods:** ``GET``

    **Returns:**

    List of project details (see ``ProjectRetrieveAPIView``). For project finder
    role, only lists title and UUID of projects.
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [CoreAPIRenderer]
    versioning_class = CoreAPIVersioning

    def get(self, request, *args, **kwargs):
        projects_all = Project.objects.all().order_by('full_title')
        if request.user.is_superuser:
            ret = projects_all
        else:
            ret = []
            role_cats = []
            projects_local = [
                a.project
                for a in RoleAssignment.objects.filter(user=request.user)
            ]
            for p in projects_all:
                local_role = p in projects_local
                if (
                    local_role
                    or p.public_guest_access
                    or any(p.full_title.startswith(c) for c in role_cats)
                ):
                    ret.append(p)
                if local_role and p.type == PROJECT_TYPE_CATEGORY:
                    role_cats.append(p.full_title + CAT_DELIMITER)
        serializer = ProjectSerializer(
            ret, many=True, context={'request': request}
        )
        return Response(serializer.data, status=200)


class ProjectRetrieveAPIView(
    ProjectQuerysetMixin, CoreAPIGenericProjectMixin, RetrieveAPIView
):
    """
    Retrieve a project or category by its UUID.

    **URL:** ``/project/api/retrieve/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``description``: Project description (string)
    - ``parent``: Parent category UUID (string or null)
    - ``readme``: Project readme (string, supports markdown)
    - ``public_guest_access``: Guest access for all users (boolean)
    - ``roles``: Project role assignments (dict, assignment UUID as key)
    - ``sodar_uuid``: Project UUID (string)
    - ``title``: Project title (string)
    - ``type``: Project type (string, options: ``PROJECT`` or ``CATEGORY``)
    """

    permission_required = 'projectroles.view_project'
    serializer_class = ProjectSerializer


class ProjectCreateAPIView(ProjectAccessMixin, CreateAPIView):
    """
    Create a project or a category.

    **URL:** ``/project/api/create``

    **Methods:** ``POST``

    **Parameters:**

    - ``title``: Project title (string)
    - ``type``: Project type (string, options: ``PROJECT`` or ``CATEGORY``)
    - ``parent``: Parent category UUID (string)
    - ``description``: Project description (string, optional)
    - ``readme``: Project readme (string, optional, supports markdown)
    - ``public_guest_access``: Guest access for all users (boolean)
    - ``owner``: User UUID of the project owner (string)
    """

    permission_classes = [ProjectCreatePermission]
    renderer_classes = [CoreAPIRenderer]
    serializer_class = ProjectSerializer
    versioning_class = CoreAPIVersioning


class ProjectUpdateAPIView(
    ProjectQuerysetMixin, CoreAPIGenericProjectMixin, UpdateAPIView
):
    """
    Update the metadata of a project or a category.

    Note that the project owner can not be updated here. Instead, use the
    dedicated API view ``RoleAssignmentOwnerTransferAPIView``.

    The project type can not be updated once a project has been created. The
    parameter is still required for non-partial updates via the ``PUT`` method.

    **URL:** ``/project/api/update/{Project.sodar_uuid}``

    **Methods:** ``PUT``, ``PATCH``

    **Parameters:**

    - ``title``: Project title (string)
    - ``type``: Project type (string, can not be modified)
    - ``parent``: Parent category UUID (string)
    - ``description``: Project description (string, optional)
    - ``readme``: Project readme (string, optional, supports markdown)
    - ``public_guest_access``: Guest access for all users (boolean)
    """

    permission_required = 'projectroles.update_project'
    serializer_class = ProjectSerializer

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        project = self.get_project(request=context['request'])
        context['parent'] = (
            str(project.parent.sodar_uuid) if project.parent else None
        )
        return context


class RoleAssignmentCreateAPIView(CoreAPIGenericProjectMixin, CreateAPIView):
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


class RoleAssignmentUpdateAPIView(CoreAPIGenericProjectMixin, UpdateAPIView):
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
    RoleAssignmentDeleteMixin, CoreAPIGenericProjectMixin, DestroyAPIView
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
        self.delete_assignment(request=self.request, instance=instance)


class RoleAssignmentOwnerTransferAPIView(
    RoleAssignmentOwnerTransferMixin, CoreAPIBaseProjectMixin, APIView
):
    """
    Trensfer project ownership to another user with a role in the project.
    Reassign a different role to the previous owner.

    The new owner must already have a role assigned in the project.

    **URL:** ``/project/api/roles/owner-transfer/{Project.sodar_uuid}``

    **Methods:** ``POST``

    **Parameters:**

    - ``new_owner``: User name of new owner (string)
    - ``old_owner_role``: Role for old owner (string. e.g. "project delegate")
    """

    permission_required = 'projectroles.update_project_owner'

    def post(self, request, *args, **kwargs):
        """Handle ownership transfer in a POST request"""
        project = self.get_project()
        # Validation for remote sites and projects
        if project.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)

        new_owner = User.objects.filter(
            username=request.data.get('new_owner')
        ).first()
        old_owner_role = Role.objects.filter(
            name=request.data.get('old_owner_role')
        ).first()
        old_owner_as = project.get_owner()
        old_owner = old_owner_as.user

        # Validate input
        if not new_owner or not old_owner_role:
            raise serializers.ValidationError(
                'Fields "new_owner" and "old_owner_role" must be present'
            )
        if not old_owner_role:
            raise serializers.ValidationError(
                'Unknown role "{}"'.format(request.data.get('old_owner_role'))
            )
        if project.type not in old_owner_role.project_types:
            raise serializers.ValidationError(
                ROLE_PROJECT_TYPE_ERROR_MSG.format(
                    project_type=project.type, role_name=old_owner_role.name
                )
            )
        if not old_owner_as:
            raise serializers.ValidationError('Existing owner role not found')
        if not new_owner:
            raise serializers.ValidationError(
                'User "{}" not found'.format(request.data.get('new_owner'))
            )
        if new_owner == old_owner:
            raise serializers.ValidationError('Owner role already set for user')
        if not project.has_role(new_owner):
            raise serializers.ValidationError(
                'User {} is not a member of the project'.format(
                    new_owner.username
                )
            )
        # Validate existing inherited role for old owner, do not allow demoting
        inh_roles = RoleAssignment.objects.filter(
            user=old_owner, project__in=project.get_parents()
        ).order_by('role__rank')
        if inh_roles and old_owner_role.rank > inh_roles.first().role.rank:
            raise serializers.ValidationError(
                'User {} has inherited role "{}", demoting is not '
                'allowed'.format(
                    old_owner.username, inh_roles.first().role.name
                )
            )

        # All OK, transfer owner
        try:
            self.transfer_owner(
                project, new_owner, old_owner_as, old_owner_role
            )
        except Exception as ex:
            raise APIException('Unable to transfer owner: {}'.format(ex))
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

    def validate(self, invite, request, **kwargs):
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


class ProjectInviteListAPIView(CoreAPIBaseProjectMixin, ListAPIView):
    """
    List user invites for a project.

    **URL:** ``/project/api/invites/list/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:** List of project invite details
    """

    # lookup_field = 'project__sodar_uuid'
    # lookup_url_kwarg = 'projectinvite'
    permission_required = 'projectroles.invite_users'
    serializer_class = ProjectInviteSerializer

    def get_queryset(self):
        return ProjectInvite.objects.filter(
            project=self.get_project(), active=True
        ).order_by('pk')


class ProjectInviteCreateAPIView(CoreAPIGenericProjectMixin, CreateAPIView):
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


class ProjectInviteRevokeAPIView(
    ProjectInviteMixin, ProjectInviteAPIMixin, CoreAPIBaseProjectMixin, APIView
):
    """
    Revoke a project invite.

    **URL:** ``/project/api/invites/revoke/{ProjectInvite.sodar_uuid}``

    **Methods:** ``POST``
    """

    permission_required = 'projectroles.invite_users'

    def post(self, request, *args, **kwargs):
        """Handle invite revoking in a POST request"""
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()
        self.validate(invite, request, **kwargs)
        invite = self.revoke_invite(invite, invite.project, request)
        return Response(
            {
                'detail': 'Invite revoked from email {} in project "{}"'.format(
                    invite.email,
                    invite.project.title,
                )
            },
            status=200,
        )


class ProjectInviteResendAPIView(
    ProjectInviteMixin, ProjectInviteAPIMixin, CoreAPIBaseProjectMixin, APIView
):
    """
    Resend email for a project invite.

    **URL:** ``/project/api/invites/resend/{ProjectInvite.sodar_uuid}``

    **Methods:** ``POST``
    """

    permission_required = 'projectroles.invite_users'

    def post(self, request, *args, **kwargs):
        """Handle invite resending in a POST request"""
        invite = ProjectInvite.objects.filter(
            sodar_uuid=kwargs['projectinvite']
        ).first()
        self.validate(invite, request, **kwargs)
        self.handle_invite(invite, request, resend=True, add_message=False)
        return Response(
            {
                'detail': 'Invite resent from email {} in project "{}"'.format(
                    invite.email,
                    invite.project.title,
                )
            },
            status=200,
        )


class AppSettingMixin:
    """Helpers for app setting API views"""

    @classmethod
    def get_and_validate_def(cls, app_name, setting_name, allowed_scopes):
        """
        Return settings definition or raise a validation error.

        :param app_name: Name of app plugin for the setting (string)
        :param setting_name: Setting name (string)
        :param allowed_scopes: Allowed scopes for the setting (list)
        """
        try:
            s_def = app_settings.get_definition(
                name=setting_name, app_name=app_name
            )
        except Exception as ex:
            raise serializers.ValidationError(ex)
        if s_def['scope'] not in allowed_scopes:
            raise serializers.ValidationError('Invalid setting scope')
        return s_def

    @classmethod
    def get_request_value(cls, request):
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
        cls, setting_def, project, request_user, setting_user
    ):
        """
        Check permissions for project settings.

        :param setting_def: Dict
        :param project: Project object
        :param request_user: User object for requesting user
        :param setting_user: User object for the setting user or None
        """
        if setting_def['scope'] == APP_SETTING_SCOPE_PROJECT:
            if not request_user.has_perm(
                'projectroles.update_project_settings', project
            ):
                raise PermissionDenied(
                    'User lacks permission to access PROJECT scope app '
                    'settings in this project'
                )
        elif setting_def['scope'] == APP_SETTING_SCOPE_PROJECT_USER:
            if not setting_user:
                raise serializers.ValidationError(
                    'No user given for PROJECT_USER setting'
                )
            if request_user != setting_user and not request_user.is_superuser:
                raise PermissionDenied(
                    'User is not allowed to update settings for other users'
                )

    @classmethod
    def _get_setting_obj(cls, app_name, setting_name, project=None, user=None):
        """
        Return the database object for a setting. Returns None if not available.

        :param app_name: Name of the app plugin (string or None)
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
        if app_name == 'projectroles':
            q_kwargs['app_plugin'] = None
        else:
            q_kwargs['app_plugin__name'] = app_name
        return AppSetting.objects.get(**q_kwargs)

    @classmethod
    def get_setting_for_api(
        cls, app_name, setting_name, project=None, user=None
    ):
        """
        Return the database object for a setting for API serving. Will create
        the object if not yet created.

        :param app_name: Name of the app plugin (string or None)
        :param setting_name: Setting name (string)
        :param project: Project object or None
        :param user: User object or None
        :return: AppSetting object
        """
        try:
            return cls._get_setting_obj(app_name, setting_name, project, user)
        except AppSetting.DoesNotExist:
            try:
                app_settings.set(
                    app_name=app_name,
                    setting_name=setting_name,
                    value=app_settings.get_default(
                        app_name, setting_name, project=project, user=user
                    ),
                    project=project,
                    user=user,
                )
                return cls._get_setting_obj(
                    app_name, setting_name, project, user
                )
            except Exception as ex:
                raise serializers.ValidationError(ex)


class ProjectSettingRetrieveAPIView(
    CoreAPIBaseProjectMixin, AppSettingMixin, RetrieveAPIView
):
    """
    API view for retrieving an app setting with the PROJECT or PROJECT_USER
    scope.

    **URL:** ``project/api/settings/retrieve/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Parameters:**

    - ``app_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)
    - ``user``: User UUID for a PROJECT_USER setting (string or None, optional)
    """

    # NOTE: Update project settings perm is checked manually
    permission_required = 'projectroles.view_project'
    serializer_class = AppSettingSerializer

    def get_object(self):
        app_name = self.request.GET.get('app_name')
        setting_name = self.request.GET.get('setting_name')

        # Get and validate definition
        s_def = self.get_and_validate_def(
            app_name,
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
        self.check_project_perms(
            s_def, project, self.request.user, setting_user
        )

        # Return new object with default setting if not set
        return self.get_setting_for_api(
            app_name, setting_name, project, setting_user
        )


class ProjectSettingSetAPIView(
    CoreAPIBaseProjectMixin,
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

    - ``app_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)
    - ``value``: Setting value (string, may contain JSON for JSON settings)
    - ``user``: User UUID for a PROJECT_USER setting (string or None, optional)
    """

    http_method_names = ['post']
    # NOTE: Update project settings perm is checked manually
    permission_required = 'projectroles.view_project'

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        timeline = get_backend_api('timeline_backend')
        app_name = request.data.get('app_name')
        setting_name = request.data.get('setting_name')

        # Get and validate definition
        s_def = self.get_and_validate_def(
            app_name,
            setting_name,
            [APP_SETTING_SCOPE_PROJECT, APP_SETTING_SCOPE_PROJECT_USER],
        )
        if s_def.get('user_modifiable') is False:
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
        self.check_project_perms(s_def, project, request.user, setting_user)

        # Set setting value with validation, return possible errors
        try:
            old_value = app_settings.get(
                app_name, setting_name, project=project, user=setting_user
            )
            app_settings.set(
                app_name=app_name,
                setting_name=setting_name,
                value=value,
                project=project,
                user=setting_user,
            )
            # Call for additional actions for project creation/update in plugins
            if s_def['scope'] == APP_SETTING_SCOPE_PROJECT and (
                settings,
                'PROJECTROLES_ENABLE_MODIFY_API',
                False,
            ):
                args = [
                    app_name,
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
            tl_desc = 'set value of {}.settings.{}'.format(
                app_name, setting_name
            )
            if setting_user:
                tl_desc += ' for user {{{}}}'.format('user')
            setting_obj = self._get_setting_obj(
                app_name, setting_name, project, setting_user
            )
            tl_extra_data = {'value': setting_obj.get_value()}
            tl_event = timeline.add_event(
                project=project,
                app_name='projectroles',
                user=request.user,
                event_name='app_setting_set_api',
                description=tl_desc,
                classified=True,
                extra_data=tl_extra_data,
                status_type='OK',
            )
            if setting_user:
                tl_event.add_object(setting_user, 'user', setting_user.username)
        return Response(
            {
                'detail': 'Set value of {}.settings.{} '
                '(project={}; user={})'.format(
                    app_name,
                    setting_name,
                    project.sodar_uuid,
                    setting_user.sodar_uuid if setting_user else None,
                )
            },
            status=200,
        )


class UserSettingRetrieveAPIView(
    CoreAPIBaseMixin, AppSettingMixin, RetrieveAPIView
):
    """
    API view for retrieving an app setting with the USER scope.

    **URL:** ``project/api/settings/retrieve/user``

    **Methods:** ``GET``

    **Parameters:**

    - ``app_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)
    """

    # NOTE: Update project settings perm is checked manually
    permission_required = 'projectroles.view_project'
    serializer_class = AppSettingSerializer

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied(ANON_ACCESS_MSG)
        app_name = self.request.GET.get('app_name')
        setting_name = self.request.GET.get('setting_name')
        # Get and validate definition
        self.get_and_validate_def(
            app_name, setting_name, [APP_SETTING_SCOPE_USER]
        )
        # Return new object with default setting if not set
        return self.get_setting_for_api(
            app_name, setting_name, user=self.request.user
        )


class UserSettingSetAPIView(CoreAPIBaseMixin, AppSettingMixin, APIView):
    """
    API view for setting the value of an app setting with the USER scope. Only
    allows the user to set the value of their own settings.

    **URL:** ``project/api/settings/set/user``

    **Methods:** ``POST``

    **Parameters:**

    - ``app_name``: Name of app plugin for the setting, use "projectroles" for projectroles settings (string)
    - ``setting_name``: Setting name (string)
    - ``value``: Setting value (string, may contain JSON for JSON settings)
    """

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied(ANON_ACCESS_MSG)
        app_name = request.data.get('app_name')
        setting_name = request.data.get('setting_name')
        s_def = self.get_and_validate_def(
            app_name, setting_name, [APP_SETTING_SCOPE_USER]
        )
        if s_def.get('user_modifiable') is False:
            raise PermissionDenied(USER_MODIFIABLE_MSG)
        value = self.get_request_value(request)

        try:
            app_settings.set(
                app_name=app_name,
                setting_name=setting_name,
                value=value,
                user=request.user,
            )
        except Exception as ex:
            raise serializers.ValidationError(ex)
        return Response(
            {
                'detail': 'Set value of {}.settings.{}'.format(
                    app_name, setting_name
                )
            },
            status=200,
        )


class UserListAPIView(CoreAPIBaseMixin, ListAPIView):
    """
    Return a list of all users on the site. Excludes system users, unless called
    with superuser access.

    **URL:** ``/project/api/users/list``

    **Methods:** ``GET``

    **Returns**: List of serializers users (see ``CurrentUserRetrieveAPIView``)
    """

    lookup_field = 'project__sodar_uuid'
    permission_classes = [IsAuthenticated]
    serializer_class = SODARUserSerializer

    def get_queryset(self):
        """
        Override get_queryset() to return users according to requesting user
        access.
        """
        qs = User.objects.all().order_by('pk')
        if self.request.user.is_superuser:
            return qs
        return qs.exclude(groups__name=SODAR_CONSTANTS['SYSTEM_USER_GROUP'])


class CurrentUserRetrieveAPIView(CoreAPIBaseMixin, RetrieveAPIView):
    """
    Return information on the user making the request.

    **URL:** ``/project/api/users/current``

    **Methods:** ``GET``

    **Returns**:

    For current user:

    - ``email``: Email address of the user (string)
    - ``is_superuser``: Superuser status (boolean)
    - ``name``: Full name of the user (string)
    - ``sodar_uuid``: User UUID (string)
    - ``username``: Username of the user (string)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SODARUserSerializer

    def get_object(self):
        return self.request.user


# TODO: Update this for new API base classes
class RemoteProjectGetAPIView(CoreAPIBaseMixin, APIView):
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
            req_version = CORE_API_DEFAULT_VERSION
        sync_data = remote_api.get_source_data(target_site, req_version)
        # Update access date for target site remote projects
        target_site.projects.all().update(date_access=timezone.now())
        return Response(sync_data, status=200)
