"""Ajax API view tests for the projectroles app"""

import json

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from test_plus.test import TestCase

from projectroles.app_links import AppLinkAPI
from projectroles.app_settings import AppSettingAPI
from projectroles.models import AppSetting, SODAR_CONSTANTS
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
)
from projectroles.tests.test_views import (
    ViewTestBase,
    PROJECT_TYPE_CATEGORY,
    PROJECT_TYPE_PROJECT,
)
from projectroles.tests.test_views_api import SerializedObjectMixin


app_links = AppLinkAPI()
app_settings = AppSettingAPI()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']

# Local constants
APP_NAME = 'projectroles'
APP_NAME_FF = 'filesfolders'
INVALID_UUID = '11111111-1111-1111-1111-111111111111'


class TestProjectListAjaxView(ProjectMixin, RoleAssignmentMixin, ViewTestBase):
    """Tests for ProjectListAjaxView"""

    def setUp(self):
        super().setUp()
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_contributor_cat = self.make_user('user_contributor_cat')
        self.user_owner = self.make_user('user_owner')
        self.user_no_roles = self.make_user('user_no_roles')
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.cat_contributor_as = self.make_assignment(
            self.project, self.user_contributor_cat, self.role_contributor
        )
        self.url = reverse('projectroles:ajax_project_list')

    def test_get(self):
        """Test TestProjectListAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        expected = {
            'projects': [
                {
                    'type': self.category.type,
                    'full_title': self.category.full_title,
                    'public_access': False,
                    'public_stats': False,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'starred': False,
                    'access': True,
                    'finder_url': None,
                    'uuid': str(self.category.sodar_uuid),
                },
                {
                    'type': self.project.type,
                    'full_title': self.project.full_title,
                    'public_access': False,
                    'public_stats': False,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'blocked': False,
                    'starred': False,
                    'access': True,
                    'finder_url': None,
                    'uuid': str(self.project.sodar_uuid),
                },
            ],
            'parent_depth': 0,
            'messages': {},
            'user': {'highlight': True, 'superuser': True},
        }
        self.assertEqual(response.data, expected)

    def test_get_parent(self):
        """Test GET with parent project"""
        with self.login(self.user):
            response = self.client.get(
                self.url + '?parent=' + str(self.category.sodar_uuid),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'projects': [
                {
                    'type': self.project.type,
                    'full_title': self.project.title,  # Not full_title
                    'public_access': False,
                    'public_stats': False,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'blocked': False,
                    'starred': False,
                    'access': True,
                    'finder_url': None,
                    'uuid': str(self.project.sodar_uuid),
                },
            ],
            'parent_depth': 1,
            'messages': {},
            'user': {'highlight': True, 'superuser': True},
        }
        self.assertEqual(response.data, expected)

    def test_get_highlight(self):
        """Test GET with highlight app setting enabled"""
        app_settings.set(
            APP_NAME, 'project_list_highlight', True, user=self.user
        )
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['highlight'], True)

    def test_get_inherited_owner(self):
        """Test GET as inherited owner"""
        with self.login(self.user_owner_cat):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['projects']), 2)

    def test_get_inherited_contrib(self):
        """Test GET as inherited contributor"""
        with self.login(self.user_contributor_cat):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['projects']), 2)

    def test_get_no_roles(self):
        """Test project list as user with no roles"""
        with self.login(self.user_no_roles):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['projects'], [])
        self.assertIsNotNone(response.data['messages'].get('no_projects'))

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET as anonymous user"""
        # with self.login(self.user_no_roles):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['projects'], [])
        self.assertIsNotNone(response.data['messages'].get('no_projects'))

    def test_get_project_parent(self):
        """Test project list with project as parent (should fail)"""
        with self.login(self.user):
            response = self.client.get(
                self.url + '?parent=' + str(self.project.sodar_uuid),
            )
        self.assertEqual(response.status_code, 400)

    def test_get_block_owner(self):
        """Test GET with project access block as owner"""
        app_settings.set(
            APP_NAME, 'project_access_block', True, project=self.project
        )
        with self.login(self.user_owner):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertNotIn('blocked', pd[0])
        self.assertEqual(pd[1]['blocked'], True)
        self.assertEqual(pd[1]['access'], False)

    def test_get_block_superuser(self):
        """Test GET with project access block as superuser"""
        app_settings.set(
            APP_NAME, 'project_access_block', True, project=self.project
        )
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertNotIn('blocked', pd[0])
        self.assertEqual(pd[1]['blocked'], True)
        self.assertEqual(pd[1]['access'], True)

    def test_get_finder(self):
        """Test GET with finder role"""
        user_finder = self.make_user('user_finder')
        self.make_assignment(self.category, user_finder, self.role_finder)
        with self.login(user_finder):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 2)
        self.assertEqual(pd[0]['full_title'], self.category.full_title)
        self.assertEqual(pd[0]['access'], True)
        self.assertEqual(pd[0]['finder_url'], None)
        self.assertEqual(pd[1]['full_title'], self.project.full_title)
        self.assertEqual(pd[1]['access'], False)
        self.assertEqual(
            pd[1]['finder_url'],
            reverse(
                'projectroles:roles',
                kwargs={'project': self.category.sodar_uuid},
            ),
        )

    def test_get_finder_parent(self):
        """Test GET with finder role inside parent"""
        user_finder = self.make_user('user_finder')
        self.make_assignment(self.category, user_finder, self.role_finder)
        with self.login(user_finder):
            response = self.client.get(
                self.url + '?parent=' + str(self.category.sodar_uuid),
            )
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 1)
        self.assertEqual(pd[0]['full_title'], self.project.title)
        self.assertEqual(pd[0]['access'], False)

    def test_get_finder_nested(self):
        """Test GET with finder role and nested access"""
        sub_cat = self.make_project(
            'SubCategory', PROJECT_TYPE_CATEGORY, self.category
        )
        self.make_assignment(sub_cat, self.user_owner, self.role_owner)
        sub_project = self.make_project(
            'SubProject', PROJECT_TYPE_PROJECT, sub_cat
        )
        self.make_assignment(sub_project, self.user_owner, self.role_owner)
        user_finder = self.make_user('user_finder')
        self.make_assignment(sub_cat, user_finder, self.role_finder)
        with self.login(user_finder):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 3)
        self.assertEqual(pd[0]['full_title'], self.category.full_title)
        self.assertEqual(pd[0]['access'], True)
        self.assertEqual(pd[1]['full_title'], sub_cat.full_title)
        self.assertEqual(pd[1]['access'], True)
        self.assertEqual(pd[2]['full_title'], sub_project.full_title)
        self.assertEqual(pd[2]['access'], False)

    def test_get_finder_other_branch(self):
        """Test project list with finder role in another branch"""
        # Give regular access to self.project
        user_finder = self.make_user('user_finder')
        self.make_assignment(self.project, user_finder, self.role_guest)
        branch_cat = self.make_project(
            'TextCategory2', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(branch_cat, self.user_owner, self.role_owner)
        branch_project = self.make_project(
            'BranchProject', PROJECT_TYPE_PROJECT, branch_cat
        )
        self.make_assignment(branch_project, self.user_owner, self.role_owner)
        self.make_assignment(branch_cat, user_finder, self.role_finder)
        with self.login(user_finder):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 4)
        self.assertEqual(pd[0]['full_title'], self.category.full_title)
        self.assertEqual(pd[0]['access'], True)
        self.assertEqual(pd[1]['full_title'], self.project.full_title)
        self.assertEqual(pd[1]['access'], True)
        self.assertEqual(pd[2]['full_title'], branch_cat.full_title)
        self.assertEqual(pd[2]['access'], True)
        self.assertEqual(pd[3]['full_title'], branch_project.full_title)
        self.assertEqual(pd[3]['access'], False)

    def test_get_starred(self):
        """Test GET with starred project"""
        app_settings.set(
            APP_NAME, 'project_star', True, project=self.project, user=self.user
        )
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['projects'][1]['starred'], True)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive(True)
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['projects'][1]['archive'], True)

    def test_get_public_access(self):
        """Test GET with public read-only access"""
        self.project.public_access = self.role_guest
        self.project.save()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 2)
        self.assertEqual(pd[1]['public_access'], True)
        self.assertEqual(pd[1]['access'], True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_public_access_anon(self):
        """Test GET with public read-only access and anonymous user"""
        self.project.public_access = self.role_guest
        self.project.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 2)
        self.assertEqual(pd[1]['public_access'], True)
        self.assertEqual(pd[1]['access'], True)

    def test_get_category_public_stats(self):
        """Test GET with category public stats"""
        app_settings.set(
            APP_NAME, 'category_public_stats', True, project=self.category
        )
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 2)
        self.assertEqual(pd[0]['full_title'], self.category.full_title)
        self.assertEqual(pd[0]['access'], True)
        self.assertEqual(pd[0]['public_access'], False)
        self.assertEqual(pd[0]['public_stats'], True)

    def test_get_category_public_stats_no_roles(self):
        """Test GET with category public stats as user with no roles"""
        app_settings.set(
            APP_NAME, 'category_public_stats', True, project=self.category
        )
        with self.login(self.user_no_roles):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 1)
        self.assertEqual(pd[0]['full_title'], self.category.full_title)
        self.assertEqual(pd[0]['access'], True)
        self.assertEqual(pd[0]['public_stats'], True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category public stats as anonymous user"""
        app_settings.set(
            APP_NAME, 'category_public_stats', True, project=self.category
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        pd = response.data['projects']
        self.assertEqual(len(pd), 1)
        self.assertEqual(pd[0]['full_title'], self.category.full_title)
        self.assertEqual(pd[0]['access'], True)
        self.assertEqual(pd[0]['public_stats'], True)


class TestProjectListColumnAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
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
                APP_NAME_FF: {'files': {'html': '0'}, 'links': {'html': '0'}}
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
                APP_NAME_FF: {'files': {'html': '0'}, 'links': {'html': '0'}}
            }
        }
        self.assertEqual(response.data, expected)


class TestProjectListRoleAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
):
    """Tests for ProjectListRoleAjaxView"""

    def setUp(self):
        super().setUp()
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_owner = self.make_user('user_owner')
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )

    def test_post_category_owner(self):
        """Test POST for role retrieval as category owner"""
        with self.login(self.user_owner_cat):
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
            str(self.category.sodar_uuid): {'name': 'Owner', 'class': None},
            str(self.project.sodar_uuid): {'name': 'Owner', 'class': None},
        }
        self.assertEqual(response.data, expected)

    def test_post_project_owner(self):
        """Test POST for role retrieval as project owner"""
        with self.login(self.user_owner):
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
            },
            str(self.project.sodar_uuid): {'name': 'Owner', 'class': None},
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


class TestCategoryStatisticsAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
):
    """Tests for CategoryStatisticsAjaxView"""

    def setUp(self):
        super().setUp()
        self.user_owner = self.make_user('user_owner')
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )

    def test_get(self):
        """Test CategoryStatisticsAjaxView GET"""
        with self.login(self.user_owner):
            response = self.client.get(
                reverse(
                    'projectroles:ajax_stats_category',
                    kwargs={'project': self.category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        expected = [
            {
                'title': 'Projects',
                'value': 1,
                'unit': None,
                'description': 'Projects in this category',
                'icon': 'mdi:cube',
            },
            {
                'title': 'Members',
                'value': 1,
                'unit': None,
                'description': 'Users with roles in this category',
                'icon': 'mdi:account-multiple',
            },
            {
                'title': 'Files',
                'value': 0,
                'unit': None,
                'description': 'Files uploaded to projects in this category',
                'icon': 'mdi:file',
            },
        ]
        self.assertEqual(response.data['stats'], expected)

    def test_get_project(self):
        """Test GET with project (should fail)"""
        with self.login(self.user_owner):
            response = self.client.get(
                reverse(
                    'projectroles:ajax_stats_category',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 403)

    def test_get_subcategory(self):
        """Test GET with subcategory"""
        new_category = self.make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, self.category
        )
        self.make_assignment(new_category, self.user_owner, self.role_owner)
        with self.login(self.user_owner):
            response = self.client.get(
                reverse(
                    'projectroles:ajax_stats_category',
                    kwargs={'project': new_category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['stats'][0]['value'], 0)
        self.assertEqual(response.data['stats'][1]['value'], 1)  # User exists
        self.assertEqual(response.data['stats'][2]['value'], 0)


class TestProjectStarringAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
):
    """Tests for ProjectStarringAjaxView"""

    def _assert_setting_count(self, count: int):
        qs = AppSetting.objects.filter(
            app_plugin=None, project=self.project, name='project_star'
        )
        self.assertEqual(qs.count(), count)

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_post(self):
        """Test ProjectStarringAjaxView POST"""
        self._assert_setting_count(0)
        with self.login(self.user):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self._assert_setting_count(1)
        self.assertEqual(
            app_settings.get(APP_NAME, 'project_star', self.project, self.user),
            True,
        )

    def test_post_update(self):
        """Test POST to update existing value"""
        app_settings.set(
            APP_NAME, 'project_star', True, self.project, self.user
        )
        self._assert_setting_count(1)
        self.assertEqual(
            app_settings.get(APP_NAME, 'project_star', self.project, self.user),
            True,
        )
        with self.login(self.user):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self._assert_setting_count(1)
        self.assertEqual(
            app_settings.get(APP_NAME, 'project_star', self.project, self.user),
            False,
        )


class TestHomeStarringAjaxView(ViewTestBase):
    """Tests for HomeStarringAjaxView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:ajax_star_home')

    def test_post(self):
        """Test HomeStarringAjaxView POST"""
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user
            ),
            False,
        )
        with self.login(self.user):
            response = self.client.post(self.url, data={'value': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user
            ),
            True,
        )

    def test_post_update(self):
        """Test POST to update existing value"""
        app_settings.set(
            APP_NAME, 'project_list_home_starred', True, user=self.user
        )
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user
            ),
            True,
        )
        with self.login(self.user):
            response = self.client.post(self.url, data={'value': '0'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user
            ),
            False,
        )

    def test_post_value_unchanged(self):
        """Test POST with unchanged value"""
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user
            ),
            False,
        )
        with self.login(self.user):
            response = self.client.post(self.url, data={'value': '0'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user
            ),
            False,
        )


