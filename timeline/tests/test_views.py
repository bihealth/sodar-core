"""View tests for the timeline app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAPI

from timeline.tests.test_models import (
    TimelineEventTestBase,
    TimelineEventMixin,
    TimelineEventStatusMixin,
    EXTRA_DATA,
)


plugin_api = PluginAPI()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
APP_NAME_PR = 'projectroles'


class ViewTestBase(
    TimelineEventMixin, TimelineEventStatusMixin, TimelineEventTestBase
):
    """Base class for timeline view testing"""

    def setUp(self):
        super().setUp()
        self.timeline = plugin_api.get_backend_api('timeline_backend')

        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        # Init category and project
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )


class TestProjectTimelineView(ViewTestBase):
    """Tests for ProjectTimelineView"""

    def test_get(self):
        """Test ProjectTimelineView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_project',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'].first(), self.event)

    def test_get_category(self):
        """Test GET with category"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_project',
                    kwargs={'project': self.category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)


class TestProjectObjectTimelineView(ViewTestBase):
    """Tests for ProjectObjectTimelineView"""

    def setUp(self):
        super().setUp()
        # Add user as an object reference
        self.obj_ref = self.event.add_object(
            obj=self.user, label='user', name=self.user.username
        )

    def test_get(self):
        """Test ProjectObjectTimelineView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_object',
                    kwargs={
                        'project': self.project.sodar_uuid,
                        'object_model': self.obj_ref.object_model,
                        'object_uuid': self.obj_ref.object_uuid,
                    },
                )
            )
        self.assertEqual(response.status_code, 200)


class TestSiteTimelineView(ViewTestBase):
    """Tests for SiteTimelineView"""

    def setUp(self):
        super().setUp()
        self.event_site = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )

    def test_get(self):
        """Test SiteTimelineView GET"""
        with self.login(self.user):
            response = self.client.get(reverse('timeline:list_site'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(
            response.context['object_list'].first(), self.event_site
        )


class TestSiteObjectTimelineView(ViewTestBase):
    """Tests for SiteObjectTimelineView"""

    def setUp(self):
        super().setUp()
        self.event_site = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )
        self.obj_ref = self.event_site.add_object(
            obj=self.user, label='user', name=self.user.username
        )

    def test_get(self):
        """Test SiteObjectTimelineView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'timeline:list_object_site',
                    kwargs={
                        'object_model': self.obj_ref.object_model,
                        'object_uuid': self.obj_ref.object_uuid,
                    },
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(
            response.context['object_list'].first(), self.event_site
        )


class TestAdminTimelineView(ViewTestBase):
    """Tests for AdminTimelineView"""

    def setUp(self):
        super().setUp()
        self.event_site = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.user,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )

    def test_get(self):
        """Test AdminTimelineView GET"""
        with self.login(self.user):
            response = self.client.get(reverse('timeline:list_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertEqual(
            response.context['object_list'].first(), self.event_site
        )
        self.assertEqual(response.context['object_list'][1], self.event)
