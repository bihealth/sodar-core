"""Models for the projectroles app"""

import logging
import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from djangoplugins.models import Plugin
from markupfield.fields import MarkupField

from projectroles.constants import get_sodar_constants


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
logger = logging.getLogger(__name__)


# SODAR constants
SODAR_CONSTANTS = get_sodar_constants()
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_ROLE_FINDER = SODAR_CONSTANTS['PROJECT_ROLE_FINDER']
APP_SETTING_SCOPE_SITE = SODAR_CONSTANTS['APP_SETTING_SCOPE_SITE']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']
AUTH_TYPE_LOCAL = SODAR_CONSTANTS['AUTH_TYPE_LOCAL']
AUTH_TYPE_LDAP = SODAR_CONSTANTS['AUTH_TYPE_LDAP']
AUTH_TYPE_OIDC = SODAR_CONSTANTS['AUTH_TYPE_OIDC']

# Local constants
APP_NAME = 'projectroles'
ROLE_RANKING = {
    PROJECT_ROLE_OWNER: 10,
    PROJECT_ROLE_DELEGATE: 20,
    PROJECT_ROLE_CONTRIBUTOR: 30,
    PROJECT_ROLE_GUEST: 40,
    PROJECT_ROLE_FINDER: 50,
}
PROJECT_TYPE_CHOICES = [('CATEGORY', 'Category'), ('PROJECT', 'Project')]
APP_SETTING_TYPES = [
    APP_SETTING_TYPE_BOOLEAN,
    APP_SETTING_TYPE_INTEGER,
    APP_SETTING_TYPE_STRING,
    APP_SETTING_TYPE_JSON,
]
PROJECT_SEARCH_TYPES = ['project']
PROJECT_TAG_STARRED = 'STARRED'
CAT_DELIMITER = ' / '
CAT_DELIMITER_ERROR_MSG = 'String "{}" is not allowed in title'.format(
    CAT_DELIMITER
)
ROLE_PROJECT_TYPE_ERROR_MSG = (
    'Invalid project type "{project_type}" for ' 'role "{role_name}"'
)
CAT_PUBLIC_ACCESS_MSG = 'Public guest access is not allowed for categories'
ADD_EMAIL_ALREADY_SET_MSG = 'Email already set as {email_type} email for user'
REMOTE_PROJECT_UNIQUE_MSG = (
    'RemoteProject with the same project UUID and site anready exists'
)
AUTH_PROVIDER_OIDC = 'oidc'


# Project ----------------------------------------------------------------------


class ProjectManager(models.Manager):
    """Manager for custom table-level Project queries"""

    def find(self, search_terms, keywords=None, project_type=None):
        """
        Return projects with a partial match in full title or, including titles
        of parent Project objects, or the description of the current object.
        Restrict to project type if project_type is set.

        :param search_terms: Search terms (list)
        :param keywords: Optional search keywords as key/value pairs (dict)
        :param project_type: Project type or None
        :return: QuerySet of Project objects
        """
        projects = super().get_queryset().order_by('title')
        if project_type:
            projects = projects.filter(type=project_type)
        term_query = Q()
        for t in search_terms:
            term_query.add(Q(full_title__icontains=t), Q.OR)
            term_query.add(Q(description__icontains=t), Q.OR)
        return projects.filter(term_query).order_by('full_title')


