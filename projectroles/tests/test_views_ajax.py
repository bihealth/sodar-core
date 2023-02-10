"""Ajax API view tests for the projectroles app"""

import json

from django.test import override_settings
from django.urls import reverse

from test_plus.test import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
)
from projectroles.tests.test_views import (
    TestViewsBase,
    PROJECT_TYPE_CATEGORY,
    PROJECT_TYPE_PROJECT,
)
from projectroles.tests.test_views_api import SerializedObjectMixin
from projectroles.views_ajax import INHERITED_OWNER_INFO


app_settings = AppSettingAPI()


class TestProjectListAjaxView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for ProjectListAjaxView"""

    def setUp(self):
        super().setUp()
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_get(self):
        """Test project list retrieval"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_project_list'),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'projects': [
                {
                    'title': self.category.title,
                    'type': self.category.type,
                    'full_title': self.category.full_title,
                    'public_guest_access': self.category.public_guest_access,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'starred': False,
                    'depth': 0,
                    'uuid': str(self.category.sodar_uuid),
                },
                {
                    'title': self.project.title,
                    'type': self.project.type,
                    'full_title': self.project.full_title,
                    'public_guest_access': self.project.public_guest_access,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'starred': False,
                    'depth': 1,
                    'uuid': str(self.project.sodar_uuid),
                },
            ],
            'parent_depth': 0,
            'messages': {},
            'user': {'superuser': True},
        }
        self.assertEqual(response.data, expected)

    def test_get_parent(self):
        """Test project list retrieval with a parent project"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_project_list')
                + '?parent='
                + str(self.category.sodar_uuid),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'projects': [
                {
                    'title': self.project.title,
                    'type': self.project.type,
                    'full_title': self.project.title,  # Not full_title
                    'public_guest_access': self.project.public_guest_access,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'starred': False,
                    'depth': 1,
                    'uuid': str(self.project.sodar_uuid),
                },
            ],
            'parent_depth': 1,
            'messages': {},
            'user': {'superuser': True},
        }
        self.assertEqual(response.data, expected)

    def test_get_inherited_owner(self):
        """Test project list retrieval for inherited owner"""
        cat_owner = self.make_user('cat_owner')
        self.owner_as_cat.user = cat_owner
        self.owner_as_cat.save()
        pro_owner = self.make_user('pro_owner')
        self.owner_as.user = pro_owner
        self.owner_as.save()
        with self.login(cat_owner):
            response = self.client.get(
                reverse('projectroles:ajax_project_list'),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['projects']), 2)

    def test_get_no_results(self):
        """Test project list retrieval with no results"""
        new_user = self.make_user('new_user')  # User with no roles
        with self.login(new_user):
            response = self.client.get(
                reverse('projectroles:ajax_project_list'),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['projects'], [])
        self.assertIsNotNone(response.data['messages'].get('no_projects'))

    def test_get_project_parent(self):
        """Test project list retrieval with project as parent (should fail)"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_project_list')
                + '?parent='
                + str(self.project.sodar_uuid),
            )
        self.assertEqual(response.status_code, 400)


