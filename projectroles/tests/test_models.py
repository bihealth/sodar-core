"""Tests for models in the projectroles Django app"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django.test import override_settings

from test_plus.test import TestCase

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    AppSetting,
    RemoteSite,
    RemoteProject,
    SODAR_CONSTANTS,
    ROLE_RANKING,
    CAT_DELIMITER,
)
from projectroles.plugins import get_app_plugin
from projectroles.utils import build_secret


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_ROLE_FINDER = SODAR_CONSTANTS['PROJECT_ROLE_FINDER']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']

# Local constants
SECRET = 'rsd886hi8276nypuvw066sbvv0rb2a6x'
EXAMPLE_APP_NAME = 'example_project_app'
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.example.org'
REMOTE_SITE_SECRET = build_secret()
REMOTE_SITE_USER_DISPLAY = True


class ProjectMixin:
    """Helper mixin for Project creation"""

    @classmethod
    def make_project(
        cls,
        title,
        type,
        parent,
        description='',
        readme=None,
        public_guest_access=False,
        archive=False,
        sodar_uuid=None,
    ):
        """Make and save a Project"""
        values = {
            'title': title,
            'type': type,
            'parent': parent,
            'description': description,
            'readme': readme,
            'archive': archive,
            'public_guest_access': public_guest_access,
        }
        if sodar_uuid:
            values['sodar_uuid'] = sodar_uuid
        project = Project(**values)
        project.save()
        return project


class RoleMixin:
    """Helper mixin for Role initialization"""

    def init_roles(self):
        """Initialize SODAR Core roles for tests"""
        self.role_owner = Role.objects.get_or_create(
            name=PROJECT_ROLE_OWNER, rank=ROLE_RANKING[PROJECT_ROLE_OWNER]
        )[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE, rank=ROLE_RANKING[PROJECT_ROLE_DELEGATE]
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR,
            rank=ROLE_RANKING[PROJECT_ROLE_CONTRIBUTOR],
        )[0]
        self.role_guest = Role.objects.get_or_create(
            name=PROJECT_ROLE_GUEST, rank=ROLE_RANKING[PROJECT_ROLE_GUEST]
        )[0]
        self.role_finder = Role.objects.get_or_create(
            name=PROJECT_ROLE_FINDER,
            rank=ROLE_RANKING[PROJECT_ROLE_FINDER],
            project_types=[PROJECT_TYPE_CATEGORY],
        )[0]


class RoleAssignmentMixin:
    """Helper mixin for RoleAssignment creation"""

    @classmethod
    def make_assignment(cls, project, user, role):
        """Make and save a RoleAssignment"""
        values = {'project': project, 'user': user, 'role': role}
        result = RoleAssignment(**values)
        result.save()
        return result


class ProjectInviteMixin:
    """Helper mixin for ProjectInvite creation"""

    @classmethod
    def make_invite(
        cls,
        email,
        project,
        role,
        issuer,
        message='',
        date_expire=None,
        secret=None,
    ):
        """Make and save a ProjectInvite"""
        values = {
            'email': email,
            'project': project,
            'role': role,
            'issuer': issuer,
            'message': message,
            'date_expire': date_expire
            if date_expire
            else (
                timezone.now()
                + timezone.timedelta(
                    days=settings.PROJECTROLES_INVITE_EXPIRY_DAYS
                )
            ),
            'secret': secret or SECRET,
            'active': True,
        }
        invite = ProjectInvite(**values)
        invite.save()
        return invite


class AppSettingMixin:
    """Helper mixin for AppSetting creation"""

    @classmethod
    def make_setting(
        cls,
        app_name,
        name,
        setting_type,
        value,
        value_json={},
        user_modifiable=True,
        project=None,
        user=None,
        sodar_uuid=None,
    ):
        """Make and save a AppSetting"""
        values = {
            'app_plugin': None
            if app_name == 'projectroles'
            else get_app_plugin(app_name).get_model(),
            'project': project,
            'name': name,
            'type': setting_type,
            'value': value,
            'value_json': value_json,
            'user_modifiable': user_modifiable,
            'user': user,
        }
        if sodar_uuid:
            values['sodar_uuid'] = sodar_uuid
        setting = AppSetting(**values)
        setting.save()
        return setting


class RemoteSiteMixin:
    """Helper mixin for RemoteSite creation"""

    @classmethod
    def make_site(
        cls,
        name,
        url,
        user_display=REMOTE_SITE_USER_DISPLAY,
        mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
        description='',
        secret=build_secret(),
    ):
        """Make and save a RemoteSite"""
        values = {
            'name': name,
            'url': url,
            'mode': mode,
            'description': description,
            'secret': secret,
            'user_display': user_display,
        }
        site = RemoteSite(**values)
        site.save()
        return site


class RemoteProjectMixin:
    """Helper mixin for RemoteProject creation"""

    @classmethod
    def make_remote_project(
        cls, project_uuid, site, level, date_access=None, project=None
    ):
        """Make and save a RemoteProject"""
        if isinstance(project_uuid, str):
            project_uuid = uuid.UUID(project_uuid)
        values = {
            'project_uuid': project_uuid,
            'site': site,
            'level': level,
            'date_access': date_access,
            'project': project
            if project
            else Project.objects.filter(sodar_uuid=project_uuid).first(),
        }
        remote_project = RemoteProject(**values)
        remote_project.save()
        return remote_project


class RemoteTargetMixin(RemoteSiteMixin, RemoteProjectMixin):
    """Helper mixin for setting up the site as TARGET for testing"""

    @classmethod
    def set_up_as_target(cls, projects):
        """Set up current site as a target site"""
        source_site = cls.make_site(
            name='Test Source',
            url='http://0.0.0.0',
            mode=SITE_MODE_SOURCE,
            description='',
            secret=build_secret(),
        )
        remote_projects = []
        for project in projects:
            remote_projects.append(
                cls.make_remote_project(
                    project_uuid=project.sodar_uuid,
                    project=project,
                    site=source_site,
                    level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
                )
            )
        return source_site, remote_projects


class SODARUserMixin:
    """Helper mixin for LDAP SodarUser creation"""

    def make_sodar_user(
        self,
        username,
        name,
        first_name,
        last_name,
        email=None,
        sodar_uuid=None,
        password='password',
    ):
        user = self.make_user(username, password)
        user.name = name
        user.first_name = first_name
        user.last_name = last_name
        if email:
            user.email = email
        if sodar_uuid:
            user.sodar_uuid = sodar_uuid
        user.save()
        return user


class TestProject(ProjectMixin, RoleMixin, RoleAssignmentMixin, TestCase):
    """Tests for model.Project"""

    def setUp(self):
        # Set up category and project
        self.category = self.make_project(
            title='TestCategory', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        self.project = self.make_project(
            title='TestProject',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
        )
        # Init roles
        self.init_roles()
        # Init users
        self.user_alice = self.make_user('alice')
        self.user_bob = self.make_user('bob')
        self.user_carol = self.make_user('carol')
        self.user_dan = self.make_user('dan')
        self.user_erin = self.make_user('erin')
        self.user_frank = self.make_user('frank')
        # Init assignment
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_alice, self.role_owner
        )

    def test_initialization(self):
        """Test Project initialization"""
        expected = {
            'id': self.project.pk,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category.pk,
            'full_title': 'TestCategory / TestProject',
            'sodar_uuid': self.project.sodar_uuid,
            'description': '',
            'public_guest_access': False,
            'archive': False,
            'has_public_children': False,
        }
        model_dict = model_to_dict(self.project)
        # HACK: Can't compare markupfields like this. Better solution?
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

    def test__str__(self):
        """Test Project __str__()"""
        expected = 'TestCategory / TestProject'
        self.assertEqual(str(self.project), expected)

    def test__repr__(self):
        """Test Project __repr__()"""
        expected = "Project('TestProject', 'PROJECT', " "'TestCategory')"
        self.assertEqual(repr(self.project), expected)

    def test_validate_parent(self):
        """Test parent validation with self as parent"""
        with self.assertRaises(ValidationError):
            self.project.parent = self.project
            self.project.save()

    def test_validate_title_identical(self):
        """Test title validation with identical title"""
        with self.assertRaises(ValidationError):
            self.make_project(
                title='TestCategory',
                type=PROJECT_TYPE_PROJECT,
                parent=self.category,
            )

    def test_validate_title_delimiter(self):
        """Test title validation with category delimiter"""
        with self.assertRaises(ValidationError):
            self.make_project(
                title='Test{}PROJECT'.format(CAT_DELIMITER),
                type=PROJECT_TYPE_PROJECT,
                parent=self.category,
            )

    def test_validate_parent_type(self):
        """Test parent type validation with project under another project"""
        with self.assertRaises(ValidationError):
            self.make_project(
                title='FailProject',
                type=PROJECT_TYPE_PROJECT,
                parent=self.project,
            )

    def test_validate_public_guest_access(self):
        """Test public guest access validation with project"""
        # Test with project
        self.project.public_guest_access = True
        self.project.save()
        # Test with category
        with self.assertRaises(ValidationError):
            self.category.public_guest_access = True
            self.category.save()

    def test_get_absolute_url(self):
        """Test get_absolute_url()"""
        expected_url = reverse(
            'projectroles:detail',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.assertEqual(self.project.get_absolute_url(), expected_url)

    def test_get_children_category(self):
        """Test children getting function for top category"""
        children = self.category.get_children()
        self.assertEqual(children[0], self.project)

    def test_get_children_project(self):
        """Test children getting function for sub project"""
        children = self.project.get_children()
        self.assertEqual(children.count(), 0)

    def test_get_depth_category(self):
        """Test project depth getting function for top category"""
        self.assertEqual(self.category.get_depth(), 0)

    def test_get_depth_project(self):
        """Test children getting function for sub project"""
        self.assertEqual(self.project.get_depth(), 1)

    def test_get_parents_category(self):
        """Test get parents function for top category"""
        self.assertEqual(self.category.get_parents(), [])

    def test_get_parents_project(self):
        """Test get parents function for sub project"""
        self.assertEqual(list(self.project.get_parents()), [self.category])

    def test_is_remote(self):
        """Test Project.is_remote() without remote projects"""
        self.assertEqual(self.project.is_remote(), False)

    def test_is_revoked(self):
        """Test Project.is_revoked() without remote projects"""
        self.assertEqual(self.project.is_revoked(), False)

    def test_set_public(self):
        """Test Project.set_public()"""
        self.assertFalse(self.project.public_guest_access)
        self.project.set_public()  # Default = True
        self.assertTrue(self.project.public_guest_access)
        self.project.set_public(False)
        self.assertFalse(self.project.public_guest_access)
        self.project.set_public(True)
        self.assertTrue(self.project.public_guest_access)

    def test_set_archive(self):
        """Test Project.set_archive()"""
        self.assertFalse(self.project.archive)
        self.project.set_archive()  # Default = True
        self.assertTrue(self.project.archive)
        self.project.set_archive(False)
        self.assertFalse(self.project.archive)
        self.project.set_archive(True)
        self.assertTrue(self.project.archive)

    def test_set_archive_category(self):
        """Test Project.set_archive() for a category (should fail)"""
        self.assertFalse(self.category.archive)
        with self.assertRaises(ValidationError):
            self.category.set_archive()

    def test_get_log_title(self):
        """Test Project.get_log_title()"""
        expected = '"{}" ({})'.format(
            self.project.title, self.project.sodar_uuid
        )
        self.assertEqual(self.project.get_log_title(), expected)
        expected = '"{}" ({})'.format(
            self.project.full_title, self.project.sodar_uuid
        )
        self.assertEqual(self.project.get_log_title(full_title=True), expected)

    def test_get_role(self):
        """Test get_role()"""
        project_as = self.make_assignment(
            self.project, self.user_bob, self.role_owner
        )
        self.assertEqual(self.project.get_role(self.user_bob), project_as)

    def test_get_role_inherit_only(self):
        """Test get_role() with only an inherited role"""
        self.assertEqual(
            self.project.get_role(self.user_alice), self.owner_as_cat
        )

    def test_get_role_inherit_equal(self):
        """Test get_role() with inherited role equal to local role"""
        project_as = self.make_assignment(
            self.project, self.user_alice, self.role_owner
        )
        self.assertEqual(self.project.get_role(self.user_alice), project_as)

    def test_get_role_inherit_higher(self):
        """Test get_role() with inherited role higher than local role"""
        cat_as = self.make_assignment(
            self.category, self.user_bob, self.role_contributor
        )
        self.make_assignment(self.project, self.user_bob, self.role_guest)
        self.assertEqual(self.project.get_role(self.user_bob), cat_as)

    def test_get_role_inherit_lower(self):
        """Test get_role() with inherited role lower than local role"""
        self.make_assignment(self.category, self.user_bob, self.role_guest)
        project_as = self.make_assignment(
            self.project, self.user_bob, self.role_contributor
        )
        self.assertEqual(self.project.get_role(self.user_bob), project_as)

    def test_get_role_set_inherited_only(self):
        """Test get_role() with inherited_only=True"""
        self.make_assignment(self.project, self.user_alice, self.role_owner)
        self.assertEqual(
            self.project.get_role(self.user_alice, inherited_only=True),
            self.owner_as_cat,
        )

    def test_get_roles(self):
        """Test get_roles()"""
        project_as = self.make_assignment(
            self.project, self.user_bob, self.role_owner
        )
        roles = self.project.get_roles()
        self.assertEqual(len(roles), 2)  # Includes inherited category owner
        self.assertEqual(roles, [project_as, self.owner_as_cat])

    def test_get_roles_no_inherited(self):
        """Test get_roles() excluding inherited roles"""
        project_as = self.make_assignment(
            self.project, self.user_bob, self.role_owner
        )
        roles = self.project.get_roles(inherited=False)
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0], project_as)

    def test_get_roles_rank(self):
        """Test get_roles() with rank limits"""
        contrib_as = self.make_assignment(
            self.project, self.user_bob, self.role_contributor
        )
        guest_as = self.make_assignment(
            self.project, self.user_carol, self.role_guest
        )
        roles = self.project.get_roles()
        self.assertIn(contrib_as, roles)
        self.assertIn(guest_as, roles)
        roles = self.project.get_roles(max_rank=30)
        self.assertEqual(roles, [contrib_as, self.owner_as_cat])
        roles = self.project.get_roles(max_rank=40)
        self.assertEqual(roles, [contrib_as, guest_as, self.owner_as_cat])
        roles = self.project.get_roles(min_rank=30)
        self.assertEqual(roles, [contrib_as, guest_as])
        roles = self.project.get_roles(min_rank=40)
        self.assertEqual(roles, [guest_as])
        roles = self.project.get_roles(min_rank=30, max_rank=30)
        self.assertEqual(roles, [contrib_as])

    def test_get_roles_rank_override(self):
        """Test get_roles() with min_rank and role override"""
        self.make_assignment(
            self.category, self.user_bob, self.role_contributor
        )
        self.make_assignment(self.project, self.user_bob, self.role_guest)
        roles = self.project.get_roles(min_rank=40)
        # Neither assignment should be returned as the guest role is overridden
        self.assertEqual(roles, [])

    def test_get_roles_user(self):
        """Test get_roles() with user limit"""
        contrib_as = self.make_assignment(
            self.project, self.user_bob, self.role_contributor
        )
        guest_as = self.make_assignment(
            self.project, self.user_carol, self.role_guest
        )
        roles = self.project.get_roles()
        self.assertIn(contrib_as, roles)
        self.assertIn(guest_as, roles)
        roles = self.project.get_roles(user=self.user_carol)
        self.assertNotIn(contrib_as, roles)
        self.assertIn(guest_as, roles)

    def test_get_roles_by_rank(self):
        """Test get_roles_by_rank()"""
        owner_as = self.make_assignment(
            self.project, self.user_bob, self.role_owner
        )
        contrib_as = self.make_assignment(
            self.project, self.user_carol, self.role_contributor
        )
        contrib_as2 = self.make_assignment(
            self.project, self.user_dan, self.role_contributor
        )
        self.assertEqual(
            self.project.get_roles_by_rank(
                role_name=PROJECT_ROLE_OWNER, inherited=False
            ),
            [owner_as],
        )
        self.assertEqual(
            self.project.get_roles_by_rank(
                role_name=PROJECT_ROLE_OWNER, inherited=True
            ),
            [owner_as, self.owner_as_cat],
        )
        self.assertEqual(
            self.project.get_roles_by_rank(
                role_name=PROJECT_ROLE_OWNER, inherited_only=True
            ),
            [self.owner_as_cat],
        )
        self.assertEqual(
            self.project.get_roles_by_rank(
                role_name=PROJECT_ROLE_CONTRIBUTOR,
            ),
            [contrib_as, contrib_as2],
        )

    def test_get_owner(self):
        """Test get_owner()"""
        self.assertEqual(self.category.get_owner().user, self.user_alice)

    def test_get_owners(self):
        """Test get_owners()"""
        owner_as = self.make_assignment(
            self.project, self.user_bob, self.role_owner
        )
        owners = self.project.get_owners()
        self.assertEqual(len(owners), 2)
        self.assertIn(self.owner_as_cat, owners)
        self.assertIn(owner_as, owners)
        self.assertEqual(
            self.project.get_owners(inherited_only=True), [self.owner_as_cat]
        )
        self.assertEqual(self.project.get_owners(inherited=False), [owner_as])

    def test_get_delegates(self):
        """Test get_delegates()"""
        delegate_as_cat = self.make_assignment(
            self.category, self.user_carol, self.role_delegate
        )
        delegate_as = self.make_assignment(
            self.project, self.user_dan, self.role_delegate
        )
        self.assertEqual(len(self.project.get_delegates()), 2)
        self.assertEqual(
            self.project.get_delegates(inherited_only=True), [delegate_as_cat]
        )
        self.assertEqual(
            self.project.get_delegates(inherited=False), [delegate_as]
        )
        # Test with inherited owner role
        delegate_as.user = self.user_alice
        delegate_as.save()
        self.assertNotIn(delegate_as, self.project.get_delegates())

    def test_get_members(self):
        """Test get_members()"""
        as_contrib = self.make_assignment(
            self.project, self.user_erin, self.role_contributor
        )
        as_contrib2 = self.make_assignment(
            self.project, self.user_frank, self.role_contributor
        )
        expected = [
            {
                'id': as_contrib.pk,
                'project': self.project.pk,
                'user': self.user_erin.pk,
                'role': self.role_contributor.pk,
                'sodar_uuid': as_contrib.sodar_uuid,
            },
            {
                'id': as_contrib2.pk,
                'project': self.project.pk,
                'user': self.user_frank.pk,
                'role': self.role_contributor.pk,
                'sodar_uuid': as_contrib2.sodar_uuid,
            },
        ]
        members = self.project.get_members()
        self.assertEqual(len(members), 2)
        for i in range(0, len(members)):
            self.assertEqual(model_to_dict(members[i]), expected[i])

    def test_is_owner(self):
        """Test is_owner()"""
        self.make_assignment(self.project, self.user_bob, self.role_owner)
        self.assertTrue(self.project.is_owner(self.user_bob))
        self.assertTrue(self.project.is_owner(self.user_alice))  # Inherited
        self.assertFalse(self.project.is_owner(self.user_carol))

    def test_is_owner_inherited_and_local(self):
        """Test is_owner() with inherited and local role on same user"""
        self.make_assignment(self.project, self.user_alice, self.role_owner)
        self.assertTrue(self.project.is_owner(self.user_alice))

    def test_is_delegate(self):
        """Test is_delegate()"""
        self.make_assignment(self.project, self.user_bob, self.role_delegate)
        self.make_assignment(self.category, self.user_carol, self.role_delegate)
        self.assertTrue(self.project.is_delegate(self.user_bob))
        self.assertFalse(self.project.is_delegate(self.user_alice))
        self.assertTrue(self.project.is_delegate(self.user_carol))  # Inherited

    def test_is_delegate_inherited_and_local(self):
        """Test is_delegate() with inherited and local role on same user"""
        self.make_assignment(self.category, self.user_bob, self.role_delegate)
        self.make_assignment(self.project, self.user_bob, self.role_delegate)
        self.assertTrue(self.project.is_delegate(self.user_bob))

    def test_is_owner_or_delegate(self):
        """Test is_owner_or_delegate()"""
        self.make_assignment(self.project, self.user_bob, self.role_owner)
        self.assertTrue(self.project.is_owner_or_delegate(self.user_bob))
        self.assertTrue(self.project.is_owner_or_delegate(self.user_alice))
        self.assertFalse(self.project.is_owner_or_delegate(self.user_carol))

    def test_has_role(self):
        """Test has_role() with a local role"""
        self.make_assignment(self.project, self.user_bob, self.role_contributor)
        self.assertFalse(self.category.has_role(self.user_bob))
        self.assertTrue(self.project.has_role(self.user_bob))

    def test_has_role_inherit(self):
        """Test has_role() for inherited roles"""
        self.make_assignment(self.category, self.user_bob, self.role_delegate)
        self.make_assignment(
            self.category, self.user_carol, self.role_contributor
        )
        self.make_assignment(self.category, self.user_dan, self.role_guest)
        self.assertTrue(self.project.has_role(self.user_alice))
        self.assertTrue(self.project.has_role(self.user_bob))
        self.assertTrue(self.project.has_role(self.user_carol))
        self.assertTrue(self.project.has_role(self.user_dan))

    def test_has_role_public(self):
        """Test has_role() in project with public guest access"""
        self.project.set_public()
        self.assertFalse(self.category.has_role(self.user_bob))
        self.assertTrue(self.project.has_role(self.user_bob))


class TestRole(RoleMixin, TestCase):
    """Tests for models.Role"""

    def setUp(self):
        self.init_roles()

    def test_initialization(self):
        """Test Role initialization"""
        expected = {
            'id': self.role_owner.pk,
            'name': PROJECT_ROLE_OWNER,
            'rank': 10,
            'project_types': [PROJECT_TYPE_CATEGORY, PROJECT_TYPE_PROJECT],
            'description': self.role_owner.description,
        }
        self.assertEqual(model_to_dict(self.role_owner), expected)

    def test_initialization_finder(self):
        """Test Role initialization for project finder"""
        expected = {
            'id': self.role_finder.pk,
            'name': PROJECT_ROLE_FINDER,
            'rank': 50,
            'project_types': [PROJECT_TYPE_CATEGORY],
            'description': self.role_finder.description,
        }
        self.assertEqual(model_to_dict(self.role_finder), expected)

    def test__str__(self):
        """Test Role __str__()"""
        expected = PROJECT_ROLE_OWNER
        self.assertEqual(str(self.role_owner), expected)

    def test__repr__(self):
        """Test Role __repr__()"""
        expected = "Role('{}')".format(PROJECT_ROLE_OWNER)
        self.assertEqual(repr(self.role_owner), expected)


class TestRoleAssignment(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, TestCase
):
    """Tests for model.RoleAssignment"""

    def setUp(self):
        # Set up category and project
        self.category = self.make_project(
            title='TestCategory', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        self.project = self.make_project(
            title='TestProject',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
        )
        # Init roles
        self.init_roles()
        # Init users
        self.user_alice = self.make_user('alice')
        self.user_bob = self.make_user('bob')
        self.user_carol = self.make_user('carol')
        # Init assignment
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_alice, self.role_owner
        )
        self.expected_default = {
            'id': self.owner_as_cat.pk,
            'project': self.category.pk,
            'user': self.user_alice.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.owner_as_cat.sodar_uuid,
        }

    def test_initialization(self):
        """Test RoleAssignment initialization"""
        self.assertEqual(
            model_to_dict(self.owner_as_cat), self.expected_default
        )

    def test_init_finder_category(self):
        """Test initializing project finder with category"""
        role_as = self.make_assignment(
            self.category, self.user_bob, self.role_finder
        )
        self.assertIsInstance(role_as, RoleAssignment)

    def test_init_finder_project(self):
        """Test initializing project finder with project (should fail)"""
        with self.assertRaises(ValidationError):
            self.make_assignment(self.project, self.user_bob, self.role_finder)

    def test__str__(self):
        """Test RoleAssignment __str__()"""
        expected = 'TestCategory: {}: alice'.format(PROJECT_ROLE_OWNER)
        self.assertEqual(str(self.owner_as_cat), expected)

    def test__repr__(self):
        """Test RoleAssignment __repr__()"""
        expected = "RoleAssignment('TestCategory', 'alice', '{}')".format(
            PROJECT_ROLE_OWNER
        )
        self.assertEqual(repr(self.owner_as_cat), expected)

    def test_validate_user(self):
        """Test adding more than one role for user in project (should fail)"""
        with self.assertRaises(ValidationError):
            self.make_assignment(
                self.category, self.user_alice, self.role_contributor
            )

    def test_validate_owner(self):
        """Test owner uniqueness validation"""
        with self.assertRaises(ValidationError):
            self.make_assignment(self.category, self.user_bob, self.role_owner)

    def test_validate_delegate_single(self):
        """Test delegate validation with reached limit"""
        self.make_assignment(self.project, self.user_bob, self.role_delegate)
        with self.assertRaises(ValidationError):
            self.make_assignment(
                self.project, self.user_carol, self.role_delegate
            )

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=0)
    def test_validate_delegate_no_limit(self):
        """Test delegate validation with zero as limit"""
        self.make_assignment(self.project, self.user_bob, self.role_delegate)
        try:
            self.make_assignment(
                self.project, self.user_carol, self.role_delegate
            )
        except ValidationError as e:
            self.fail(e)

    def test_validate_delegate_inherited(self):
        """Test delegate validation with inherited delegate"""
        self.make_assignment(self.category, self.user_bob, self.role_delegate)
        # Limit should not be reached
        delegate_as = self.make_assignment(
            self.project, self.user_carol, self.role_delegate
        )
        self.assertIsInstance(delegate_as, RoleAssignment)


class TestProjectInvite(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestCase
):
    """Tests for ProjectInvite"""

    def setUp(self):
        # Init project
        self.project = self.make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )
        # Init roles
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        self.role_delegate = Role.objects.get(name=PROJECT_ROLE_DELEGATE)
        self.role_contributor = Role.objects.get(name=PROJECT_ROLE_CONTRIBUTOR)
        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Init invite
        self.invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )

    def test_initialization(self):
        """Test ProjectInvite initialization"""
        expected = {
            'id': self.invite.pk,
            'email': 'test@example.com',
            'project': self.project.pk,
            'role': self.role_contributor.pk,
            'issuer': self.user.pk,
            'date_expire': self.invite.date_expire,
            'message': '',
            'secret': SECRET,
            'sodar_uuid': self.invite.sodar_uuid,
            'active': True,
        }
        self.assertEqual(model_to_dict(self.invite), expected)

    def test__str__(self):
        """Test ProjectInvite __str__()"""
        expected = (
            'TestProject: test@example.com (project contributor) ' '[ACTIVE]'
        )
        self.assertEqual(str(self.invite), expected)

    def test__repr__(self):
        """Test ProjectInvite __repr__()"""
        expected = (
            "ProjectInvite('TestProject', 'test@example.com', "
            "'project contributor', True)"
        )
        self.assertEqual(repr(self.invite), expected)


class TestProjectManager(ProjectMixin, RoleAssignmentMixin, TestCase):
    """Tests for ProjectManager"""

    def setUp(self):
        self.category_top = self.make_project(
            title='TestCategory',
            type=PROJECT_TYPE_CATEGORY,
            parent=None,
            description='XXX',
        )
        self.project = self.make_project(
            title='TestProject',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category_top,
            description='YYY',
        )

    def test_find_all(self):
        """Test find() with any project type"""
        result = Project.objects.find(['test'], project_type=None)
        self.assertEqual(len(result), 2)
        result = Project.objects.find(['ThisFails'], project_type=None)
        self.assertEqual(len(result), 0)

    def test_find_project(self):
        """Test find() with project_type=PROJECT"""
        result = Project.objects.find(
            ['test'], project_type=PROJECT_TYPE_PROJECT
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.project)

    def test_find_category(self):
        """Test find() with project_type=CATEGORY"""
        result = Project.objects.find(
            ['test'], project_type=PROJECT_TYPE_CATEGORY
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.category_top)

    def test_find_multi_one(self):
        """Test find() with one valid multi-term"""
        result = Project.objects.find(['project', 'ThisFails'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.project)

    def test_find_multi_two(self):
        """Test find() with two valid multi-terms"""
        result = Project.objects.find(['category', 'project'])
        self.assertEqual(len(result), 2)

    def test_find_description(self):
        """Test find() with search term for description"""
        result = Project.objects.find(['xxx'], project_type=None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.category_top)

    def test_find_description_multi_one(self):
        """Test find() with one valid multi-search term for description"""
        result = Project.objects.find(['xxx', 'ThisFails'], project_type=None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.category_top)

    def test_find_description_multi_two(self):
        """Test find() with two valid multi-search terms for description"""
        result = Project.objects.find(['xxx', 'yyy'], project_type=None)
        self.assertEqual(len(result), 2)

    def test_find_multi_fields(self):
        """Test find() with multiple terms for different fields"""
        result = Project.objects.find(['project', 'xxx'])
        self.assertEqual(len(result), 2)


class TestProjectSetting(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for model.AppSetting with user == None"""

    def setUp(self):
        # Init project
        self.project = self.make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )
        # Init role
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init test setting
        self.setting_str = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='str_setting',
            setting_type='STRING',
            value='test',
            project=self.project,
        )
        # Init integer setting
        self.setting_int = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='int_setting',
            setting_type='INTEGER',
            value=170,
            project=self.project,
        )
        # Init boolean setting
        self.setting_bool = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='bool_setting',
            setting_type='BOOLEAN',
            value=True,
            project=self.project,
        )
        # Init JSON setting
        self.setting_json = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='json_setting',
            setting_type='JSON',
            value=None,
            value_json={'Testing': 'good'},
            project=self.project,
        )

    def test_initialization(self):
        """Test AppSetting initialization"""
        expected = {
            'id': self.setting_str.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': self.project.pk,
            'name': 'str_setting',
            'type': 'STRING',
            'user': None,
            'value': 'test',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_str.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_str), expected)

    def test_initialization_integer(self):
        """Test initialization with integer value"""
        expected = {
            'id': self.setting_int.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': self.project.pk,
            'name': 'int_setting',
            'type': 'INTEGER',
            'user': None,
            'value': '170',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_int.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_int), expected)

    def test_initialization_json(self):
        """Test initialization with JSON value"""
        expected = {
            'id': self.setting_json.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': self.project.pk,
            'name': 'json_setting',
            'type': 'JSON',
            'user': None,
            'value': None,
            'value_json': {'Testing': 'good'},
            'user_modifiable': True,
            'sodar_uuid': self.setting_json.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_json), expected)

    def test__str__(self):
        """Test AppSetting __str__()"""
        expected = 'TestProject: {} / str_setting'.format(EXAMPLE_APP_NAME)
        self.assertEqual(str(self.setting_str), expected)

    def test__repr__(self):
        """Test AppSetting __repr__()"""
        expected = (
            "AppSetting('TestProject', None, '{}', 'str_setting')".format(
                EXAMPLE_APP_NAME
            )
        )
        self.assertEqual(repr(self.setting_str), expected)

    def test_get_value_str(self):
        """Test get_value() with type STRING"""
        val = self.setting_str.get_value()
        self.assertIsInstance(val, str)
        self.assertEqual(val, 'test')

    def test_get_value_int(self):
        """Test get_value() with type INTEGER"""
        val = self.setting_int.get_value()
        self.assertIsInstance(val, int)
        self.assertEqual(val, 170)

    def test_get_value_bool(self):
        """Test get_value() with type BOOLEAN"""
        val = self.setting_bool.get_value()
        self.assertIsInstance(val, bool)
        self.assertEqual(val, True)

    def test_get_value_json(self):
        """Test get_value() with type JSON"""
        val = self.setting_json.get_value()
        self.assertEqual(val, {'Testing': 'good'})


