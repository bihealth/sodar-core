"""REST API view model serializers for the projectroles app"""

from email.utils import parseaddr
from packaging.version import parse as parse_version

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import exceptions, serializers
from drf_keyed_list import KeyedListSerializer

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    AppSetting,
    SODARUserAdditionalEmail,
    SODAR_CONSTANTS,
    ROLE_RANKING,
    CAT_DELIMITER,
    CAT_DELIMITER_ERROR_MSG,
    ROLE_PROJECT_TYPE_ERROR_MSG,
)
from projectroles.utils import build_secret
from projectroles.views import (
    ProjectModifyMixin,
    RoleAssignmentModifyMixin,
    ProjectInviteMixin,
)


User = get_user_model()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_ROLE_FINDER = SODAR_CONSTANTS['PROJECT_ROLE_FINDER']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']

# Local constants
REMOTE_MODIFY_MSG = (
    'Modification of remote projects is not allowed, modify on the SOURCE site '
    'instead'
)
VERSION_1_1 = parse_version('1.1')
VERSION_2_0 = parse_version('2.0')


# Base Serializers -------------------------------------------------------------


class SODARModelSerializer(serializers.ModelSerializer):
    """Base serializer for any SODAR model with a sodar_uuid field"""

    sodar_uuid = serializers.CharField(read_only=True)

    class Meta:
        pass

    def to_representation(self, instance):
        """
        Override to_representation() to ensure sodar_uuid is included for object
        creation POST responses.
        """
        ret = super().to_representation(instance)
        if 'sodar_uuid' not in ret and 'sodar_uuid' in self.context:
            ret['sodar_uuid'] = str(self.context['sodar_uuid'])
        return ret

    def save(self, **kwargs):
        """
        Override save() to ensure sodar_uuid is included for object creation
        POST responses.
        """
        obj = super().save(**kwargs)
        return self.post_save(obj)

    def post_save(self, obj):
        """
        Function to call at the end of a custom save() method. Ensures the
        returning of sodar_uuid in object creation POST responses.

        :param obj: Object created in save()
        :return: obj
        """
        if hasattr(obj, 'sodar_uuid'):
            self.context['sodar_uuid'] = obj.sodar_uuid
        return obj


class SODARProjectModelSerializer(SODARModelSerializer):
    """
    Base serializer for SODAR models with a project relation.

    The project field is read only because it is retrieved through the object
    reference in the URL.
    """

    project = serializers.SlugRelatedField(
        slug_field='sodar_uuid', read_only=True
    )

    class Meta:
        pass

    def to_representation(self, instance):
        """
        Override to_representation() to ensure the project value is included
        in responses.
        """
        ret = super().to_representation(instance)
        if 'project' not in ret and 'project' in self.context:
            ret['project'] = str(self.context['project'].sodar_uuid)
        return ret

    def create(self, validated_data):
        """Override create() to add project into validated data"""
        if 'project' not in validated_data and 'project' in self.context:
            validated_data['project'] = self.context['project']
        return super().create(validated_data)


class SODARNestedListSerializer(SODARModelSerializer):
    """
    Serializer to display nested SODAR models as dicts with sodar_uuid as key.
    """

    class Meta:
        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'sodar_uuid'
        duplicate_list_key = True  # Extension to drf-keyed-list

    def to_representation(self, instance):
        """
        Override to_representation() to pop project from a nested list
        representation, where the project context is already known in the
        topmost model.
        """
        ret = super().to_representation(instance)
        if self.context.get('project'):
            ret.pop('project', None)
        return ret


class SODARUserSerializer(SODARModelSerializer):
    """Serializer for the user model used in SODAR Core based sites"""

    additional_emails = serializers.SerializerMethodField()
    auth_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'username',
            'name',
            'email',
            'additional_emails',
            'is_superuser',
            'auth_type',
            'sodar_uuid',
        ]

    def get_additional_emails(self, obj: User) -> list:
        return [
            e.email
            for e in SODARUserAdditionalEmail.objects.filter(
                user=obj, verified=True
            ).order_by('email')
        ]

    def get_auth_type(self, obj: User) -> str:
        return obj.get_auth_type()

    def to_representation(self, instance):
        """Override to_representation() to handle version differences"""
        ret = super().to_representation(instance)
        # Omit auth_type from <1.1
        if (
            'request' in self.context
            and parse_version(self.context['request'].version) < VERSION_1_1
        ):
            ret.pop('auth_type', None)
        return ret