class Project(models.Model):
    """
    A SODAR project. Can have one parent category in case of nested
    projects. The project must be of a specific type, of which "CATEGORY" and
    "PROJECT" are currently implemented. "CATEGORY" projects are used as
    containers for other projects.
    """

    #: Project title
    title = models.CharField(
        max_length=255, unique=False, help_text='Project title'
    )

    #: Type of project ("CATEGORY", "PROJECT")
    type = models.CharField(
        max_length=64,
        choices=PROJECT_TYPE_CHOICES,
        default=PROJECT_TYPE_PROJECT,
        help_text='Type of project ("CATEGORY", "PROJECT")',
    )

    #: Parent category if nested, otherwise null
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        related_name='children',
        help_text='Parent category if nested',
        on_delete=models.CASCADE,
    )

    #: Short project description
    description = models.CharField(
        max_length=512,
        unique=False,
        blank=True,
        null=True,
        help_text='Short project description',
    )

    #: Project README (optional, supports markdown)
    readme = MarkupField(
        null=True,
        blank=True,
        markup_type='markdown',
        help_text='Project README (optional, supports markdown)',
    )

    #: Public guest access
    public_guest_access = models.BooleanField(
        default=False,
        help_text='Allow public guest access for the project, also including '
        'unauthenticated users if allowed on the site',
    )

    #: Project is archived (read-only)
    archive = models.BooleanField(
        default=False,
        help_text='Project is archived (read-only)',
    )

    #: Full project title with parent path (auto-generated)
    full_title = models.CharField(
        max_length=4096,
        null=True,
        help_text='Full project title with parent path (auto-generated)',
    )

    #: Whether project has children with public access (auto-generated)
    has_public_children = models.BooleanField(
        default=False,
        help_text='Whether project has children with public access '
        '(auto-generated)',
    )

    #: Project SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='Project SODAR UUID'
    )

    # Set manager for custom queries
    objects = ProjectManager()

    class Meta:
        unique_together = ('title', 'parent')
        ordering = ['parent__title', 'title']

    def __str__(self):
        return self.full_title

    def __repr__(self):
        values = (
            self.title,
            self.type,
            self.parent.title if self.parent else None,
        )
        return 'Project({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Custom validation and field populating for Project"""
        self._validate_parent()
        self._validate_title()
        self._validate_parent_type()
        self._validate_public_guest_access()
        self._validate_archive()
        # Update full title of self and children
        self.full_title = self._get_full_title()
        # TODO: Save with commit=False with other args to avoid double save()?
        super().save(*args, **kwargs)
        if self.type == PROJECT_TYPE_CATEGORY:
            for child in self.children.all():
                child.save()
        # Update public children
        # NOTE: Parents will be updated in ProjectModifyMixin.modify_project()
        if self._has_public_children():
            self.has_public_children = True
            super().save(*args, **kwargs)

    def _validate_parent(self):
        """
        Validate parent value to ensure project can't be set as its own parent.
        """
        if self.parent == self:
            raise ValidationError('Project can not be set as its own parent')

    def _validate_parent_type(self):
        """Validate parent value to ensure parent can not be a project"""
        if self.parent and self.parent.type == PROJECT_TYPE_PROJECT:
            raise ValidationError(
                'Subprojects are only allowed within categories'
            )

    def _validate_public_guest_access(self):
        """
        Validate public guest access to ensure it is not set on categories.

        NOTE: Does not prevent saving but forces the value to be False, see
              issue #1404.
        """
        if self.type == PROJECT_TYPE_CATEGORY and self.public_guest_access:
            logger.warning(CAT_PUBLIC_ACCESS_MSG + ', setting to False')
            self.public_guest_access = False

    def _validate_title(self):
        """
        Validate title against parent title to ensure they don't equal parent.
        """
        if self.parent and self.title == self.parent.title:
            raise ValidationError('Project and parent titles can not be equal')
        if (
            CAT_DELIMITER in self.title
            or self.title.startswith(CAT_DELIMITER.strip())
            or self.title.endswith(CAT_DELIMITER.strip())
        ):
            raise ValidationError(CAT_DELIMITER_ERROR_MSG)

    def _validate_archive(self):
        """
        Validate archive status against project type to ensure archiving is only
        applied to projects.
        """
        if self.archive and self.type != PROJECT_TYPE_PROJECT:
            raise ValidationError(
                'Archiving a category is not currently supported'
            )

    def get_absolute_url(self):
        return reverse(
            'projectroles:detail', kwargs={'project': self.sodar_uuid}
        )

    # Internal helpers

    def _get_full_title(self):
        """Return full title of project with path."""
        parents = self.get_parents()
        ret = (
            CAT_DELIMITER.join([p.title for p in parents]) + CAT_DELIMITER
            if parents
            else ''
        )
        return ret + self.title

    def _has_public_children(self):
        """
        Return True if the project has any children with public guest access.
        """
        if self.type != PROJECT_TYPE_CATEGORY:
            return False
        for child in self.get_children():
            if child.public_guest_access:
                return True
            ret = child._has_public_children()
            if ret:
                return True
        return False

    def _update_public_children(self):
        """Update has_public_children for this project's parents."""
        if self.parent:
            parent = self.parent
            public_found = False
            while parent:
                if public_found:
                    parent.has_public_children = True
                else:
                    parent.has_public_children = parent._has_public_children()
                parent.save()
                if not public_found and parent.has_public_children:
                    public_found = True
                parent = parent.parent

    # Custom row-level functions

    def get_parents(self):
        """
        Return a list of parent projects in inheritance order.

        :return: List of Project objects
        """
        if not self.parent:
            return []
        ret = []
        parent = self.parent
        while parent:
            ret.append(parent)
            parent = parent.parent
        return reversed(ret)

    def get_children(self, flat=False):
        """
        Return child objects for a Category, sorted by full title.

        :param flat: Return all children recursively as a flat list (bool)
        :return: QuerySet
        """
        if self.type != PROJECT_TYPE_CATEGORY:
            return Project.objects.none()
        if flat:
            return Project.objects.filter(
                full_title__startswith=self.full_title + CAT_DELIMITER
            ).order_by('full_title')
        return self.children.all().order_by('title')

    def get_depth(self):
        """Return depth of project in the project tree structure (root=0)"""
        return len(self.full_title.split(CAT_DELIMITER)) - 1

    def get_role(self, user, inherited_only=False):
        """
        Return the currently active role for user, or None if not available.
        Returns the highest ranked role including inherited roles. In case of
        multiple roles of the same level in the hierarchy, the lowest one is
        returned.

        :param user: User object
        :param inherited_only: Only return an inherited role if True
                               (boolean, default=False)
        :return: RoleAssignment object or None
        """
        if not user or user.is_anonymous:
            return None
        projects = [self] if not inherited_only else []
        projects += list(self.get_parents())
        return (
            RoleAssignment.objects.filter(
                project__in=projects,
                user=user,
                role__project_types__contains=[self.type],
            )
            .order_by('role__rank', '-project__full_title')
            .first()
        )

    def get_roles(
        self,
        user=None,
        inherited=True,
        inherited_only=False,
        min_rank=None,
        max_rank=None,
    ):
        """
        Return project role assignments.

        :param user: Limit to user (User object or None)
        :param inherited: Include inherited roles (bool)
        :param inherited_only: Return only inherited roles (bool)
        :param min_rank: Limit roles to minimum rank (integer or None)
        :param max_rank: Limit roles to maximum rank (integer or None)
        :return: List of RoleAssignment objects
        :raise: ValueError If inheritance arguments conflict
        """
        if not inherited and inherited_only:
            raise ValueError(
                'Inherited set False and inherited_only set True, No results '
                'can be returned'
            )
        projects = [] if inherited_only else [self]
        # NOTE: We have to get inherited roles to exclude overridden ones
        parents = list(self.get_parents())
        projects += parents
        q_kwargs = {
            'project__in': projects,
            'role__project_types__contains': [self.type],
        }
        if user and user.is_authenticated:
            q_kwargs['user'] = user
        roles = RoleAssignment.objects.filter(**q_kwargs).order_by(
            '-project__full_title', 'role__name', 'user'
        )
        user_roles = {}
        for a in roles:
            u = a.user
            rank_ok = (not min_rank or a.role.rank >= min_rank) and (
                not max_rank or a.role.rank <= max_rank
            )
            # Local role (always returned first if it exists)
            if a.project == self and not inherited_only and rank_ok:
                user_roles[u] = a
            # Inherited role of higher rank
            elif (
                inherited
                and a.project in parents
                and (
                    u not in user_roles or a.role.rank < user_roles[u].role.rank
                )
                and rank_ok
            ):
                user_roles[u] = a
            # Pop overridden role if in list
            elif (
                a.project in parents
                and u in user_roles
                and a.role.rank < user_roles[u].role.rank
            ):
                user_roles.pop(u, None)
        return list(user_roles.values())

    def get_roles_by_rank(
        self, role_name, inherited=True, inherited_only=False
    ):
        """
        Return RoleAssignments for specific role name. Will also include custom
        roles of identical rank once role customization is implemented (see
        issue #288).

        :param role_name: Name of role (string)
        :param inherited: Include inherited roles (bool)
        :param inherited_only: Return only inherited roles (bool)
        :return: List
        """
        if role_name not in ROLE_RANKING:
            role = Role.objects.filter(name=role_name).first()
            if not role:
                raise ValueError('Unknown role "{}"'.format(role_name))
            rank = role.rank
        else:
            rank = ROLE_RANKING[role_name]
        return self.get_roles(
            inherited=inherited,
            inherited_only=inherited_only,
            min_rank=rank,
            max_rank=rank,
        )

    def get_owner(self):
        """
        Return RoleAssignment for local (non-inherited) owner or None if not
        set.

        :return: QuerySet
        """
        return self.local_roles.filter(role__name=PROJECT_ROLE_OWNER).first()

    def get_owners(self, inherited=True, inherited_only=False):
        """
        Return RoleAssignments for project owner as well as possible inherited
        owners from parent projects.

        :param inherited: Include inherited roles (bool)
        :param inherited_only: Return only inherited roles (bool)
        :return: List
        """
        rank = ROLE_RANKING[PROJECT_ROLE_OWNER]
        return self.get_roles(
            inherited=inherited,
            inherited_only=inherited_only,
            min_rank=rank,
            max_rank=rank,
        )

    def get_delegates(self, inherited=True, inherited_only=False):
        """
        Return RoleAssignments for delegates. Excludes delegates with an
        inherited owner role.

        :param inherited: Include inherited roles (bool)
        :param inherited_only: Return only inherited roles (bool)
        :return: List
        """
        rank = ROLE_RANKING[PROJECT_ROLE_DELEGATE]
        return self.get_roles(
            inherited=inherited,
            inherited_only=inherited_only,
            min_rank=rank,
            max_rank=rank,
        )

    def is_owner(self, user):
        """
        Return True if user is owner in this project or inherits ownership from
        a parent category.

        :return: Boolean
        """
        if not user.is_authenticated:
            return False
        role_as = self.get_role(user)
        if role_as and role_as.role.rank == ROLE_RANKING[PROJECT_ROLE_OWNER]:
            return True
        return False

    def is_delegate(self, user):
        """
        Return True if user is delegate in this project or inherits delegate
        status from a parent category.

        :return: Boolean
        """
        if not user.is_authenticated:
            return False
        role_as = self.get_role(user)
        if role_as and role_as.role.rank == ROLE_RANKING[PROJECT_ROLE_DELEGATE]:
            return True
        return False

    def is_owner_or_delegate(self, user):
        """
        Return True if user is either an owner or a delegate in this project.
        Includes inherited assignments.

        :return: Boolean
        """
        if not user.is_authenticated:
            return False
        role_as = self.get_role(user)
        if role_as and role_as.role.rank in [
            ROLE_RANKING[PROJECT_ROLE_OWNER],
            ROLE_RANKING[PROJECT_ROLE_DELEGATE],
        ]:
            return True
        return False

    def get_members(self, inherited=True):
        """
        Return RoleAssignments for members of project excluding owner and
        delegates.

        :param inherited: Include inherited roles (boolean)
        :return: List of RoleAssignments
        """
        return self.get_roles(
            inherited=inherited,
            min_rank=Role.objects.get(name=PROJECT_ROLE_CONTRIBUTOR).rank,
        )

    def has_role(self, user):
        """
        Return whether user has roles in Project. Returns True if user has local
        role, inherits a role from a parent category, or if public guest access
        is enabled for the project.

        :param user: User object
        :return: Boolean
        """
        if self.public_guest_access or self.get_role(user=user):
            return True
        return False

    def has_role_in_children(self, user):
        """
        Return True if user has a role in any of the children in the project.
        Also returns true if public guest access is true for any child.

        :param user: User object
        :return: Boolean
        """
        if self.type != PROJECT_TYPE_CATEGORY:
            return False
        # User with role in self has at least the same role in children
        if self.has_role(user):
            return True
        children = self.get_children(flat=True)
        if (
            any([c.public_guest_access for c in children])
            or RoleAssignment.objects.filter(
                user=user, project__in=children
            ).count()
            > 0
        ):
            return True
        return False

    def get_source_site(self):
        """
        Return source site or None if this is a locally defined project.

        :return: RemoteProject object or None
        """
        if (
            settings.PROJECTROLES_SITE_MODE
            == SODAR_CONSTANTS['SITE_MODE_SOURCE']
        ):
            return None
        RemoteProject = apps.get_model(APP_NAME, 'RemoteProject')
        try:
            return RemoteProject.objects.get(
                project_uuid=self.sodar_uuid,
                site__mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            ).site
        except RemoteProject.DoesNotExist:
            pass
        return None

    def is_remote(self):
        """
        Return True if current project has been retrieved from a remote SODAR
        site.

        :return: Boolean
        """
        if (
            settings.PROJECTROLES_SITE_MODE
            == SODAR_CONSTANTS['SITE_MODE_TARGET']
            and self.get_source_site()
        ):
            return True
        return False

    def is_revoked(self):
        """
        Return True if remote access has been revoked for the project.

        :return: Boolean
        """
        if self.is_remote():
            remote_project = RemoteProject.objects.filter(
                project=self, site=self.get_source_site()
            ).first()
            if (
                remote_project
                and remote_project.level
                == SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']
            ):
                return True
        return False

    def set_public(self, public=True):
        """Helper for setting value of public_guest_access"""
        if public != self.public_guest_access:
            # NOTE: Validation no longer raises an exception (see ¤1404)
            if self.type == PROJECT_TYPE_CATEGORY and public:
                raise ValidationError(CAT_PUBLIC_ACCESS_MSG)
            self.public_guest_access = public
            self.save()
            self._update_public_children()  # Update for parents

    def set_archive(self, status=True):
        """
        Helper for setting archive value. Raises ValidationError for categories.
        """
        if status != self.archive:
            self.archive = status
            self.save()

    def get_log_title(self, full_title=False):
        """
        Return a logger-friendly title for the project.

        :param full_title: Display full title if True (boolean)
        :return: String
        """
        return '"{}" ({})'.format(
            self.full_title if full_title else self.title, self.sodar_uuid
        )