class TestRemoteProjectAccessAjaxView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    ViewTestBase,
):
    """Tests for RemoteProjectAccessAjaxView"""

    @classmethod
    def _get_query_string(cls, *args) -> str:
        """Get query string for GET requests"""
        return '?' + '&'.join(['rp={}'.format(rp.sodar_uuid) for rp in args])

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
        self.remote_site = self.make_site(
            name='RemoteSite',
            url='https://remote.site',
            mode=SITE_MODE_TARGET,
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self.rp_uuid = str(self.remote_project.sodar_uuid)
        self.remote_site2 = self.make_site(
            name='RemoteSite2',
            url='https://remote.site2',
            mode=SITE_MODE_TARGET,
        )
        self.remote_project2 = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site2,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self.rp_uuid2 = str(self.remote_project2.sodar_uuid)
        self.query_string = self._get_query_string(
            self.remote_project, self.remote_project2
        )
        self.url = reverse(
            'projectroles:ajax_remote_access',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test RemoteProjectAccessAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(self.url + self.query_string)
        self.assertEqual(response.status_code, 200)
        expected = {self.rp_uuid: False, self.rp_uuid2: False}
        self.assertEqual(response.data, expected)

    def test_get_accessed(self):
        """Test GET with one remote project accessed"""
        self.remote_project.date_access = timezone.now()
        self.remote_project.save()
        with self.login(self.user):
            response = self.client.get(self.url + self.query_string)
        self.assertEqual(response.status_code, 200)
        expected = {self.rp_uuid: True, self.rp_uuid2: False}
        self.assertEqual(response.data, expected)

    def test_get_accessed_multiple(self):
        """Test GET with multiple remote projects accessed"""
        self.remote_project.date_access = timezone.now()
        self.remote_project.save()
        self.remote_project2.date_access = timezone.now()
        self.remote_project2.save()
        with self.login(self.user):
            response = self.client.get(self.url + self.query_string)
        self.assertEqual(response.status_code, 200)
        expected = {self.rp_uuid: True, self.rp_uuid2: True}
        self.assertEqual(response.data, expected)

    def test_get_wrong_project(self):
        """Test GET with remote project for a different project"""
        new_project = self.make_project(
            'NewProject', PROJECT_TYPE_PROJECT, self.category
        )
        new_rp = self.make_remote_project(
            new_project.sodar_uuid,
            self.remote_site,
            REMOTE_LEVEL_READ_ROLES,
            project=new_project,
        )
        with self.login(self.user):
            response = self.client.get(
                self.url + self._get_query_string(new_rp)
            )
        self.assertEqual(response.status_code, 400)

    def test_get_invalid_uuid(self):
        """Test GET with invalid remote project UUID"""
        with self.login(self.user):
            response = self.client.get(self.url + '?rp=' + INVALID_UUID)
        self.assertEqual(response.status_code, 404)


class TestSidebarContentAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
):
    """Tests for SidebarContentAjaxView"""

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
        """Test SidebarContentAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:ajax_sidebar',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'links': app_links.get_project_links(self.user, self.project)
        }
        self.assertEqual(response.json(), expected)

    def test_get_category(self):
        """Test GET with category"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:ajax_sidebar',
                    kwargs={'project': self.category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'links': app_links.get_project_links(self.user, self.category)
        }
        self.assertEqual(response.json(), expected)

    def test_get_app_link(self):
        """Test GET with app plugin link"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:ajax_sidebar',
                    kwargs={'project': self.project.sodar_uuid},
                )
                + '?app_name=filesfolders'
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'links': app_links.get_project_links(
                self.user, self.project, app_name=APP_NAME_FF
            )
        }
        self.assertEqual(response.json(), expected)

    def test_get_url_name(self):
        """Test GET with URL name"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:ajax_sidebar',
                    kwargs={'project': self.project.sodar_uuid},
                )
                + '?app_name=filesfolders&url_name=file_create'
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'links': app_links.get_project_links(
                self.user,
                self.project,
                app_name=APP_NAME_FF,
                url_name='file_create',
            )
        }
        self.assertEqual(response.json(), expected)


