"""Ajax API view tests for the timeline app"""

from django.urls import reverse
from django.utils.timezone import localtime

# Projectroles dependency
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin
from projectroles.tests.test_views import (
    ViewTestBase,
    PROJECT_TYPE_CATEGORY,
    PROJECT_TYPE_PROJECT,
)

from timeline.models import DEFAULT_MESSAGES
from timeline.views_ajax import EventExtraDataMixin
from timeline.templatetags.timeline_tags import get_status_style
from timeline.tests.test_models import TimelineEventMixin


# Local constants
APP_NAME_PR = 'projectroles'


class TimelineAjaxViewTestBase(
    ProjectMixin, RoleAssignmentMixin, TimelineEventMixin, ViewTestBase
):
    """Base class for timeline Ajax API view tests"""

    @classmethod
    def _format_ts(cls, timestamp):
        """Format timestamp as an expected value from the Ajax API view"""
        return localtime(timestamp).strftime('%Y-%m-%d %H:%M:%S')

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


class TestProjectEventDetailAjaxView(TimelineAjaxViewTestBase):
    """Tests for ProjectEventDetailAjaxView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, APP_NAME_PR, self.user, 'project_create'
        )
        self.event_status_init = self.event.set_status(
            'INIT', DEFAULT_MESSAGES['INIT']
        )
        self.event_status_ok = self.event.set_status(
            'OK', DEFAULT_MESSAGES['OK'], extra_data={'test': 'test'}
        )
        self.url = reverse(
            'timeline:ajax_detail_project',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectEventDetailAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event.app,
            'name': self.event.event_name,
            'user': self.user.username,
            'timestamp': self._format_ts(self.event.get_timestamp()),
            'status': [
                {
                    'type': 'OK',
                    'class': get_status_style(self.event_status_ok),
                    'description': DEFAULT_MESSAGES['OK'],
                    'timestamp': self._format_ts(
                        self.event_status_ok.timestamp
                    ),
                    'extra_status_link': reverse(
                        'timeline:ajax_extra_status',
                        kwargs={
                            'eventstatus': self.event_status_ok.sodar_uuid,
                        },
                    ),
                },
                {
                    'type': 'INIT',
                    'class': get_status_style(self.event_status_init),
                    'description': DEFAULT_MESSAGES['INIT'],
                    'timestamp': self._format_ts(
                        self.event_status_init.timestamp
                    ),
                    'extra_status_link': None,
                },
            ],
        }
        self.assertEqual(response.data, expected)

    def test_get_no_user(self):
        """Test GET for event with no user"""
        self.event.user = None
        self.event.save()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user'], 'N/A')


class TestProjectEventExtraAjaxView(TimelineAjaxViewTestBase):
    """Tests for ProjectEventExtraAjaxView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project,
            APP_NAME_PR,
            self.user,
            'project_create',
            extra_data={'example_data': 'example_extra_data'},
        )
        self.event_status_init = self.event.set_status(
            'INIT', DEFAULT_MESSAGES['INIT']
        )
        self.event_status_ok = self.event.set_status(
            'OK', DEFAULT_MESSAGES['OK']
        )
        self.url = reverse(
            'timeline:ajax_extra_project',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectEventExtraAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event.app,
            'user': self.user.username,
            'extra': self.event.extra_data,
        }
        self.assertIn(expected['app'], str(response.data))
        self.assertIn(expected['user'], str(response.data))
        self.assertIn(expected['extra']['example_data'], str(response.data))

    def test_get_no_user(self):
        """Test GET for event with no user"""
        self.event.user = None
        self.event.save()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user'], 'N/A')