# Role -------------------------------------------------------------------------


def get_role_project_type_default():
    """Return default value for Role.project_type"""
    return [PROJECT_TYPE_CATEGORY, PROJECT_TYPE_PROJECT]


class Role(models.Model):
    """Role definition, used to assign roles to projects in RoleAssignment"""

    #: Name of role
    name = models.CharField(
        max_length=64, unique=True, help_text='Name of role'
    )

    #: Role rank for determining role hierarchy
    rank = models.IntegerField(
        default=0,  # 0 = No rank
        help_text='Role rank for determining role hierarchy',
    )

    #: Allowed project types for the role
    project_types = ArrayField(
        models.CharField(max_length=64, blank=False),
        default=get_role_project_type_default,
        help_text='Allowed project types for the role',
    )

    #: Role description
    description = models.TextField(help_text='Role description')

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Role({})'.format(repr(self.name))


# RoleAssignment ---------------------------------------------------------------


class RoleAssignment(models.Model):
    """
    Assignment of an user to a role in a project. One local assignment per user
    is allowed for each project.

    One local project owner assignment is allowed for a project. Local project
    delegate assignements might be limited using PROJECTROLES_DELEGATE_LIMIT.

    Inherited role assignments can be accessed via the Project model API, e.g.
    Project.get_roles().
    """

    #: Project in which role is assigned
    project = models.ForeignKey(
        Project,
        related_name='local_roles',
        help_text='Project in which role is assigned',
        on_delete=models.CASCADE,
    )

    #: User for whom role is assigned
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name='roles',
        help_text='User for whom role is assigned',
        on_delete=models.CASCADE,
    )

    #: Role to be assigned
    role = models.ForeignKey(
        Role,
        related_name='assignments',
        help_text='Role to be assigned',
        on_delete=models.CASCADE,
    )

    #: RoleAssignment SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='RoleAssignment SODAR UUID'
    )

    class Meta:
        ordering = [
            'project__parent__title',
            'project__title',
            'role__name',
            'user__username',
        ]

    def __str__(self):
        return '{}: {}: {}'.format(self.project, self.role, self.user)

    def __repr__(self):
        values = (self.project.title, self.user.username, self.role.name)
        return 'RoleAssignment({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Version of save() to include custom validation for RoleAssignment"""
        self._validate_project_type()
        self._validate_user()
        self._validate_owner()
        self._validate_delegate()
        super().save(*args, **kwargs)

    def _validate_project_type(self):
        """Validate type of project to ensure it is in allowed types"""
        if self.project.type not in self.role.project_types:
            raise ValidationError(
                ROLE_PROJECT_TYPE_ERROR_MSG.format(
                    project_type=self.project.type, role_name=self.role.name
                )
            )

    def _validate_user(self):
        """
        Validate fields to ensure user has only one role set for the project.
        """
        role_as = RoleAssignment.objects.filter(
            project=self.project, user=self.user
        ).first()
        if role_as and (not self.pk or role_as.pk != self.pk):
            raise ValidationError(
                'Role {} already set for {} in {}'.format(
                    role_as.role, role_as.user, role_as.project
                )
            )

    def _validate_owner(self):
        """
        Validate role to ensure no more than one project owner is assigned to a
        project.
        """
        if self.role.name == PROJECT_ROLE_OWNER:
            owner = self.project.get_owner()
            if owner and (not self.pk or owner.pk != self.pk):
                raise ValidationError(
                    'User {} already set as owner of {}'.format(
                        owner, self.project
                    )
                )

    def _validate_delegate(self):
        """
        Validate role to ensure no more than the allowed amount of project
        delegates are assigned to a project.
        """
        if (
            self.role.name != PROJECT_ROLE_DELEGATE
            or self.project.is_remote()  # No validation for remote projects
        ):
            return
        del_limit = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)
        delegates = self.project.get_delegates(inherited=False)
        if 0 < del_limit <= len(delegates) and (
            not self.pk
            or self.project.local_roles.filter(
                role__name=PROJECT_ROLE_DELEGATE, pk=self.pk
            )
            is None
        ):
            raise ValidationError(
                'The local delegate limit for this project ({}) has already '
                'been reached.'.format(del_limit)
            )


