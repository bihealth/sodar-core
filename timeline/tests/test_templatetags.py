"""Tests for template tags in the timeline app"""

from django.urls import reverse
from django.utils.timezone import localtime

from djangoplugins.models import Plugin

# Projectroles dependency
from projectroles.plugins import PluginAPI

from timeline.models import TimelineEvent, DEFAULT_MESSAGES
from timeline.templatetags import timeline_tags as tags
from timeline.tests.test_api import TimelineAPIMixin
from timeline.tests.test_models import (
    TimelineEventTestBase,
    TimelineEventMixin,
    TimelineEventStatusMixin,
    TimelineEventObjectRefMixin,
)


plugin_api = PluginAPI()


# Local constants
APP_NAME_PR = 'projectroles'
APP_NAME_FF = 'filesfolders'
INVALID_APP_NAME = 'asdfghjk1235'
TEST_EVENT_NAME = 'test_event'
TEST_EVENT_DESC = 'test event'


class TestTemplateTags(
    TimelineAPIMixin,
    TimelineEventMixin,
    TimelineEventStatusMixin,
    TimelineEventObjectRefMixin,
    TimelineEventTestBase,
):
    """Tests for timeline template tags"""

    def setUp(self):
        super().setUp()

        # Initialize project event
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name='project_create',
            description='create project with {owner} as owner',
        )
        self.event_status = self.make_event_status(
            event=self.event,
            status_type='OK',
            description=DEFAULT_MESSAGES['OK'],
        )

        # Generate plugin lookup dict
        self.plugin_lookup = tags.get_plugin_lookup()
        # Get timeline API
        self.timeline = plugin_api.get_backend_api('timeline_backend')

    def test_get_timestamp(self):
        """Test get_timestamp()"""
        self.assertEqual(
            tags.get_timestamp(self.event),
            localtime(self.event_status.timestamp).strftime(
                '%Y-%m-%d %H:%M:%S'
            ),
        )

    def test_get_timestamp_no_status(self):
        """Test get_timestamp() with missing status object"""
        self.event_status.delete()
        self.assertEqual(tags.get_timestamp(self.event), 'N/A')

    def test_get_event_name(self):
        """Test get_event_name()"""
        self.assertEqual(self.event.event_name, 'project_create')
        self.assertEqual(tags.get_event_name(self.event), 'Project Create')

    def test_get_event_description(self):
        """Test get_event_description()"""
        request = self.get_request(self.user_owner, self.project)
        self.assertEqual(
            tags.get_event_description(self.event, self.plugin_lookup, request),
            self.timeline.get_event_description(self.event, request=request),
        )

    def test_get_event_description_no_request(self):
        """Test get_event_description() without a request object"""
        self.assertEqual(
            tags.get_event_description(self.event, self.plugin_lookup),
            self.timeline.get_event_description(self.event),
        )

    def test_get_details_events(self):
        """Test get_details_events()"""
        self.assertEqual(TimelineEvent.objects.count(), 1)
        self.assertEqual(len(tags.get_details_events(self.project)), 1)
        # Create 5 additional events for a total of 6
        for _ in range(5):
            event = self.make_event(
                project=self.project,
                app=APP_NAME_PR,
                user=self.user_owner,
                event_name=TEST_EVENT_NAME,
                description=TEST_EVENT_DESC,
            )
            self.make_event_status(
                event=event,
                status_type='OK',
                description=DEFAULT_MESSAGES['OK'],
            )
        self.assertEqual(TimelineEvent.objects.count(), 6)
        self.assertEqual(len(tags.get_details_events(self.project)), 5)

    def test_get_details_events_classified_disabled(self):
        """Test get_details_events() with disabled classified event display"""
        self.assertEqual(len(tags.get_details_events(self.project)), 1)
        event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
            classified=True,
        )
        self.make_event_status(
            event=event,
            status_type='OK',
            description=DEFAULT_MESSAGES['OK'],
        )
        self.assertEqual(TimelineEvent.objects.count(), 2)
        self.assertEqual(len(tags.get_details_events(self.project)), 1)

    def test_get_details_events_classified_enabled(self):
        """Test get_details_events() with enabled classified event display"""
        self.assertEqual(len(tags.get_details_events(self.project)), 1)
        event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
            classified=True,
        )
        self.make_event_status(
            event=event,
            status_type='OK',
            description=DEFAULT_MESSAGES['OK'],
        )
        ret = tags.get_details_events(self.project, view_classified=True)
        self.assertEqual(len(ret), 2)
        self.assertEqual(ret[0], event)  # Latest event should be first

    def test_get_plugin_lookup(self):
        """Test get_plugin_lookup()"""
        ret = tags.get_plugin_lookup()
        for p in Plugin.objects.all():
            self.assertIn(p.name, ret.keys())
            self.assertEqual(ret[p.name].__class__, p.get_plugin().__class__)

    def test_get_app_icon_html(self):
        """Test get_app_icon_html()"""
        ret = tags.get_app_icon_html(self.event, self.plugin_lookup)
        url = reverse(
            'projectroles:detail',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.assertIn('mdi:cube', ret)
        self.assertIn('Projectroles', ret)
        self.assertIn(url, ret)

    def test_get_app_icon_html_no_project(self):
        """Test get_app_icon_html() on event without project"""
        event = self.make_event(
            project=None,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
        )
        ret = tags.get_app_icon_html(event, self.plugin_lookup)
        self.assertIn(tags.ICON_PROJECTROLES, ret)
        self.assertIn('Projectroles', ret)
        self.assertNotIn('href=', ret)

    def test_get_app_icon_html_plugin(self):
        """Test get_app_icon_html() on event from an app plugin"""
        plugin = plugin_api.get_app_plugin(APP_NAME_FF)
        url = reverse(
            plugin.entry_point_url_id,
            kwargs={'project': self.project.sodar_uuid},
        )
        event = self.make_event(
            project=self.project,
            app=APP_NAME_FF,
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
        )
        ret = tags.get_app_icon_html(event, self.plugin_lookup)
        self.assertIn(plugin.icon, ret)
        self.assertIn(plugin.title, ret)
        self.assertIn(url, ret)

    def test_get_app_icon_html_projectroles(self):
        """Test get_app_icon_html() on event without project"""
        event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
        )
        url = reverse(
            'projectroles:detail',
            kwargs={'project': self.project.sodar_uuid},
        )
        ret = tags.get_app_icon_html(event, self.plugin_lookup)
        self.assertIn(tags.ICON_PROJECTROLES, ret)
        self.assertIn('Projectroles', ret)
        self.assertIn(url, ret)

    def test_get_app_icon_html_example_project_app(self):
        """Test get_app_icon_html() on event from an app plugin"""
        plugin = plugin_api.get_app_plugin('example_project_app')
        url = reverse(
            plugin.entry_point_url_id,
            kwargs={'project': self.project.sodar_uuid},
        )
        event = self.make_event(
            project=self.project,
            app='example_project_app',
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
        )
        ret = tags.get_app_icon_html(event, self.plugin_lookup)
        self.assertIn(plugin.icon, ret)
        self.assertIn(plugin.title, ret)
        self.assertIn(url, ret)

    def test_get_app_icon_html_example_site_app(self):
        """Test get_app_icon_html() on event from an app plugin"""
        plugin = plugin_api.get_app_plugin('example_site_app')
        url = reverse(
            plugin.entry_point_url_id,
            kwargs={},
        )
        event = self.make_event(
            project=self.project,
            app='example_site_app',
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
        )
        ret = tags.get_app_icon_html(event, self.plugin_lookup)
        self.assertIn(plugin.icon, ret)
        self.assertIn(plugin.title, ret)
        self.assertIn(url, ret)

    def test_get_app_icon_html_invalid_plugin(self):
        """Test get_app_icon_html() on event from an invalid plugin"""
        event = self.make_event(
            project=self.project,
            app=INVALID_APP_NAME,
            user=self.user_owner,
            event_name=TEST_EVENT_NAME,
            description=TEST_EVENT_DESC,
        )
        ret = tags.get_app_icon_html(event, self.plugin_lookup)
        self.assertIn(tags.ICON_UNKNOWN_APP, ret)
        self.assertIn(INVALID_APP_NAME, ret)  # No title = use app name in event
        self.assertNotIn('href=', ret)

    def test_get_status_style(self):
        """Test get_status_style()"""
        self.assertEqual(
            tags.get_status_style(self.event_status),
            tags.STATUS_STYLES[self.event_status.status_type] + ' text-light',
        )

    def test_get_status_style_invalid(self):
        """Test get_status_style() with an invalid stauts"""
        self.event_status.status_type = 'qwerty123456'
        self.assertEqual(tags.get_status_style(self.event_status), 'bg-light')

    # TODO: Test extra data tags once refactored