class TestUserSetting(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for AppSetting with USER scope"""

    def setUp(self):
        # Init user & role
        self.user = self.make_user('owner')
        # Init settings
        self.setting_str = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='str_setting',
            setting_type='STRING',
            value='test',
            user=self.user,
        )
        self.setting_int = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='int_setting',
            setting_type='INTEGER',
            value=170,
            user=self.user,
        )
        self.setting_bool = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='bool_setting',
            setting_type='BOOLEAN',
            value=True,
            user=self.user,
        )
        self.setting_json = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='json_setting',
            setting_type='JSON',
            value=None,
            value_json={'Testing': 'good'},
            user=self.user,
        )

    def test_initialization(self):
        """Test AppSetting initialization"""
        expected = {
            'id': self.setting_str.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': None,
            'name': 'str_setting',
            'type': 'STRING',
            'user': self.user.pk,
            'value': 'test',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_str.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_str), expected)

    def test_initialization_integer(self):
        """Test initialization with integer value"""
        expected = {
            'id': self.setting_int.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': None,
            'name': 'int_setting',
            'type': 'INTEGER',
            'user': self.user.pk,
            'value': '170',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': self.setting_int.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_int), expected)

    def test_initialization_json(self):
        """Test initialization with integer value"""
        expected = {
            'id': self.setting_json.pk,
            'app_plugin': get_app_plugin(EXAMPLE_APP_NAME).get_model().pk,
            'project': None,
            'name': 'json_setting',
            'type': 'JSON',
            'user': self.user.pk,
            'value': None,
            'value_json': {'Testing': 'good'},
            'user_modifiable': True,
            'sodar_uuid': self.setting_json.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.setting_json), expected)

    def test__str__(self):
        """Test AppSetting __str__()"""
        expected = 'owner: {} / str_setting'.format(EXAMPLE_APP_NAME)
        self.assertEqual(str(self.setting_str), expected)

    def test__repr__(self):
        """Test AppSetting __repr__()"""
        expected = "AppSetting(None, 'owner', '{}', 'str_setting')".format(
            EXAMPLE_APP_NAME
        )
        self.assertEqual(repr(self.setting_str), expected)

    def test_get_value_str(self):
        """Test get_value() with type STRING"""
        val = self.setting_str.get_value()
        self.assertIsInstance(val, str)
        self.assertEqual(val, 'test')

    def test_get_value_int(self):
        """Test get_value() with type INTEGER"""
        val = self.setting_int.get_value()
        self.assertIsInstance(val, int)
        self.assertEqual(val, 170)

    def test_get_value_bool(self):
        """Test get_value() with type BOOLEAN"""
        val = self.setting_bool.get_value()
        self.assertIsInstance(val, bool)
        self.assertEqual(val, True)

    def test_get_value_json(self):
        """Test get_value() with type BOOLEAN"""
        val = self.setting_json.get_value()
        self.assertEqual(val, {'Testing': 'good'})


class TestRemoteSite(
    ProjectMixin, RoleAssignmentMixin, RemoteSiteMixin, TestCase
):
    """Tests for model.RemoteSite"""

    def setUp(self):
        # Init project
        self.project = self.make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )
        # Init role
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Init remote site
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            description='',
            secret=REMOTE_SITE_SECRET,
            user_display=REMOTE_SITE_USER_DISPLAY,
        )

    def test_initialization(self):
        """Test RemoteSite initialization"""
        expected = {
            'id': self.site.pk,
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SODAR_CONSTANTS['SITE_MODE_TARGET'],
            'description': '',
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': self.site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        self.assertEqual(model_to_dict(self.site), expected)

    def test__str__(self):
        """Test RemoteSite __str__()"""
        expected = '{} ({})'.format(
            REMOTE_SITE_NAME, SODAR_CONSTANTS['SITE_MODE_TARGET']
        )
        self.assertEqual(str(self.site), expected)

    def test__repr__(self):
        """Test RemoteSite __repr__()"""
        expected = "RemoteSite('{}', '{}', '{}')".format(
            REMOTE_SITE_NAME,
            SODAR_CONSTANTS['SITE_MODE_TARGET'],
            REMOTE_SITE_URL,
        )
        self.assertEqual(repr(self.site), expected)

    def test_validate_mode(self):
        """Test _validate_mode() with an invalid mode (should fail)"""
        with self.assertRaises(ValidationError):
            self.make_site(
                name='New site',
                url='http://example.com',
                mode='uGaj9eicQueib1th',
            )


class TestRemoteProject(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    TestCase,
):
    """Tests for model.RemoteProject"""

    def setUp(self):
        # Init project
        self.project = self.make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )
        # Init role
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.user_alice = self.make_user('alice')
        self.user_bob = self.make_user('bob')
        # Init remote site
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL'],
            project=self.project,
        )

    def test_initialization(self):
        """Test RemoteProject initialization"""
        expected = {
            'id': self.remote_project.pk,
            'project_uuid': self.project.sodar_uuid,
            'project': self.project.pk,
            'site': self.site.pk,
            'level': SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL'],
            'date_access': None,
            'sodar_uuid': self.remote_project.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.remote_project), expected)

    def test__str__(self):
        """Test RemoteProject __str__()"""
        expected = '{}: {} ({})'.format(
            REMOTE_SITE_NAME, str(self.project.sodar_uuid), SITE_MODE_TARGET
        )
        self.assertEqual(str(self.remote_project), expected)

    def test__repr__(self):
        """Test RemoteProject __repr__()"""
        expected = "RemoteProject('{}', '{}', '{}')".format(
            REMOTE_SITE_NAME, str(self.project.sodar_uuid), SITE_MODE_TARGET
        )
        self.assertEqual(repr(self.remote_project), expected)

    def test_is_remote_source(self):
        """Test Project.is_remote() as source"""
        self.assertEqual(self.project.is_remote(), False)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_is_remote_target(self):
        """Test Project.is_remote() as target"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()
        self.assertEqual(self.project.is_remote(), True)

    def test_get_source_site(self):
        """Test Project.get_source_site() as source"""
        self.assertEqual(self.project.get_source_site(), None)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_source_site_target(self):
        """Test Project.get_source_site() as target"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()
        self.assertEqual(self.project.get_source_site(), self.site)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_is_revoked_target(self):
        """Test Project.is_revoked() as target"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()
        self.assertEqual(self.project.is_revoked(), False)
        self.remote_project.level = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']
        self.remote_project.save()
        self.assertEqual(self.project.is_revoked(), True)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    @override_settings(PROJECTROLES_DELEGATE_LIMIT=1)
    def test_validate_remote_delegates(self):
        """Test delegate validation: can add for remote project with limit"""
        self.site.mode = SITE_MODE_SOURCE
        self.site.save()
        self.make_assignment(self.project, self.user_bob, self.role_delegate)
        try:
            self.make_assignment(
                self.project, self.user_alice, self.role_delegate
            )
        except ValidationError as e:
            self.fail(e)

    def test_get_project(self):
        """Test get_project() with project and project_uuid"""
        self.assertEqual(self.remote_project.get_project(), self.project)

    def test_get_project_no_foreign_key(self):
        """Test get_project() with no project foreign key"""
        self.remote_project.project = None
        self.remote_project.save()
        self.assertEqual(self.remote_project.get_project(), self.project)


class TestSODARUser(TestCase):
    """Tests for the SODARUser class"""

    def setUp(self):
        self.user = self.make_user()

    def test__str__(self):
        """Test __str__()"""
        self.assertEqual(
            self.user.__str__(), 'testuser'
        )  # This is the default username for self.make_user()

    def test_get_form_label(self):
        """Test get_form_label()"""
        self.assertEqual(self.user.get_form_label(), 'testuser')

    def test_get_form_label_email(self):
        """Test get_form_label() with email"""
        self.assertEqual(
            self.user.get_form_label(email=True),
            'testuser <testuser@example.com>',
        )

    def test_get_form_label_name(self):
        """Test get_form_label() with name"""
        self.user.name = 'Full Name'
        self.assertEqual(
            self.user.get_form_label(),
            'Full Name (testuser)',
        )

    def test_get_form_label_first_last(self):
        """Test get_form_label() with first and last name"""
        self.user.first_name = 'Full'
        self.user.last_name = 'Name'
        self.assertEqual(
            self.user.get_form_label(email=True),
            'Full Name (testuser) <testuser@example.com>',
        )

    def test_update_full_name(self):
        """Test update_full_name()"""
        self.assertEqual(self.user.name, '')
        self.user.first_name = 'Full'
        self.user.last_name = 'Name'
        self.user.update_full_name()
        self.assertEqual(self.user.name, 'Full Name')

    def test_update_ldap_username(self):
        """Test update_ldap_username()"""
        self.user.username = 'user@example'
        self.user.update_ldap_username()
        self.assertEqual(self.user.username, 'user@EXAMPLE')