# AppSetting -------------------------------------------------------------------


class AppSettingManager(models.Manager):
    """Manager for custom table-level AppSetting queries"""

    def get_setting_value(
        self, plugin_name, setting_name, project=None, user=None
    ):
        """
        Return value of setting_name for plugin_name in project or for user.

        Note that project and/or user must be set.

        :param plugin_name: App plugin name (string)
        :param setting_name: Name of setting (string)
        :param project: Project object or pk
        :param user: User object or pk
        :return: Value (string)
        :raise: AppSetting.DoesNotExist if setting is not found
        """
        query_parameters = {
            'name': setting_name,
            'project': project,
            'user': user,
        }
        if not plugin_name == APP_NAME:
            query_parameters['app_plugin__name'] = plugin_name
        setting = super().get_queryset().get(**query_parameters)
        return setting.get_value()


class AppSetting(models.Model):
    """
    Project and users settings value.

    The settings are defined in the "app_settings" member in a SODAR project
    app's plugin. The scope of each setting can be either "USER" or "PROJECT",
    defined for each setting in app_settings. Project AND user-specific settings
    or settings which don't belong to either are are currently not supported.
    """

    #: App to which the setting belongs
    app_plugin = models.ForeignKey(
        Plugin,
        null=True,
        unique=False,
        related_name='settings',
        help_text='App to which the setting belongs',
        on_delete=models.CASCADE,
    )

    #: Project to which the setting belongs
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        related_name='settings',
        help_text='Project to which the setting belongs',
        on_delete=models.CASCADE,
    )

    #: Project to which the setting belongs
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='user_settings',
        help_text='User to which the setting belongs',
        on_delete=models.CASCADE,
    )

    #: Name of the setting
    name = models.CharField(
        max_length=255, unique=False, help_text='Name of the setting'
    )

    #: Type of the setting
    type = models.CharField(
        max_length=64, unique=False, help_text='Type of the setting'
    )

    #: Value of the setting
    value = models.CharField(
        unique=False,
        null=True,
        blank=True,
        help_text='Value of the setting',
    )

    #: Optional JSON value for the setting
    value_json = models.JSONField(
        null=True, default=dict, help_text='Optional JSON value for the setting'
    )

    #: Setting visibility in forms
    user_modifiable = models.BooleanField(
        default=True, help_text='Setting visibility in forms'
    )

    #: AppSetting SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='AppSetting SODAR UUID'
    )

    # Set manager for custom queries
    objects = AppSettingManager()

    class Meta:
        ordering = ['project__title', 'app_plugin__name', 'name']
        unique_together = ['project', 'user', 'app_plugin', 'name']

    def __str__(self):
        plugin_name = self.app_plugin.name if self.app_plugin else APP_NAME
        if self.project:
            label = self.project.title
        elif self.user:
            label = self.user.username
        else:
            label = 'SITE'
        return '{}: {} / {}'.format(label, plugin_name, self.name)

    def __repr__(self):
        values = (
            self.project.title if self.project else None,
            self.user.username if self.user else None,
            self.app_plugin.name if self.app_plugin else APP_NAME,
            self.name,
        )
        return 'AppSetting({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Version of save() to convert 'value' data according to 'type'"""
        if self.type == APP_SETTING_TYPE_BOOLEAN:
            self.value = str(int(self.value))
        elif self.type == APP_SETTING_TYPE_INTEGER:
            self.value = str(self.value)
        super().save(*args, **kwargs)

    # Custom row-level functions

    def get_value(self):
        """Return value of the setting in the format specified in 'type'"""
        if self.type == APP_SETTING_TYPE_INTEGER:
            return int(self.value)
        elif self.type == APP_SETTING_TYPE_BOOLEAN:
            return bool(int(self.value))
        elif self.type == APP_SETTING_TYPE_JSON:
            return self.value_json
        return self.value


