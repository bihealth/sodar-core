"""Ajax API view tests for the projectroles app"""

import json

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from test_plus.test import TestCase

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
from projectroles.utils import AppLinkContent


app_links = AppLinkContent()
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
                    'public_guest_access': self.category.public_guest_access,
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
                    'public_guest_access': self.project.public_guest_access,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'starred': False,
                    'access': True,
                    'finder_url': None,
                    'uuid': str(self.project.sodar_uuid),
                },
            ],
            'parent_depth': 0,
            'messages': {},
            'user': {'highlight': False, 'superuser': True},
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
                    'public_guest_access': self.project.public_guest_access,
                    'archive': False,
                    'remote': False,
                    'revoked': False,
                    'starred': False,
                    'access': True,
                    'finder_url': None,
                    'uuid': str(self.project.sodar_uuid),
                },
            ],
            'parent_depth': 1,
            'messages': {},
            'user': {'highlight': False, 'superuser': True},
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
        """Test project list for inherited owner"""
        with self.login(self.user_owner_cat):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['projects']), 2)

    def test_get_inherited_contrib(self):
        """Test project list for inherited contributor"""
        with self.login(self.user_contributor_cat):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['projects']), 2)

    def test_get_no_results(self):
        """Test project list with no results"""
        with self.login(self.user_no_roles):
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

    def test_get_finder(self):
        """Test project list with finder role"""
        user_finder = self.make_user('user_finder')
        self.make_assignment(self.category, user_finder, self.role_finder)
        with self.login(user_finder):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        res_data = response.data['projects']
        self.assertEqual(len(res_data), 2)
        self.assertEqual(res_data[0]['full_title'], self.category.full_title)
        self.assertEqual(res_data[0]['access'], True)
        self.assertEqual(res_data[0]['finder_url'], None)
        self.assertEqual(res_data[1]['full_title'], self.project.full_title)
        self.assertEqual(res_data[1]['access'], False)
        self.assertEqual(
            res_data[1]['finder_url'],
            reverse(
                'projectroles:roles',
                kwargs={'project': self.category.sodar_uuid},
            ),
        )

    def test_get_finder_parent(self):
        """Test project list with finder role inside parent"""
        user_finder = self.make_user('user_finder')
        self.make_assignment(self.category, user_finder, self.role_finder)
        with self.login(user_finder):
            response = self.client.get(
                self.url + '?parent=' + str(self.category.sodar_uuid),
            )
        self.assertEqual(response.status_code, 200)
        res_data = response.data['projects']
        self.assertEqual(len(res_data), 1)
        self.assertEqual(res_data[0]['full_title'], self.project.title)
        self.assertEqual(res_data[0]['access'], False)

    def test_get_finder_nested(self):
        """Test project list with finder role and nested access"""
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
        res_data = response.data['projects']
        self.assertEqual(len(res_data), 3)
        self.assertEqual(res_data[0]['full_title'], self.category.full_title)
        self.assertEqual(res_data[0]['access'], True)
        self.assertEqual(res_data[1]['full_title'], sub_cat.full_title)
        self.assertEqual(res_data[1]['access'], True)
        self.assertEqual(res_data[2]['full_title'], sub_project.full_title)
        self.assertEqual(res_data[2]['access'], False)

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
        res_data = response.data['projects']
        self.assertEqual(len(res_data), 4)
        self.assertEqual(res_data[0]['full_title'], self.category.full_title)
        self.assertEqual(res_data[0]['access'], True)
        self.assertEqual(res_data[1]['full_title'], self.project.full_title)
        self.assertEqual(res_data[1]['access'], True)
        self.assertEqual(res_data[2]['full_title'], branch_cat.full_title)
        self.assertEqual(res_data[2]['access'], True)
        self.assertEqual(res_data[3]['full_title'], branch_project.full_title)
        self.assertEqual(res_data[3]['access'], False)

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

    def test_get_public_guest_access(self):
        """Test GET with public guest access"""
        self.project.public_guest_access = True
        self.project.save()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['projects'][1]['public_guest_access'], True
        )


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
            str(self.category.sodar_uuid): {'name': 'Owner', 'class': None},
            str(self.project.sodar_uuid): {'name': 'Owner', 'class': None},
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


class TestProjectStarringAjaxView(
    ProjectMixin, RoleAssignmentMixin, ViewTestBase
):
    """Tests for ProjectStarringAjaxView"""

    def _assert_setting_count(self, count):
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

    def test_project_star(self):
        """Test Starring a Project"""
        self._assert_setting_count(0)
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:ajax_star',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self._assert_setting_count(1)
        star = app_settings.get(
            APP_NAME, 'project_star', self.project, self.user
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
            APP_NAME, 'project_star', self.project, self.user
        )
        self._assert_setting_count(1)
        self.assertEqual(star, False)


class TestRemoteProjectAccessAjaxView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    ViewTestBase,
):
    """Tests for RemoteProjectAccessAjaxView"""

    @classmethod
    def _get_query_string(cls, *args):
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