class TestSiteReadOnlySettingAjaxView(SerializedObjectMixin, TestCase):
    """Tests for SiteReadOnlySettingAjaxView"""

    def setUp(self):
        self.user = self.make_user('user')
        self.user.save()

    def test_get_disabled(self):
        """Test SiteReadOnlySettingAjaxView GET with read-only mode disabled"""
        self.assertFalse(app_settings.get(APP_NAME, 'site_read_only'))
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_settings_site_read_only')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'site_read_only': False})

    def test_get_enabled(self):
        """Test GET with read-only mode enabled"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_settings_site_read_only')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'site_read_only': True})


class TestUserDropdownContentAjaxView(ViewTestBase):
    """Tests for UserDropdownContentAjaxView"""

    def setUp(self):
        super().setUp()
        self.user = self.make_user('user')
        self.user.is_superuser = True
        self.user.save()
        self.reg_user = self.make_user('reg_user')

    def test_get(self):
        """Test UserDropdownContentAjaxView GET as regular user"""
        with self.login(self.reg_user):
            response = self.client.get(
                reverse('projectroles:ajax_user_dropdown')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {'links': app_links.get_user_links(self.reg_user)}
        )

    def test_get_superuser(self):
        """Test GET as superuser"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_user_dropdown')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {'links': app_links.get_user_links(self.user)}
        )

    def test_get_app_name(self):
        """Test GET with app plugin name"""
        with self.login(self.reg_user):
            response = self.client.get(
                reverse('projectroles:ajax_user_dropdown') + '?app_name=tokens'
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'links': app_links.get_user_links(
                    self.reg_user, app_name='tokens'
                )
            },
        )

    def test_get_url_name(self):
        """Test GET with URL name"""
        with self.login(self.reg_user):
            response = self.client.get(
                reverse('projectroles:ajax_user_dropdown')
                + '?app_name=tokens&url_name=create'
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'links': app_links.get_user_links(
                    self.reg_user, app_name='tokens', url_name='create'
                )
            },
        )