# ProjectInvite ----------------------------------------------------------------


class ProjectInvite(models.Model):
    """
    Invite which is sent to a non-logged in user, determining their role in
    the project.
    """

    #: Email address of the person to be invited
    email = models.EmailField(
        unique=False,
        null=False,
        blank=False,
        help_text='Email address of the person to be invited',
    )

    #: Project to which the person is invited
    project = models.ForeignKey(
        Project,
        null=False,
        related_name='invites',
        help_text='Project to which the person is invited',
        on_delete=models.CASCADE,
    )

    #: Role assigned to the person
    role = models.ForeignKey(
        Role,
        null=False,
        help_text='Role assigned to the person',
        on_delete=models.CASCADE,
    )

    #: User who issued the invite
    issuer = models.ForeignKey(
        AUTH_USER_MODEL,
        null=False,
        related_name='issued_invites',
        help_text='User who issued the invite',
        on_delete=models.CASCADE,
    )

    #: DateTime of invite creation
    date_created = models.DateTimeField(
        auto_now_add=True, help_text='DateTime of invite creation'
    )

    #: Expiration of invite as DateTime
    date_expire = models.DateTimeField(
        null=False, help_text='Expiration of invite as DateTime'
    )

    #: Message to be included in the invite email (optional)
    message = models.TextField(
        blank=True,
        help_text='Message to be included in the invite email (optional)',
    )

    #: Secret token provided to user with the invite
    secret = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text='Secret token provided to user with the invite',
    )

    #: Status of the invite (False if claimed or revoked)
    active = models.BooleanField(
        default=True,
        help_text='Status of the invite (False if claimed or revoked)',
    )

    #: ProjectInvite SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='ProjectInvite SODAR UUID'
    )

    class Meta:
        ordering = ['project__title', 'email', 'role__name']

    def __str__(self):
        return '{}: {} ({}){}'.format(
            self.project,
            self.email,
            self.role.name,
            ' [ACTIVE]' if self.active else '',
        )

    def __repr__(self):
        values = (self.project.title, self.email, self.role.name, self.active)
        return 'ProjectInvite({})'.format(', '.join(repr(v) for v in values))

    @classmethod
    def _get_date_expire(cls):
        """
        Return expiry date based on current date + INVITE_EXPIRY_DAYS

        :return: DateTime object
        """
        return timezone.now() + timezone.timedelta(
            days=settings.PROJECTROLES_INVITE_EXPIRY_DAYS
        )

    def save(self, *args, **kwargs):
        if not self.pk and not self.date_expire:  # Set date_expire on create
            self.date_expire = self._get_date_expire()
        super().save(*args, **kwargs)

    # Custom row-level functions

    def is_ldap(self):
        """
        Return True if invite is intended for an LDAP user.

        :return: Boolean
        """
        # Only consider LDAP if enabled in Django settings
        if not settings.ENABLE_LDAP:
            return False
        # Check if domain is associated with LDAP
        domain = self.email.split('@')[1].lower()
        domain_no_tld = domain.split('.')[0].lower()
        ldap_domains = [
            getattr(settings, 'AUTH_LDAP_USERNAME_DOMAIN', '').lower(),
            getattr(settings, 'AUTH_LDAP2_USERNAME_DOMAIN', '').lower(),
        ]
        alt_domains = [
            a.lower() for a in getattr(settings, 'LDAP_ALT_DOMAINS', [])
        ]
        if domain_no_tld in ldap_domains or domain in alt_domains:
            return True
        return False

    def get_url(self, request):
        """
        Return invite URL for a project invitation.

        :param request: HttpRequest object
        :return: URL (string)
        """
        return request.build_absolute_uri(
            reverse(
                'projectroles:invite_accept', kwargs={'secret': self.secret}
            )
        )

    def reset_date_expire(self):
        """
        Reset date_expire to current date plus defined expiry days. Saves the
        object.
        """
        self.date_expire = self._get_date_expire()
        self.save()