class TestProjectListColumnAjaxView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for ProjectListColumnAjaxView"""

    def setUp(self):
        super().setUp()
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_post(self):
        """Test POST for custom column retrieval"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_project_list_columns'),
                json.dumps({'projects': [str(self.project.sodar_uuid)]}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            str(self.project.sodar_uuid): {
                'filesfolders': {'files': {'html': '0'}, 'links': {'html': '0'}}
            }
        }
        self.assertEqual(response.data, expected)

    @override_settings(FILESFOLDERS_SHOW_LIST_COLUMNS=False)
    def test_post_no_columns(self):
        """Test POST with no custom colums"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_project_list_columns'),
                json.dumps({'projects': [str(self.project.sodar_uuid)]}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        expected = {str(self.project.sodar_uuid): {}}
        self.assertEqual(response.data, expected)

    def test_post_no_permission(self):
        """Test POST with no user permission on a project"""
        new_project = self.make_project(
            'NewProject', PROJECT_TYPE_PROJECT, None
        )
        new_user = self.make_user('new_user')
        self.make_assignment(new_project, new_user, self.role_owner)

        with self.login(new_user):
            response = self.client.post(
                reverse('projectroles:ajax_project_list_columns'),
                json.dumps(
                    {
                        'projects': [
                            str(self.project.sodar_uuid),
                            str(new_project.sodar_uuid),
                        ]
                    }
                ),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            str(new_project.sodar_uuid): {
                'filesfolders': {'files': {'html': '0'}, 'links': {'html': '0'}}
            }
        }
        self.assertEqual(response.data, expected)


class TestProjectListRoleAjaxView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for ProjectListRoleAjaxView"""

    def setUp(self):
        super().setUp()
        self.user_cat_owner = self.make_user('cat_owner')
        self.user_pro_owner = self.make_user('pro_owner')
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_cat_owner, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_pro_owner, self.role_owner
        )

    def test_post_category_owner(self):
        """Test POST for role retrieval as category owner"""
        with self.login(self.user_cat_owner):
            response = self.client.post(
                reverse('projectroles:ajax_project_list_roles'),
                json.dumps(
                    {
                        'projects': [
                            str(self.category.sodar_uuid),
                            str(self.project.sodar_uuid),
                        ]
                    }
                ),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            str(self.category.sodar_uuid): {
                'name': 'Owner',
                'class': None,
                'info': None,
            },
            str(self.project.sodar_uuid): {
                'name': 'Owner',
                'class': 'text-muted',
                'info': INHERITED_OWNER_INFO,
            },
        }
        self.assertEqual(response.data, expected)

    def test_post_project_owner(self):
        """Test POST for role retrieval as project owner"""
        with self.login(self.user_pro_owner):
            response = self.client.post(
                reverse('projectroles:ajax_project_list_roles'),
                json.dumps(
                    {
                        'projects': [
                            str(self.category.sodar_uuid),
                            str(self.project.sodar_uuid),
                        ]
                    }
                ),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            str(self.category.sodar_uuid): {
                'name': 'N/A',
                'class': 'text-muted',
                'info': None,
            },
            str(self.project.sodar_uuid): {
                'name': 'Owner',
                'class': None,
                'info': None,
            },
        }
        self.assertEqual(response.data, expected)

    def test_post_no_access(self):
        """Test POST for role retrieval with no access to project"""
        new_user = self.make_user('new_user')  # User with no roles
        with self.login(new_user):
            response = self.client.post(
                reverse('projectroles:ajax_project_list_roles'),
                json.dumps(
                    {
                        'projects': [
                            str(self.category.sodar_uuid),
                            str(self.project.sodar_uuid),
                        ]
                    }
                ),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {})


class TestProjectStarringAjaxView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for ProjectStarringAjaxView"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_project_star(self):
        """Test Starring a Project"""
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:ajax_star',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        star = app_settings.get(
            'projectroles', 'project_star', self.project, self.user
        )
        self.assertEqual(star, True)

        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:ajax_star',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        star = app_settings.get(
            'projectroles', 'project_star', self.project, self.user
        )
        self.assertEqual(star, False)


class TestCurrentUserRetrieveAjaxView(SerializedObjectMixin, TestCase):
    """Tests for CurrentUserRetrieveAjaxView"""

    def setUp(self):
        self.user = self.make_user('user')
        self.user.is_superuser = True
        self.user.save()
        self.reg_user = self.make_user('reg_user')

    def test_regular_user(self):
        """Test CurrentUserRetrieveAjaxView with regular user"""
        with self.login(self.reg_user):
            response = self.client.get(
                reverse('projectroles:ajax_user_current')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.get_serialized_user(self.reg_user))

    def test_superuser(self):
        """Test CurrentUserRetrieveAjaxView with superuser"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_user_current')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.get_serialized_user(self.user))
