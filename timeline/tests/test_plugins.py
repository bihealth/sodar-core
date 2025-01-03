"""Plugin tests for the timeline app"""

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import (
    get_backend_api,
    ProjectAppPluginPoint,
    BackendPluginPoint,
    SiteAppPluginPoint,
    PluginSearchResult,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)

from timeline.api import TimelineAPI
from timeline.plugins import STATS_DESC_USER_COUNT

# from timeline.tests.test_models import TimelineEventMixin
from timeline.urls import urls_ui_project, urls_ui_site, urls_ui_admin


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
PROJECT_PLUGIN_NAME = 'timeline'
PROJECT_PLUGIN_TITLE = 'Timeline'
BACKEND_PLUGIN_NAME = 'timeline_backend'
BACKEND_PLUGIN_TITLE = 'Timeline Backend'
SITE_PLUGIN_NAME = 'timeline_site'
SITE_PLUGIN_TITLE = 'Site-Wide Events'
ADMIN_PLUGIN_NAME = 'timeline_site_admin'
ADMIN_PLUGIN_TITLE = 'All Timeline Events'
EVENT_NAME = 'test_event'
SEARCH_TERMS = ['test']
SEARCH_RET_CAT = 'all'
SEARCH_RET_TITLE = 'Timeline Events'
SEARCH_RET_TYPES = ['timeline']


class TimelinePluginTestBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    TestCase,
):
    """Base class for timeline plugin tests"""

    def setUp(self):
        # Init users
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.user_owner = self.make_user('user_owner')
        # Init roles
        self.init_roles()
        # Init category, project and roles
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )


class TestProjectAppPlugin(TimelinePluginTestBase):
    """Tests for timeline ProjectAppPlugin"""

    def setUp(self):
        super().setUp()
        self.plugin = ProjectAppPluginPoint.get_plugin(PROJECT_PLUGIN_NAME)
        self.event_kw = {
            'project': self.project,
            'app_name': 'projectroles',
            'user': self.user,
            'event_name': EVENT_NAME,
            'description': 'description',
        }
        self.timeline = get_backend_api('timeline_backend')

    def test_plugin_retrieval(self):
        """Test retrieving ProjectAppPlugin"""
        self.assertIsNotNone(self.plugin)
        self.assertEqual(self.plugin.get_model().name, PROJECT_PLUGIN_NAME)
        self.assertEqual(self.plugin.name, PROJECT_PLUGIN_NAME)
        self.assertEqual(self.plugin.get_model().title, PROJECT_PLUGIN_TITLE)
        self.assertEqual(self.plugin.urls, urls_ui_project)

    def test_get_statistics(self):
        """Test get_statistics() with no events"""
        expected = {
            'event_count': {
                'label': 'Events',
                'value': 0,
            },
            'user_count': {
                'label': 'Users',
                'description': STATS_DESC_USER_COUNT,
                'value': 0,
            },
        }
        self.assertEqual(self.plugin.get_statistics(), expected)

    def test_get_statistics_events(self):
        """Test get_statistics() with existing events"""
        self.timeline.add_event(**self.event_kw)
        self.event_kw['user'] = self.user_owner
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.get_statistics()
        self.assertEqual(ret['event_count']['value'], 2)
        self.assertEqual(ret['user_count']['value'], 2)

    def test_get_statistics_same_user(self):
        """Test get_statistics() with existing events by same user"""
        self.timeline.add_event(**self.event_kw)
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.get_statistics()
        self.assertEqual(ret['event_count']['value'], 2)
        self.assertEqual(ret['user_count']['value'], 1)

    def test_get_statistics_no_user(self):
        """Test get_statistics() with existing events including no user"""
        self.timeline.add_event(**self.event_kw)
        self.event_kw['user'] = None
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.get_statistics()
        self.assertEqual(ret['event_count']['value'], 2)
        self.assertEqual(ret['user_count']['value'], 1)

    def test_search(self):
        """Test search() with no events"""
        ret = self.plugin.search(SEARCH_TERMS, self.user)
        self.assertEqual(len(ret), 1)
        self.assertIsInstance(ret[0], PluginSearchResult)
        self.assertEqual(ret[0].category, SEARCH_RET_CAT)
        self.assertEqual(ret[0].title, SEARCH_RET_TITLE)
        self.assertEqual(ret[0].search_types, SEARCH_RET_TYPES)
        self.assertEqual(ret[0].items, [])

    def test_search_events(self):
        """Test search() with events"""
        event = self.timeline.add_event(**self.event_kw)
        self.event_kw['user'] = self.user_owner
        event2 = self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, self.user)
        self.assertEqual(len(ret), 1)
        self.assertIsInstance(ret[0].items, list)
        self.assertEqual(len(ret[0].items), 2)
        self.assertEqual(ret[0].items[0], event2)
        self.assertEqual(ret[0].items[1], event)

    def test_search_event_name(self):
        """Test search() with event name"""
        event = self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search([EVENT_NAME], self.user)
        self.assertEqual(len(ret), 1)
        self.assertEqual(len(ret[0].items), 1)
        self.assertEqual(ret[0].items[0], event)

    def test_search_event_name_display(self):
        """Test search() with event name in display formatting"""
        event = self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(['Test Event'], self.user)
        self.assertEqual(len(ret), 1)
        self.assertEqual(len(ret[0].items), 1)
        self.assertEqual(ret[0].items[0], event)

    def test_search_invalid_terms(self):
        """Test search() with invalid terms"""
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(['yuyaeQu7ma6aeFi2'], self.user)
        self.assertEqual(len(ret[0].items), 0)

    def test_search_mixed_terms(self):
        """Test search() with valid and invalid terms"""
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS + ['yuyaeQu7ma6aeFi2'], self.user)
        self.assertEqual(len(ret[0].items), 1)

    def test_search_no_perms(self):
        """Test search() as user with no permissions"""
        # Create user with no permissions to self.project
        user_no_perms = self.make_user('user_no_perms')
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, user_no_perms)
        self.assertEqual(len(ret[0].items), 0)

    def test_search_mixed_perms(self):
        """Test search() as user with mixed permissions"""
        user_new = self.make_user('user_new')
        project_new = self.make_project(
            'TestProject2', PROJECT_TYPE_PROJECT, self.category
        )
        self.make_assignment(project_new, self.user_owner, self.role_owner)
        self.make_assignment(project_new, user_new, self.role_contributor)
        self.timeline.add_event(**self.event_kw)
        self.event_kw['project'] = project_new
        project_event_new = self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, user_new)
        self.assertEqual(len(ret[0].items), 1)
        self.assertEqual(ret[0].items[0], project_event_new)
        ret = self.plugin.search(SEARCH_TERMS, self.user_owner)
        self.assertEqual(len(ret[0].items), 2)

    def test_search_project_classified_owner(self):
        """Test search() with classified project event as owner"""
        self.event_kw['classified'] = True
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, self.user_owner)
        self.assertEqual(len(ret[0].items), 1)

    def test_search_project_classified_contributor(self):
        """Test search() with classified project event as contributor"""
        user_contrib = self.make_user('user_contrib')
        self.make_assignment(self.project, user_contrib, self.role_contributor)
        self.event_kw['classified'] = True
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, user_contrib)
        self.assertEqual(len(ret[0].items), 0)

    def test_search_site_superuser(self):
        """Test search() with site event as superuser"""
        self.event_kw['project'] = None
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, self.user)
        self.assertEqual(len(ret[0].items), 1)

    def test_search_site_regular_user(self):
        """Test search() with site event as regular user"""
        self.event_kw['project'] = None
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, self.user_owner)
        self.assertEqual(len(ret[0].items), 1)

    def test_search_site_classified_superuser(self):
        """Test search() with classified site event as superuser"""
        self.event_kw['project'] = None
        self.event_kw['classified'] = True
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, self.user)
        self.assertEqual(len(ret[0].items), 1)

    def test_search_site_classified_regular_user(self):
        """Test search() with classified site event as regular user"""
        self.event_kw['project'] = None
        self.event_kw['classified'] = True
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(SEARCH_TERMS, self.user_owner)
        self.assertEqual(len(ret[0].items), 0)

    def test_search_type(self):
        """Test search() with defined search type"""
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(
            SEARCH_TERMS, self.user, search_type='timeline'
        )
        self.assertEqual(len(ret[0].items), 1)

    def test_search_type_invalid(self):
        """Test search() with invalid search type"""
        self.timeline.add_event(**self.event_kw)
        ret = self.plugin.search(
            SEARCH_TERMS, self.user, search_type='raTho0Oo'
        )
        self.assertEqual(len(ret[0].items), 0)