# RemoteSite -------------------------------------------------------------------


class RemoteSite(models.Model):
    """Remote SODAR site"""

    #: Site name
    name = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text='Site name',
    )

    #: Site URL
    url = models.URLField(
        max_length=2000,
        blank=False,
        null=False,
        unique=False,
        help_text='Site URL',
    )

    #: Site mode
    mode = models.CharField(
        max_length=64,
        unique=False,
        blank=False,
        null=False,
        default=SODAR_CONSTANTS['SITE_MODE_TARGET'],
        help_text='Site mode',
    )

    #: Site description
    description = models.TextField(help_text='Site description')

    #: Secret token used to connect to the master site
    secret = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=True,  # Can be NULL for Peer Mode
        help_text='Secret token for connecting to the source site',
    )

    #: RemoteSite visibilty to users
    user_display = models.BooleanField(
        default=True, unique=False, help_text='Display site to users'
    )

    #: RemoteSite project access modifiability for owners and delegates
    owner_modifiable = models.BooleanField(
        default=True,
        unique=False,
        help_text='Allow owners and delegates to modify project access for '
        'this site',
    )

    #: RemoteSite relation UUID (local)
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='RemoteSite relation UUID (local)',
    )

    class Meta:
        ordering = ['name']
        unique_together = ['url', 'mode', 'secret']

    def __str__(self):
        return '{} ({})'.format(self.name, self.mode)

    def __repr__(self):
        values = (self.name, self.mode, self.url)
        return 'RemoteSite({})'.format(', '.join(repr(v) for v in values))

    def save(self, *args, **kwargs):
        """Version of save() to include custom validation"""
        self._validate_mode()
        super().save(*args, **kwargs)

    def _validate_mode(self):
        """Validate mode value"""
        if self.mode not in SODAR_CONSTANTS['SITE_MODES']:
            raise ValidationError(
                'Mode "{}" not found in SITE_MODES'.format(self.mode)
            )

    # Custom row-level functions

    def get_access_date(self):
        """Return date of latest project access by remote site"""
        projects = (
            RemoteProject.objects.filter(site=self)
            .exclude(date_access__isnull=True)
            .order_by('-date_access')
        )
        if projects.count() > 0:
            return projects.first().date_access

    def get_url(self):
        """Return sanitized site URL"""
        if self.url[-1] == '/':
            return self.url[:-1]
        return self.url