# Projectroles Serializers -----------------------------------------------------


class RoleAssignmentValidateMixin:
    """Mixin for common role assignment validation"""

    def validate(self, attrs):
        project = self.context['project']
        current_user = self.context['request'].user
        del_limit = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)

        # Validation for remote sites and projects
        if project.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)
        if 'role' not in attrs:
            return attrs

        # Do not allow modifying/inviting owner
        if attrs['role'].name == PROJECT_ROLE_OWNER:
            raise serializers.ValidationError('Modifying owner not allowed')
        # Check delegate perms
        if attrs[
            'role'
        ].name == PROJECT_ROLE_DELEGATE and not current_user.has_perm(
            'projectroles.update_project_delegate', project
        ):
            raise exceptions.PermissionDenied(
                'User lacks permission to assign delegates'
            )
        # Check delegate limit
        if (
            attrs['role'].name == PROJECT_ROLE_DELEGATE
            and del_limit != 0
            and len(project.get_delegates(inherited=False)) >= del_limit
        ):
            raise serializers.ValidationError(
                f'Project delegate limit of {del_limit} has been reached'
            )
        return attrs


class RoleAssignmentSerializer(
    RoleAssignmentModifyMixin,
    RoleAssignmentValidateMixin,
    SODARProjectModelSerializer,
):
    """Serializer for the RoleAssignment model"""

    role = serializers.SlugRelatedField(
        slug_field='name', queryset=Role.objects.all()
    )
    user = serializers.SlugRelatedField(
        slug_field='sodar_uuid', queryset=User.objects.all()
    )

    class Meta:
        model = RoleAssignment
        fields = ['project', 'role', 'user', 'sodar_uuid']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        project = self.context['project']
        # Add user to instance for PATCH requests
        if self.instance and not attrs.get('user'):
            attrs['user'] = self.instance.user

        # Do not allow updating user
        if (
            self.instance
            and 'user' in attrs
            and attrs['user'] != self.instance.user
        ):
            raise serializers.ValidationError(
                'Updating the user is not allowed, create a new role '
                'assignment instead'
            )

        # Validate project type
        if project.type not in attrs['role'].project_types:
            raise serializers.ValidationError(
                ROLE_PROJECT_TYPE_ERROR_MSG.format(
                    project_type=project.type, role_name=attrs['role'].name
                )
            )
        # Check for existing role if creating
        if not self.instance:
            old_as = RoleAssignment.objects.filter(
                project=project, user=attrs['user']
            ).first()
            if old_as:
                raise serializers.ValidationError(
                    f'User already has the role of "{old_as.role.name}" in '
                    f'project (UUID={old_as.sodar_uuid})'
                )
        # Prevent demoting if inherited role exists
        for old_role_as in RoleAssignment.objects.filter(
            project__in=project.get_parents(), user=attrs['user']
        ):
            if attrs['role'].rank > old_role_as.role.rank:
                raise serializers.ValidationError(
                    f'User inherits role "{old_role_as.role.name}", demoting '
                    f'from inherited role is not allowed'
                )
        return attrs

    def save(self, **kwargs):
        """Override save() to handle saving with project modify API"""
        # NOTE: Role not updated in response data unless we set self.instance
        # TODO: Figure out a clean fix
        self.instance = self.post_save(
            self.modify_assignment(
                data=self.validated_data,
                request=self.context['request'],
                project=self.context['project'],
                instance=self.instance,
            )
        )
        return self.instance

    def to_representation(self, instance):
        """
        Override to return proper user field depending on API version.
        NOTE: Requires request in context object!
        """
        ret = super().to_representation(instance)
        if (
            isinstance(ret.get('user'), dict)
            and parse_version(self.context['request'].version) >= VERSION_2_0
        ):
            ret['user'] = ret['user']['sodar_uuid']
        return ret


class RoleAssignmentNestedListSerializer(
    SODARNestedListSerializer, RoleAssignmentSerializer
):
    """Nested list serializer for the RoleAssignment model."""

    # Using API <2.0 serializer as default
    # TODO: Change to SlugRelatedField when removing support for <2.0 (#1691)
    user = SODARUserSerializer(read_only=True)

    class Meta(SODARNestedListSerializer.Meta):
        model = RoleAssignment
        fields = ['role', 'user', 'sodar_uuid']
        read_only_fields = ['role']