class TestCurrentUserRetrieveAjaxView(SerializedObjectMixin, TestCase):
    """Tests for CurrentUserRetrieveAjaxView"""

    def setUp(self):
        self.user = self.make_user('user')
        self.user.is_superuser = True
        self.user.save()
        self.reg_user = self.make_user('reg_user')

    def test_get_regular_user(self):
        """Test CurrentUserRetrieveAjaxView GET with regular user"""
        with self.login(self.reg_user):
            response = self.client.get(
                reverse('projectroles:ajax_user_current')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.get_serialized_user(self.reg_user))

    def test_get_superuser(self):
        """Test GET with superuser"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_user_current')
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.get_serialized_user(self.user))


class TestUserAutocompleteAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
):
    """Tests for UserAutocompleteAjaxView"""

    def _get_forward_qs(self, data: dict) -> str:
        """Return forward querystring for UserAutocompleteAjaxView requests"""
        return '?forward=' + json.dumps(data)

    def setUp(self):
        super().setUp()
        self.user_owner = self.make_user('user_owner')
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.user_no_roles = self.make_user('user_no_roles')
        self.url = reverse('projectroles:ajax_autocomplete_user')

    def test_get(self):
        """Test UserAutocompleteAjaxView GET with default params"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 3)

    def test_get_project(self):
        """Test GET with project scope"""
        data = {
            'project': str(self.project.sodar_uuid),
            'scope': 'project',
        }
        with self.login(self.user):
            response = self.client.get(self.url + self._get_forward_qs(data))
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], str(self.user_owner.sodar_uuid))

    def test_get_project_exclude(self):
        """Test GET with project_exclude scope"""
        data = {
            'project': str(self.project.sodar_uuid),
            'scope': 'project_exclude',
        }
        with self.login(self.user):
            response = self.client.get(self.url + self._get_forward_qs(data))
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertNotIn(
            str(self.user_owner.sodar_uuid), [r['id'] for r in results]
        )

    def test_get_inactive_user(self):
        """Test GET with inactive user"""
        self.user_owner.is_active = False
        self.user_owner.save()
        data = {
            'project': str(self.project.sodar_uuid),
            'scope': 'project',
        }
        with self.login(self.user):
            response = self.client.get(self.url + self._get_forward_qs(data))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 0)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_get_disallow_local(self):
        """Test GET with local users disallowed"""
        with self.login(self.user_owner):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 0)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_get_disallow_local_as_superuser(self):
        """Test GET with local users disallowed as superuser"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # For superuser, all users should be returned
        self.assertEqual(len(response.json()['results']), 3)

    def test_get_user_exclude(self):
        """Test GET with user excluding"""
        data = {
            'scope': 'all',
            'exclude': [str(self.user_owner.sodar_uuid)],
        }
        with self.login(self.user):
            response = self.client.get(self.url + self._get_forward_qs(data))
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        self.assertNotIn(
            str(self.user_owner.sodar_uuid), [r['id'] for r in results]
        )


class TestUserAutocompleteRedirectAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
):
    """Tests for UserAutocompleteRedirectAjaxView"""

    def setUp(self):
        super().setUp()
        self.user_owner = self.make_user('user_owner')
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.url = reverse('projectroles:ajax_autocomplete_user_redirect')

    def test_get(self):
        """Test TestUserAutocompleteRedirectAjaxView GET"""
        data = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example.com',
        }
        with self.login(self.user):
            response = self.client.get(self.url, data)
        self.assertEqual(response.status_code, 200)
        option_new = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example.com"',
            'create_id': True,
        }
        data = json.loads(response.content)
        self.assertIn(option_new, data['results'])

    def test_get_invalid_email(self):
        """Test GET with invalid email"""
        data = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example',
        }
        with self.login(self.user):
            response = self.client.get(self.url, data)
        self.assertEqual(response.status_code, 200)
        option_new = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example"',
            'create_id': True,
        }
        data = json.loads(response.content)
        self.assertNotIn(option_new, data['results'])

    def test_post_redirect_to_invite(self):
        """Test POST for redirecting to ProjectInviteCreateView"""
        data = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'text': 'test@example.com',
        }
        with self.login(self.user):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(
            data['redirect_url'],
            reverse(
                'projectroles:invite_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
