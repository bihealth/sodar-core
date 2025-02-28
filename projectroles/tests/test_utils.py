"""Utils tests for the projectroles app"""

import re

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from django.urls import reverse

from test_plus import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin
from projectroles.tests.test_views import ViewTestBase
from projectroles.utils import (
    AppLinkContent,
    get_display_name,
    build_secret,
    get_app_names,
)


app_links = AppLinkContent()
app_settings = AppSettingAPI()


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']

# Local constants
APP_NAME = 'projectroles'
APP_NAME_FF = 'filesfolders'
CONSTANTS_OVERRIDE = {
    'DISPLAY_NAMES': {
        'CATEGORY': {'default': 'bar', 'plural': 'bars'},
        'PROJECT': {'default': 'foo', 'plural': 'foos'},
    }
}


class TestUtils(TestCase):
    """Tests for general utilities"""

    def test_get_display_name(self):
        """Test get_display_name()"""
        self.assertEqual(get_display_name(PROJECT_TYPE_PROJECT), 'project')
        self.assertEqual(
            get_display_name(PROJECT_TYPE_PROJECT, title=True), 'Project'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_PROJECT, count=3), 'projects'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_PROJECT, title=True, count=3),
            'Projects',
        )
        self.assertEqual(get_display_name(PROJECT_TYPE_CATEGORY), 'category')
        self.assertEqual(
            get_display_name(PROJECT_TYPE_CATEGORY, title=True), 'Category'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_CATEGORY, count=3), 'categories'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_CATEGORY, title=True, count=3),
            'Categories',
        )

    # TODO: Test with override

    def test_build_secret(self):
        """Test build_secret()"""
        secret = build_secret()
        self.assertEqual(re.match(r'[a-z\d]{32}', secret).string, secret)
        self.assertEqual(len(build_secret(16)), 16)

    @override_settings(PROJECTROLES_SECRET_LENGTH=16)
    def test_build_secret_override(self):
        """Test build_secret() with default length setting override"""
        self.assertEqual(len(build_secret()), 16)

    def test_get_app_names(self):
        """Test get_app_names()"""
        app_names = get_app_names()
        self.assertNotEqual(len(app_names), 0)
        self.assertFalse(any([a.startswith('django.') for a in app_names]))
        self.assertFalse(any(['.apps.' in a for a in app_names]))
        self.assertNotIn(settings.SITE_PACKAGE, app_names)