class ProjectInviteSerializer(
    ProjectInviteMixin, RoleAssignmentValidateMixin, SODARProjectModelSerializer
):
    """Serializer for the ProjectInvite model"""

    # Using API <2.0 serializer as default
    # TODO: Change to SlugRelatedField when removing support for <2.0 (#1691)
    issuer = SODARUserSerializer(read_only=True)
    role = serializers.SlugRelatedField(
        slug_field='name', queryset=Role.objects.all()
    )

    class Meta:
        model = ProjectInvite
        fields = [
            'email',
            'project',
            'role',
            'issuer',
            'date_created',
            'date_expire',
            'message',
            'sodar_uuid',
        ]
        read_only_fields = ['issuer', 'date_created', 'date_expire', 'active']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Validate email
        if not parseaddr(attrs['email'])[1]:
            raise serializers.ValidationError(
                'Invalid email address "{}"'.format(attrs['email'])
            )
        # Check for existing user
        user = User.objects.filter(email=attrs['email']).first()
        if user:
            raise serializers.ValidationError(
                'User already exist in system with given email '
                '"{}": {} ({})'.format(
                    attrs['email'], user.username, user.sodar_uuid
                )
            )
        return attrs

    def create(self, validated_data):
        validated_data['issuer'] = self.context['request'].user
        # validated_data['date_expire'] = get_expiry_date()
        validated_data['secret'] = build_secret()
        return super().create(validated_data)

    def save(self, **kwargs):
        obj = super().save(**kwargs)
        self.handle_invite(obj, self.context['request'], add_message=False)
        return self.post_save(obj)

    def to_representation(self, instance):
        """
        Override to return proper user field depending on API version.
        NOTE: Requires request in context object!
        """
        ret = super().to_representation(instance)
        if (
            isinstance(ret.get('issuer'), dict)
            and parse_version(self.context['request'].version) >= VERSION_2_0
        ):
            ret['issuer'] = ret['issuer']['sodar_uuid']
        return ret