# RemoteProject ----------------------------------------------------------------


class RemoteProject(models.Model):
    """Remote project relation"""

    #: Related project UUID
    project_uuid = models.UUIDField(
        default=None, unique=False, help_text='Project UUID'
    )

    #: Related project object (if created locally)
    project = models.ForeignKey(
        Project,
        related_name='remotes',
        blank=True,
        null=True,
        help_text='Related project object (if created locally)',
        on_delete=models.CASCADE,
    )

    #: Related remote SODAR site
    site = models.ForeignKey(
        RemoteSite,
        null=False,
        related_name='projects',
        help_text='Remote SODAR site',
        on_delete=models.CASCADE,
    )

    #: Project access level
    level = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=False,
        default=SODAR_CONSTANTS['REMOTE_LEVEL_NONE'],
        help_text='Project access level',
    )

    #: DateTime of last access from/to remote site
    date_access = models.DateTimeField(
        null=True,
        auto_now_add=False,
        help_text='DateTime of last access from/to remote site',
    )

    #: RemoteProject relation UUID (local)
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='RemoteProject relation UUID (local)',
    )

    class Meta:
        ordering = ['site__name', 'project_uuid']

    def save(self, *args, **kwargs):
        # NOTE: Can't use unique constraint with foreign key relation
        rp = self.__class__.objects.filter(
            project_uuid=self.project_uuid, site=self.site
        ).first()
        if rp and rp.id != self.id:
            raise ValidationError(REMOTE_PROJECT_UNIQUE_MSG)
        super().save(*args, **kwargs)

    def __str__(self):
        return '{}: {} ({})'.format(
            self.site.name, str(self.project_uuid), self.site.mode
        )

    def __repr__(self):
        values = (self.site.name, str(self.project_uuid), self.site.mode)
        return 'RemoteProject({})'.format(', '.join(repr(v) for v in values))

    # Custom row-level functions

    def get_project(self):
        """Get the related Project object"""
        return (
            self.project
            or Project.objects.filter(sodar_uuid=self.project_uuid).first()
        )


# User Models ------------------------------------------------------------------