class TestAppLinkContent(ProjectMixin, RoleAssignmentMixin, ViewTestBase):
    """Tests for AppLinkContent"""

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

    def test_get_project_links(self):
        """Test get_project_links() with project"""
        kw = {'project': self.project.sodar_uuid}
        expected = [
            {
                'name': 'project-detail',
                'url': reverse('projectroles:detail', kwargs=kw),
                'label': 'Project Overview',
                'icon': 'mdi:cube',
                'active': False,
            },
            {
                'name': 'app-plugin-filesfolders',
                'url': reverse('filesfolders:list', kwargs=kw),
                'label': 'Files',
                'icon': 'mdi:file',
                'active': False,
            },
            {
                'name': 'app-plugin-timeline',
                'url': reverse('timeline:list_project', kwargs=kw),
                'label': 'Timeline',
                'icon': 'mdi:clock-time-eight',
                'active': False,
            },
            {
                'name': 'app-plugin-bgjobs',
                'url': reverse('bgjobs:list', kwargs=kw),
                'label': 'Background Jobs',
                'icon': 'mdi:server',
                'active': False,
            },
            {
                'name': 'app-plugin-example_project_app',
                'url': reverse('example_project_app:example', kwargs=kw),
                'label': 'Example Project App',
                'icon': 'mdi:rocket-launch',
                'active': False,
            },
            {
                'name': 'project-roles',
                'url': reverse('projectroles:roles', kwargs=kw),
                'label': 'Members',
                'icon': 'mdi:account-multiple',
                'active': False,
            },
            {
                'name': 'project-update',
                'url': reverse('projectroles:update', kwargs=kw),
                'label': 'Update Project',
                'icon': 'mdi:lead-pencil',
                'active': False,
            },
        ]
        self.assertEqual(
            app_links.get_project_links(self.user_owner, self.project), expected
        )

    def test_get_project_links_app_name(self):
        """Test get_project_links() with project and specific app plugin"""
        kw = {'project': self.project.sodar_uuid}
        expected = [
            {
                'name': 'project-detail',
                'url': reverse('projectroles:detail', kwargs=kw),
                'label': 'Project Overview',
                'icon': 'mdi:cube',
                'active': False,
            },
            {
                'name': 'app-plugin-filesfolders',
                'url': reverse('filesfolders:list', kwargs=kw),
                'label': 'Files',
                'icon': 'mdi:file',
                'active': True,  # This should be active
            },
            {
                'name': 'app-plugin-timeline',
                'url': reverse('timeline:list_project', kwargs=kw),
                'label': 'Timeline',
                'icon': 'mdi:clock-time-eight',
                'active': False,
            },
            {
                'name': 'app-plugin-bgjobs',
                'url': reverse('bgjobs:list', kwargs=kw),
                'label': 'Background Jobs',
                'icon': 'mdi:server',
                'active': False,
            },
            {
                'name': 'app-plugin-example_project_app',
                'url': reverse('example_project_app:example', kwargs=kw),
                'label': 'Example Project App',
                'icon': 'mdi:rocket-launch',
                'active': False,
            },
            {
                'name': 'project-roles',
                'url': reverse('projectroles:roles', kwargs=kw),
                'label': 'Members',
                'icon': 'mdi:account-multiple',
                'active': False,
            },
            {
                'name': 'project-update',
                'url': reverse('projectroles:update', kwargs=kw),
                'label': 'Update Project',
                'icon': 'mdi:lead-pencil',
                'active': False,
            },
        ]
        self.assertEqual(
            app_links.get_project_links(
                self.user_owner, self.project, app_name=APP_NAME_FF
            ),
            expected,
        )

    def test_get_project_links_category(self):
        """Test get_project_links() with category"""
        kw = {'project': self.category.sodar_uuid}
        expected = [
            {
                'name': 'project-detail',
                'url': reverse('projectroles:detail', kwargs=kw),
                'label': 'Category Overview',
                'icon': 'mdi:rhombus-split',
                'active': False,
            },
            {
                'name': 'app-plugin-timeline',
                'url': reverse('timeline:list_project', kwargs=kw),
                'label': 'Timeline',
                'icon': 'mdi:clock-time-eight',
                'active': False,
            },
            {
                'name': 'project-roles',
                'url': reverse('projectroles:roles', kwargs=kw),
                'label': 'Members',
                'icon': 'mdi:account-multiple',
                'active': False,
            },
            {
                'name': 'project-update',
                'url': reverse('projectroles:update', kwargs=kw),
                'label': 'Update Category',
                'icon': 'mdi:lead-pencil',
                'active': False,
            },
            {
                'name': 'project-create',
                'url': reverse('projectroles:create', kwargs=kw),
                'label': 'Create Project or Category',
                'icon': 'mdi:plus-thick',
                'active': False,
            },
        ]
        self.assertEqual(
            app_links.get_project_links(self.user_owner, self.category),
            expected,
        )

    def test_get_project_links_home_superuser(self):
        """Test get_project_links() with home URL as superuser"""
        expected = [
            {
                'name': 'home-project-create',
                'url': reverse('projectroles:create'),
                'label': 'Create Category',
                'icon': 'mdi:plus-thick',
                'active': False,
            },
        ]
        self.assertEqual(
            app_links.get_project_links(self.user, url_name='home'),
            expected,
        )

    def test_get_project_links_home_regular_user(self):
        """Test get_project_links() with home URL as regular user"""
        self.assertEqual(
            app_links.get_project_links(self.user_owner, url_name='home'), []
        )

    def test_get_project_links_url_name_projectroles(self):
        """Test get_project_links() with projectroles URL name"""
        links = app_links.get_project_links(
            self.user_owner,
            self.project,
            app_name=APP_NAME,
            url_name='roles',
        )
        self.assertEqual(len(links), 7)
        for i in range(0, 6):
            if i == 5:
                self.assertEqual(links[i]['name'], 'project-roles')
                self.assertEqual(links[i]['active'], True)
            else:
                self.assertEqual(links[i]['active'], False)

    def test_get_project_links_url_name_app_plugin(self):
        """Test get_project_links() with app plugin URL name"""
        links = app_links.get_project_links(
            self.user_owner,
            self.project,
            app_name=APP_NAME_FF,
            url_name='file_create',
        )
        self.assertEqual(len(links), 7)
        for i in range(0, 6):
            if i == 1:
                self.assertEqual(links[i]['name'], 'app-plugin-filesfolders')
                self.assertEqual(links[i]['active'], True)
            else:
                self.assertEqual(links[i]['active'], False)

    def test_get_project_links_contributor(self):
        """Test get_project_links() with project as contributor"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.project, user_new, self.role_contributor)
        links = app_links.get_project_links(user_new, self.project)
        self.assertEqual(len(links), 6)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-update', link_names)

    def test_get_project_links_guest(self):
        """Test get_project_links() with project as guest"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.project, user_new, self.role_guest)
        links = app_links.get_project_links(user_new, self.project)
        self.assertEqual(len(links), 6)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-update', link_names)

    def test_get_project_links_category_contributor(self):
        """Test get_project_links() with category as contributor"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.category, user_new, self.role_contributor)
        links = app_links.get_project_links(user_new, self.category)
        self.assertEqual(len(links), 4)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-update', link_names)  # NOTE: Can create

    def test_get_project_links_category_guest(self):
        """Test get_project_links() with category as guest"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.category, user_new, self.role_guest)
        links = app_links.get_project_links(user_new, self.category)
        self.assertEqual(len(links), 3)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-update', link_names)
        self.assertNotIn('project-create', link_names)

    @override_settings(PROJECTROLES_HIDE_PROJECT_APPS=[APP_NAME_FF])
    def test_get_project_links_hidden_app(self):
        """Test get_project_links() with hidden app"""
        links = app_links.get_project_links(self.user, self.project)
        self.assertEqual(len(links), 6)
        link_names = [link['name'] for link in links]
        self.assertNotIn('app-plugin-filesfolders', link_names)

    @override_settings(
        PROJECTROLES_SITE_MODE=SITE_MODE_TARGET,
        PROJECTROLES_TARGET_CREATE=False,
    )
    def test_get_project_links_category_target_disallow(self):
        """Test get_project_links() as target site with creation disallowed"""
        links = app_links.get_project_links(self.user_owner, self.category)
        self.assertEqual(len(links), 4)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-create', link_names)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_project_links_category_target_allow(self):
        """Test get_project_links() as target site with creation sallowed"""
        links = app_links.get_project_links(self.user_owner, self.category)
        self.assertEqual(len(links), 5)

    @override_settings(
        PROJECTROLES_SITE_MODE=SITE_MODE_TARGET,
        PROJECTROLES_TARGET_CREATE=False,
    )
    def test_get_project_links_category_target_disallow_superuser(self):
        """Test get_project_links() as superuser on target site with creation disallowed"""
        links = app_links.get_project_links(self.user, self.category)
        self.assertEqual(len(links), 4)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-create', link_names)

    def test_get_project_links_read_only(self):
        """Test get_project_links() with project and site read-only mode"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        links = app_links.get_project_links(self.user_owner, self.project)
        self.assertEqual(len(links), 6)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-update', link_names)

    def test_get_project_links_read_only_superuser(self):
        """Test get_project_links() with project and site read-only mode as superuser"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        links = app_links.get_project_links(self.user, self.project)
        self.assertEqual(len(links), 7)

    def test_get_project_links_category_read_only(self):
        """Test get_project_links() with category and site read-only mode"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        links = app_links.get_project_links(self.user_owner, self.category)
        self.assertEqual(len(links), 3)
        link_names = [link['name'] for link in links]
        self.assertNotIn('project-update', link_names)
        self.assertNotIn('project-create', link_names)

    def test_get_project_links_category_read_only_superuser(self):
        """Test get_project_links() with category and site read-only mode as superuser"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        links = app_links.get_project_links(self.user, self.category)
        self.assertEqual(len(links), 5)

    def test_get_user_links(self):
        """Test get_user_links() as regular user"""
        expected = [
            {
                'name': 'appalerts',
                'url': reverse('appalerts:list'),
                'label': 'App Alerts',
                'icon': 'mdi:alert-octagram',
                'active': False,
            },
            {
                'name': 'example_site_app',
                'url': reverse('example_site_app:example'),
                'label': 'Example Site App',
                'icon': 'mdi:rocket-launch-outline',
                'active': False,
            },
            {
                'name': 'timeline_site',
                'url': reverse('timeline:list_site'),
                'label': 'Site-Wide Events',
                'icon': 'mdi:clock-time-eight-outline',
                'active': False,
            },
            {
                'name': 'tokens',
                'url': reverse('tokens:list'),
                'label': 'API Tokens',
                'icon': 'mdi:key-chain-variant',
                'active': False,
            },
            {
                'name': 'userprofile',
                'url': reverse('userprofile:detail'),
                'label': 'User Profile',
                'icon': 'mdi:account-details',
                'active': False,
            },
            {
                'name': 'sign-out',
                'url': reverse('logout'),
                'label': 'Logout',
                'icon': 'mdi:logout-variant',
                'active': False,
            },
        ]
        self.assertEqual(app_links.get_user_links(self.user_owner), expected)

    def test_get_user_links_superuser(self):
        """Test get_user_links() as superuser"""
        expected = [
            {
                'name': 'adminalerts',
                'url': reverse('adminalerts:list'),
                'label': 'Admin Alerts',
                'icon': 'mdi:alert',
                'active': False,
            },
            {
                'name': 'appalerts',
                'url': reverse('appalerts:list'),
                'label': 'App Alerts',
                'icon': 'mdi:alert-octagram',
                'active': False,
            },
            {
                'name': 'bgjobs_site',
                'url': reverse('bgjobs:site_list'),
                'label': 'Site Background Jobs',
                'icon': 'mdi:server',
                'active': False,
            },
            {
                'name': 'example_site_app',
                'url': reverse('example_site_app:example'),
                'label': 'Example Site App',
                'icon': 'mdi:rocket-launch-outline',
                'active': False,
            },
            {
                'name': 'remotesites',
                'url': reverse('projectroles:remote_sites'),
                'label': 'Remote Site Access',
                'icon': 'mdi:cloud-sync',
                'active': False,
            },
            {
                'name': 'siteappsettings',
                'url': '/project/site-app-settings',
                'label': 'Site App Settings',
                'icon': 'mdi:cog-outline',
                'active': False,
            },
            {
                'name': 'siteinfo',
                'url': reverse('siteinfo:info'),
                'label': 'Site Info',
                'icon': 'mdi:bar-chart',
                'active': False,
            },
            {
                'name': 'timeline_site',
                'url': reverse('timeline:list_site'),
                'label': 'Site-Wide Events',
                'icon': 'mdi:clock-time-eight-outline',
                'active': False,
            },
            {
                'name': 'timeline_site_admin',
                'url': reverse('timeline:list_admin'),
                'label': 'All Timeline Events',
                'icon': 'mdi:web-clock',
                'active': False,
            },
            {
                'name': 'tokens',
                'url': reverse('tokens:list'),
                'label': 'API Tokens',
                'icon': 'mdi:key-chain-variant',
                'active': False,
            },
            {
                'name': 'userprofile',
                'url': reverse('userprofile:detail'),
                'label': 'User Profile',
                'icon': 'mdi:account-details',
                'active': False,
            },
            {
                'name': 'admin',
                'url': '/admin/',
                'label': 'Django Admin',
                'icon': 'mdi:cogs',
                'active': False,
            },
            {
                'name': 'sign-out',
                'url': reverse('logout'),
                'label': 'Logout',
                'icon': 'mdi:logout-variant',
                'active': False,
            },
        ]
        self.assertEqual(app_links.get_user_links(self.user), expected)

    def test_get_user_links_app_name(self):
        """Test get_user_links() with app plugin name"""
        links = app_links.get_user_links(self.user_owner, app_name='tokens')
        self.assertEqual(len(links), 6)
        for i in range(0, 5):
            if i == 3:
                self.assertEqual(links[i]['name'], 'tokens')
                self.assertEqual(links[i]['active'], True)
            else:
                self.assertEqual(links[i]['active'], False)

    def test_get_user_links_url_name(self):
        """Test get_user_links() with URL name"""
        links = app_links.get_user_links(
            self.user_owner, app_name='tokens', url_name='create'
        )
        self.assertEqual(len(links), 6)
        for i in range(0, 5):
            if i == 3:
                self.assertEqual(links[i]['name'], 'tokens')
                self.assertEqual(links[i]['active'], True)
            else:
                self.assertEqual(links[i]['active'], False)

    def test_get_user_links_url_name_remote(self):
        """Test get_user_links() with remote sites URL name"""
        links = app_links.get_user_links(
            self.user, app_name=APP_NAME, url_name='remote_site_create'
        )
        self.assertEqual(len(links), 13)
        for i in range(0, 13):
            if i == 4:
                self.assertEqual(links[i]['name'], 'remotesites')
                self.assertEqual(links[i]['active'], True)
            else:
                self.assertEqual(links[i]['active'], False)

    def test_get_user_links_url_name_site_app_settings(self):
        """Test get_user_links() with site app settings URL name"""
        links = app_links.get_user_links(
            self.user, app_name=APP_NAME, url_name='site_app_settings'
        )
        self.assertEqual(len(links), 13)
        for i in range(0, 13):
            if i == 5:
                self.assertEqual(links[i]['name'], 'siteappsettings')
                self.assertEqual(links[i]['active'], True)
            else:
                self.assertEqual(links[i]['active'], False)

    def test_get_user_links_anon(self):
        """Test get_user_links() as anonymous user"""
        links = app_links.get_user_links(AnonymousUser())
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['name'], 'sign-in')

    @override_settings(PROJECTROLES_KIOSK_MODE=True)
    def test_get_user_links_anon_kiosk_mode(self):
        """Test get_user_links() as anonymous user and kiosk mode"""
        links = app_links.get_user_links(AnonymousUser())
        self.assertEqual(len(links), 0)

    def test_get_user_links_read_only(self):
        """Test get_user_links() with site read-only mode as regular user"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        # All should be returned
        self.assertEqual(len(app_links.get_user_links(self.user_owner)), 6)

    def test_get_user_links_read_only_superuser(self):
        """Test get_user_links() with site read-only mode as superuser"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        self.assertEqual(len(app_links.get_user_links(self.user)), 13)