class TestSiteEventDetailAjaxView(TimelineAjaxViewTestBase):
    """Tests for SiteEventDetailAjaxView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(None, APP_NAME_PR, self.user, 'test_event')
        self.event_status_init = self.event.set_status(
            'INIT', DEFAULT_MESSAGES['INIT']
        )
        self.event_status_ok = self.event.set_status(
            'OK', DEFAULT_MESSAGES['OK'], extra_data={'test': 'test'}
        )

    def test_get(self):
        """Test SiteEventDetailAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:ajax_detail_site',
                    kwargs={'timelineevent': self.event.sodar_uuid},
                ),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event.app,
            'name': self.event.event_name,
            'user': self.user.username,
            'timestamp': self._format_ts(self.event.get_timestamp()),
            'status': [
                {
                    'type': 'OK',
                    'class': get_status_style(self.event_status_ok),
                    'description': DEFAULT_MESSAGES['OK'],
                    'timestamp': self._format_ts(
                        self.event_status_ok.timestamp
                    ),
                    'extra_status_link': reverse(
                        'timeline:ajax_extra_status',
                        kwargs={
                            'eventstatus': self.event_status_ok.sodar_uuid,
                        },
                    ),
                },
                {
                    'type': 'INIT',
                    'class': get_status_style(self.event_status_init),
                    'description': DEFAULT_MESSAGES['INIT'],
                    'timestamp': self._format_ts(
                        self.event_status_init.timestamp
                    ),
                    'extra_status_link': None,
                },
            ],
        }
        self.assertEqual(response.data, expected)


class TestSiteEventExtraAjaxView(TimelineAjaxViewTestBase):
    """Tests for SiteEventExtraAjaxView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            None,
            APP_NAME_PR,
            self.user,
            'test_event',
            extra_data={'example_data': 'example_extra_data'},
        )
        self.event_status_init = self.event.set_status(
            'INIT', DEFAULT_MESSAGES['INIT']
        )
        self.event_status_ok = self.event.set_status(
            'OK', DEFAULT_MESSAGES['OK']
        )

    def test_get(self):
        """Test SiteEventExtraAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:ajax_extra_site',
                    kwargs={'timelineevent': self.event.sodar_uuid},
                ),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event.app,
            'name': self.event.event_name,
            'user': self.user.username,
            'timestamp': self._format_ts(self.event.get_timestamp()),
            'extra': self.event.extra_data,
        }
        self.assertIn(expected['app'], str(response.data))
        self.assertIn(expected['user'], str(response.data))


class TestEventStatusExtraAjaxView(
    TimelineAjaxViewTestBase, EventExtraDataMixin
):
    """Tests for EventStatusExtraAjaxView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, APP_NAME_PR, self.user, 'test_event'
        )
        self.event_status_init = self.event.set_status(
            'INIT',
            DEFAULT_MESSAGES['INIT'],
            extra_data={'test': 'test'},
        )
        self.event_site = self.make_event(
            None, APP_NAME_PR, self.user, 'test_event_site'
        )
        self.event_site_status_init = self.event_site.set_status(
            'INIT',
            DEFAULT_MESSAGES['INIT'],
            extra_data={'test': 'test'},
        )

    def test_get_project(self):
        """Test EventStatusExtraAjaxView GET with project event"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:ajax_extra_status',
                    kwargs={
                        'eventstatus': self.event_status_init.sodar_uuid,
                    },
                ),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event.app,
            'name': self.event.event_name,
            'user': self.user.username,
            'timestamp': self._format_ts(self.event.get_timestamp()),
            'extra': self.get_event_extra(self.event, status=0)['extra'],
        }
        self.assertEqual(response.data, expected)

    def test_get_site(self):
        """Test GET with site event"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:ajax_extra_status',
                    kwargs={
                        'eventstatus': self.event_site_status_init.sodar_uuid,
                    },
                ),
            )
        self.assertEqual(response.status_code, 200)
        expected = {
            'app': self.event_site.app,
            'name': self.event_site.event_name,
            'user': self.user.username,
            'timestamp': self._format_ts(self.event_site.get_timestamp()),
            'extra': self.get_event_extra(self.event_site, status=0)['extra'],
        }
        self.assertEqual(response.data, expected)