class SODARUser(AbstractUser):
    """
    SODAR compatible abstract user model. Use this on your SODAR Core based
    site.
    """

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_('Name of User'), blank=True, max_length=255)

    #: User SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='User SODAR UUID'
    )

    class Meta:
        abstract = True
        ordering = ['name', 'username']

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.set_group()

    def get_full_name(self):
        """Return full name or username if not set"""
        if hasattr(self, 'name') and self.name:
            return self.name
        elif self.first_name and self.last_name:
            return '{} {}'.format(self.first_name, self.last_name)
        return self.username

    def get_display_name(self, inc_user=False):
        """
        Return user name for displaying in UI.

        :param inc_user: Include username if true (boolean, default=False)
        :return: String
        """
        ret = self.get_full_name()
        if ret != self.username and inc_user:
            ret += f' ({self.username})'
        return ret

    def get_form_label(self, email=False):
        """
        Return user label with full name, username and optional email.

        :param email: Return email if True (boolean, default=False)
        :return: String
        """
        ret = self.get_full_name()
        if ret != self.username:
            ret += ' ({})'.format(self.username)
        if email and self.email:
            ret += ' <{}>'.format(self.email)
        return ret

    def get_auth_type(self):
        """
        Return user authentication type: OIDC, LDAP or local.

        :return: String which may equal AUTH_TYPE_OIDC, AUTH_TYPE_LDAP or
                 AUTH_TYPE_LOCAL.
        """
        groups = [g.name for g in self.groups.all()]
        if 'oidc' in groups:
            return AUTH_TYPE_OIDC
        elif (
            self.username.find('@') != -1
            and self.username.split('@')[1].lower() in groups
        ):
            return AUTH_TYPE_LDAP
        return AUTH_TYPE_LOCAL

    def is_local(self):
        """
        Return True if user is of type AUTH_TYPE_LOCAL.

        :return: Boolean
        """
        return self.get_auth_type() == AUTH_TYPE_LOCAL

    def set_group(self):
        """Set user group based on user name or social auth provider"""
        social_auth = getattr(self, 'social_auth', None)
        if social_auth:
            social_auth = social_auth.first()
        ldap_domains = [
            getattr(settings, 'AUTH_LDAP_USERNAME_DOMAIN', '').upper(),
            getattr(settings, 'AUTH_LDAP2_USERNAME_DOMAIN', '').upper(),
        ]
        # OIDC user group
        if social_auth and social_auth.provider == AUTH_PROVIDER_OIDC:
            group_name = AUTH_PROVIDER_OIDC
        # LDAP domain user groups
        elif (
            self.username.find('@') != -1
            and self.username.split('@')[1].upper() in ldap_domains
        ):
            group_name = self.username.split('@')[1].lower()
        # System user group for local users
        else:
            group_name = SODAR_CONSTANTS['SYSTEM_USER_GROUP']
        group, created = Group.objects.get_or_create(name=group_name)
        if group not in self.groups.all():
            group.user_set.add(self)
            logger.info(
                'Set user group "{}" for {}'.format(group_name, self.username)
            )
            return group_name

    def update_full_name(self):
        """
        Update full name of user.

        :return: String
        """
        # Save user name from first_name and last_name into name
        full_name = ''
        if self.first_name != '':
            full_name = self.first_name + (
                ' ' + self.last_name if self.last_name != '' else ''
            )
        if self.name != full_name:
            self.name = full_name
            self.save()
            logger.info(
                'Full name updated for user {}: {}'.format(
                    self.username, self.name
                )
            )
        return self.name

    def update_ldap_username(self):
        """
        Update username for an LDAP user.

        :return: String
        """
        # Make domain in username uppercase
        if (
            self.username.find('@') != -1
            and self.username.split('@')[1].islower()
        ):
            u_split = self.username.split('@')
            self.username = u_split[0] + '@' + u_split[1].upper()
            self.save()
        return self.username


class SODARUserAdditionalEmail(models.Model):
    """
    Model representing an additional email address for a user. Stores
    information for email verification.
    """

    #: User for whom the email is assigned
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name='additional_emails',
        help_text='User for whom the email is assigned',
        on_delete=models.CASCADE,
    )

    #: Email address
    email = models.EmailField(
        unique=False,
        null=False,
        blank=False,
        help_text='Email address',
    )

    #: Email verification status
    verified = models.BooleanField(
        default=False, help_text='Email verification status'
    )

    #: Secret token for email verification
    secret = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=True,
        help_text='Secret token for email verification',
    )

    #: DateTime of creation
    date_created = models.DateTimeField(
        auto_now_add=True, help_text='DateTime of creation'
    )

    #: DateTime of last modification
    date_modified = models.DateTimeField(
        auto_now=True, help_text='DateTime of last modification'
    )

    #: SODARUserAdditionalEmail SODAR UUID
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text='SODARUserAdditionalEmail SODAR UUID',
    )

    class Meta:
        ordering = ['user__username', 'email']
        unique_together = ['user', 'email']

    def __str__(self):
        return '{}: {}'.format(self.user.username, self.email)

    def __repr__(self):
        values = (
            self.user.username,
            self.email,
            str(self.verified),
            self.secret,
            str(self.sodar_uuid),
        )
        return 'SODARUserAdditionalEmail({})'.format(
            ', '.join(repr(v) for v in values)
        )

    def _validate_email_unique(self):
        """
        Assert the same email has not yet been set for the user.
        """
        if self.email == self.user.email:
            raise ValidationError(
                ADD_EMAIL_ALREADY_SET_MSG.format(email_type='primary')
            )

    def save(self, *args, **kwargs):
        self._validate_email_unique()
        super().save(*args, **kwargs)