class TestBackendPlugin(TimelinePluginTestBase):
    """Tests for timeline BackendPlugin"""

    def setUp(self):
        super().setUp()
        self.plugin = BackendPluginPoint.get_plugin(BACKEND_PLUGIN_NAME)

    def test_plugin_retrieval(self):
        """Test retrieving BackendPlugin"""
        self.assertIsNotNone(self.plugin)
        self.assertEqual(self.plugin.get_model().name, BACKEND_PLUGIN_NAME)
        self.assertEqual(self.plugin.name, BACKEND_PLUGIN_NAME)
        self.assertEqual(self.plugin.get_model().title, BACKEND_PLUGIN_TITLE)

    def test_get_api(self):
        """Test get_api()"""
        self.assertIsInstance(self.plugin.get_api(), TimelineAPI)


class TestSiteAppPlugin(TimelinePluginTestBase):
    """Tests for timeline SiteAppPlugin"""

    def setUp(self):
        super().setUp()
        self.plugin = SiteAppPluginPoint.get_plugin(SITE_PLUGIN_NAME)

    def test_plugin_retrieval(self):
        """Test retrieving SiteAppPlugin"""
        self.assertIsNotNone(self.plugin)
        self.assertEqual(self.plugin.get_model().name, SITE_PLUGIN_NAME)
        self.assertEqual(self.plugin.name, SITE_PLUGIN_NAME)
        self.assertEqual(self.plugin.get_model().title, SITE_PLUGIN_TITLE)
        self.assertEqual(self.plugin.urls, urls_ui_site)


class TestAdminSiteAppPlugin(TimelinePluginTestBase):
    """Tests for timeline AdminSiteAppPlugin"""

    def setUp(self):
        super().setUp()
        self.plugin = SiteAppPluginPoint.get_plugin(ADMIN_PLUGIN_NAME)

    def test_plugin_retrieval(self):
        """Test retrieving AdminSiteAppPlugin"""
        self.assertIsNotNone(self.plugin)
        self.assertEqual(self.plugin.get_model().name, ADMIN_PLUGIN_NAME)
        self.assertEqual(self.plugin.name, ADMIN_PLUGIN_NAME)
        self.assertEqual(self.plugin.get_model().title, ADMIN_PLUGIN_TITLE)
        self.assertEqual(self.plugin.urls, urls_ui_admin)