class ProjectSerializer(ProjectModifyMixin, SODARModelSerializer):
    """Serializer for the Project model"""

    owner = serializers.CharField(write_only=True, required=False)
    parent = serializers.SlugRelatedField(
        slug_field='sodar_uuid',
        many=False,
        allow_null=True,
        queryset=Project.objects.filter(type=PROJECT_TYPE_CATEGORY),
    )
    readme = serializers.CharField(required=False, allow_blank=True)
    # NOTE: public_access or public_guest_access presence checked in validate()
    public_access = serializers.SlugRelatedField(
        slug_field='name',
        allow_null=True,
        required=False,
        queryset=Role.objects.all(),
    )
    archive = serializers.BooleanField(read_only=True)
    roles = RoleAssignmentNestedListSerializer(
        read_only=True, many=True, source='get_roles'
    )
    children = serializers.SlugRelatedField(
        slug_field='sodar_uuid',
        many=True,
        allow_null=True,
        read_only=True,
    )

    class Meta:
        model = Project
        fields = [
            'title',
            'type',
            'parent',
            'description',
            'readme',
            'public_access',
            'public_guest_access',
            'archive',
            'full_title',
            'owner',
            'roles',
            'children',
            'sodar_uuid',
        ]
        read_only_fields = ['full_title']

    def _validate_title(self, parent, attrs):
        """Validate title field"""
        title = attrs.get('title')
        if title and (
            CAT_DELIMITER in title
            or title.startswith(CAT_DELIMITER.strip())
            or title.endswith(CAT_DELIMITER.strip())
        ):
            raise serializers.ValidationError(CAT_DELIMITER_ERROR_MSG)
        if parent and title == parent.title:
            raise serializers.ValidationError('Title can\'t match with parent')
        if (
            title
            and not self.instance
            and Project.objects.filter(title=attrs['title'], parent=parent)
        ):
            raise serializers.ValidationError(
                'Title must be unique within parent'
            )

    def _validate_type(self, attrs):
        """Validate type field"""
        project_type = attrs.get('type')
        if project_type not in [
            PROJECT_TYPE_CATEGORY,
            PROJECT_TYPE_PROJECT,
            None,
        ]:  # None is ok for PATCH (will be updated in modify_project())
            raise serializers.ValidationError(
                f'Type is not {PROJECT_TYPE_CATEGORY} or {PROJECT_TYPE_PROJECT}'
            )
        if (
            project_type
            and self.instance
            and attrs['type'] != self.instance.type
        ):
            raise serializers.ValidationError(
                'Changing the project type is not allowed'
            )

    def _validate_parent(self, parent, attrs, current_user, disable_categories):
        """Validate parent field"""
        # Attempting to move project under category without perms
        if (
            parent
            and not current_user.is_superuser
            and not current_user.has_perm('projectroles.create_project', parent)
            and (not self.instance or self.instance.parent != parent)
        ):
            raise exceptions.PermissionDenied(
                'User lacks permission to place project under given category'
            )
        if parent and parent.is_project():
            raise serializers.ValidationError('Parent is not a category')
        elif (
            'parent' in attrs
            and not parent
            and self.instance
            and self.instance.parent
            and not current_user.is_superuser
        ):
            raise exceptions.PermissionDenied(
                'Only superusers are allowed to place categories in root'
            )

        # Attempting to create/move project in root
        if (
            'parent' in attrs
            and not parent
            and attrs.get('type') == PROJECT_TYPE_PROJECT
            and not disable_categories
        ):
            raise serializers.ValidationError(
                'Project must be placed under a category'
            )
        # Ensure we are not moving a category under one of its children
        if (
            parent
            and self.instance
            and self.instance.is_category()
            and parent in self.instance.get_children(flat=True)
        ):
            raise serializers.ValidationError(
                'Moving a category under its own child is not allowed'
            )

    def _validate_owner(self, attrs):
        """Validate owner field"""
        if attrs.get('owner'):
            if (
                self.partial
                and attrs['owner'] != self.instance.get_owner().user.sodar_uuid
            ):
                raise serializers.ValidationError(
                    'Modifying owner not allowed here, '
                    'use ownership transfer API view instead'
                )
            owner = User.objects.filter(sodar_uuid=attrs['owner']).first()
            if not owner:
                raise serializers.ValidationError('Owner not found')
            attrs['owner'] = owner
        elif not self.instance:
            raise serializers.ValidationError(
                'The "owner" parameter must be supplied for project creation'
            )

    def _validate_public_access(self, attrs):
        """Validate public_access and public_guest_access fields"""
        req_version = parse_version(self.context['request'].version)
        req_method = self.context['request'].method
        # Ensure either public_access or public_guest_access are present
        # NOTE: Done here for backwards compatibility with <v2.0
        if req_version >= VERSION_2_0 and 'public_guest_access' in attrs:
            raise serializers.ValidationError(
                'Field public_guest_access not supported by API >=v2.0, use '
                'public_access instead'
            )
        if req_method in ['POST', 'PUT']:
            if req_version >= VERSION_2_0 and 'public_access' not in attrs:
                raise serializers.ValidationError(
                    'Field public_access is required'
                )
            elif (
                req_version <= VERSION_1_1
                and 'public_guest_access' not in attrs
            ):
                raise serializers.ValidationError(
                    'Field public_guest_access is required'
                )

        # Validate public_access and public_guest_access for categories
        if attrs.get('type') == PROJECT_TYPE_CATEGORY and (
            attrs.get('public_guest_access') or attrs.get('public_access')
        ):
            raise serializers.ValidationError(
                'Public guest access is not allowed for categories'
            )

        # Set appropriate values depending on API version
        if parse_version(self.context['request'].version) < VERSION_2_0:
            if attrs['public_guest_access']:
                role_guest = Role.objects.filter(
                    name=PROJECT_ROLE_GUEST
                ).first()
                attrs['public_access'] = role_guest
                attrs['public_guest_access'] = True  # DEPRECATED
            else:
                attrs['public_access'] = None
                attrs['public_guest_access'] = False  # DEPRECATED

    def validate(self, attrs):
        site_mode = getattr(
            settings,
            'PROJECTROLES_SITE_MODE',
            SODAR_CONSTANTS['SITE_MODE_SOURCE'],
        )
        target_create = getattr(settings, 'PROJECTROLES_TARGET_CREATE', True)
        disable_categories = getattr(
            settings, 'PROJECTROLES_DISABLE_CATEGORIES', False
        )
        current_user = self.context['request'].user

        # Validation for remote sites and projects
        if self.instance and self.instance.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)
        elif (
            not self.instance
            and site_mode == SODAR_CONSTANTS['SITE_MODE_TARGET']
            and not target_create
        ):
            raise serializers.ValidationError(
                'Creation of local projects not allowed on this target site'
            )
        # Validate parent
        parent = attrs.get('parent')
        self._validate_parent(parent, attrs, current_user, disable_categories)
        # Validate title
        self._validate_title(parent, attrs)
        # Validate type
        self._validate_type(attrs)
        # Validate and set owner
        self._validate_owner(attrs)
        # Validate and update public_access and public_guest_access
        self._validate_public_access(attrs)

        # Set readme
        if 'readme' in attrs and 'raw' in attrs['readme']:
            attrs['readme'] = attrs['readme']['raw']
        return attrs

    def save(self, **kwargs):
        """Override save() to handle saving with project modify API"""
        # NOTE: post_save() not needed here since we do an atomic model.save()
        return self.modify_project(
            data=self.validated_data,
            request=self.context['request'],
            instance=self.instance,
        )

    def to_representation(self, instance):
        """
        Override to make sure fields are correctly returned.
        NOTE: Requires request in context object!
        """
        ret = super().to_representation(instance)
        req_version = parse_version(self.context['request'].version)
        # Set up project to get instance with UUID
        parent = ret.get('parent')
        project = Project.objects.get(
            title=ret['title'],
            **{'parent__sodar_uuid': parent} if parent else {},
        )
        user = self.context['request'].user

        # Return only title, full title and UUID for projects with finder role
        if (
            project.is_project()
            and project.parent
            and not project.has_role(user)
        ):
            parent_as = project.parent.get_role(user)
            if (
                parent_as
                and parent_as.role.rank >= ROLE_RANKING[PROJECT_ROLE_FINDER]
            ):
                return {
                    'title': project.title,
                    'full_title': project.full_title,
                    'sodar_uuid': str(project.sodar_uuid),
                }

        # Else return full serialization
        # Proper rendering of readme
        ret['readme'] = project.readme.raw or ''
        # Force project UUID
        if not ret.get('sodar_uuid'):
            ret['sodar_uuid'] = str(project.sodar_uuid)
        # Add inherited info to roles
        if ret.get('roles'):
            for k, v in ret['roles'].items():
                role_as = RoleAssignment.objects.get(sodar_uuid=k)
                ret['roles'][k]['inherited'] = (
                    True if role_as.project != project else False
                )
        # Set full_title manually
        ret['full_title'] = project.full_title
        # Remove children field for projects and API version <1.1
        if project.is_project() or req_version < VERSION_1_1:
            ret.pop('children', None)
        # Replace public_access with public_guest_access if API version <2.0
        if req_version < VERSION_2_0:
            ret['public_guest_access'] = ret['public_access'] is not None
            ret.pop('public_access', None)
        else:  # Else remove public_guest_access
            ret.pop('public_guest_access', None)
        return ret


class AppSettingSerializer(SODARProjectModelSerializer):
    """
    Serializer for the AppSetting model. Should only be used for read and list
    views. The sodar_uuid is not provided, as interacting with database objects
    directly is not the intended way to set/get app settings.
    """

    plugin_name = serializers.CharField(read_only=True)
    # Using API <2.0 serializer as default
    # TODO: Change to SlugRelatedField when removing support for <2.0 (#1691)
    user = SODARUserSerializer(read_only=True)

    class Meta:
        model = AppSetting
        fields = [
            'plugin_name',
            'project',
            'user',
            'name',
            'type',
            'value',
            'user_modifiable',
        ]
        read_only_fields = [*fields]

    def to_representation(self, instance):
        """Override to clean up data for serialization"""
        ret = super().to_representation(instance)
        if instance.app_plugin:
            ret['plugin_name'] = instance.app_plugin.name
        else:
            ret['plugin_name'] = 'projectroles'
        ret['value'] = instance.get_value()
        if (
            isinstance(ret.get('user'), dict)
            and parse_version(self.context['request'].version) >= VERSION_2_0
        ):
            ret['user'] = ret['user']['sodar_uuid']
        return ret
