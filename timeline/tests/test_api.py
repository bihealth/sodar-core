"""API tests for the timeline app"""

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.forms.models import model_to_dict
from django.test import RequestFactory
from django.urls import reverse

# Projectroles dependency
from projectroles.models import Project, SODARUser, SODAR_CONSTANTS
from projectroles.plugins import PluginAPI
from projectroles.tests.test_models import (
    RemoteSiteMixin,
    REMOTE_SITE_NAME,
    REMOTE_SITE_URL,
)

# Filesfolders dependency
from filesfolders.tests.test_models import FolderMixin

from timeline.models import (
    TimelineEvent,
    TimelineEventStatus,
    TimelineEventObjectRef,
    DEFAULT_MESSAGES,
)
from timeline.templatetags import timeline_tags as tags
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
APP_NAME_FF = 'filesfolders'


class TimelineAPIMixin:
    """Helpers for timeline API use"""

    @classmethod
    def get_request(cls, user: SODARUser, project: Project) -> HttpRequest:
        """Return mock request"""
        request = RequestFactory().get(
            'timeline:list', kwargs={'project': project}
        )
        request.user = user
        return request


class TestTimelineAPI(
    TimelineAPIMixin,
    TimelineEventMixin,
    TimelineEventStatusMixin,
    RemoteSiteMixin,
    FolderMixin,
    TimelineEventTestBase,
):
    def setUp(self):
        super().setUp()
        self.timeline = plugin_api.get_backend_api('timeline_backend')
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.save()

    def test_add_event(self):
        """Test adding an event"""
        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )

        self.assertEqual(TimelineEvent.objects.all().count(), 1)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 1)  # Init

        expected = {
            'id': event.pk,
            'project': self.project.pk,
            'app': APP_NAME_PR,
            'plugin': None,
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(event), expected)

        status = event.get_status()
        expected_status = {
            'id': status.pk,
            'event': event.pk,
            'status_type': self.timeline.TL_STATUS_INIT,
            'description': DEFAULT_MESSAGES[self.timeline.TL_STATUS_INIT],
            'extra_data': {},
            'sodar_uuid': status.sodar_uuid,
        }
        self.assertEqual(model_to_dict(status), expected_status)

    def test_add_event_with_status(self):
        """Test adding an event with status"""
        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_OK,
            status_desc=self.timeline.TL_STATUS_OK,
            status_extra_data={},
        )

        status = event.get_status()
        self.assertEqual(TimelineEvent.objects.all().count(), 1)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 2)

        expected_event = {
            'id': event.pk,
            'project': self.project.pk,
            'app': APP_NAME_PR,
            'plugin': None,
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(event), expected_event)

        expected_status = {
            'id': status.pk,
            'event': event.pk,
            'status_type': self.timeline.TL_STATUS_OK,
            'description': self.timeline.TL_STATUS_OK,
            'extra_data': {},
            'sodar_uuid': status.sodar_uuid,
        }
        self.assertEqual(model_to_dict(status), expected_status)

    def test_add_event_custom_init(self):
        """Test adding an event with custom INIT status"""
        custom_init_desc = 'Custom init'
        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_INIT,
            status_desc=custom_init_desc,
        )

        self.assertEqual(TimelineEvent.objects.all().count(), 1)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 1)  # Init

        status = event.get_status()
        expected_status = {
            'id': status.pk,
            'event': event.pk,
            'status_type': self.timeline.TL_STATUS_INIT,
            'description': custom_init_desc,
            'extra_data': {},
            'sodar_uuid': status.sodar_uuid,
        }
        self.assertEqual(model_to_dict(status), expected_status)

    def test_add_event_no_user(self):
        """Test adding an event with no user"""
        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=None,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )

        self.assertEqual(TimelineEvent.objects.all().count(), 1)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 1)

        expected = {
            'id': event.pk,
            'project': self.project.pk,
            'app': APP_NAME_PR,
            'plugin': None,
            'user': None,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(event), expected)

    def test_add_event_anon_user(self):
        """Test adding an event with AnonymousUser"""
        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=AnonymousUser(),
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )

        self.assertEqual(TimelineEvent.objects.all().count(), 1)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 1)
        self.assertIsNone(event.user)

    def test_add_event_invalid_app(self):
        """Test adding an event with an invalid app name (should fail)"""
        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.timeline.add_event(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                event_name='test_event',
                description='description',
                extra_data=EXTRA_DATA,
            )

        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

    def test_add_event_invalid_status(self):
        """Test adding an event with an invalid status type"""
        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

        with self.assertRaises(ValueError):
            self.timeline.add_event(
                project=self.project,
                app_name=APP_NAME_PR,
                user=self.user_owner,
                event_name='test_event',
                description='description',
                status_type='NON-EXISTING STATUS TYPE',
                extra_data=EXTRA_DATA,
            )

        self.assertEqual(TimelineEvent.objects.all().count(), 0)
        self.assertEqual(TimelineEventStatus.objects.all().count(), 0)

    def test_add_object(self):
        """Test adding an object to an event"""
        self.assertEqual(TimelineEventObjectRef.objects.all().count(), 0)

        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
            extra_data=EXTRA_DATA,
        )
        temp_obj = self.project.get_owner()
        ref = event.add_object(
            obj=temp_obj,
            label='obj',
            name='assignment',
            extra_data=EXTRA_DATA,
        )

        self.assertEqual(TimelineEventObjectRef.objects.all().count(), 1)
        expected = {
            'id': ref.pk,
            'event': event.pk,
            'label': 'obj',
            'name': 'assignment',
            'object_model': temp_obj.__class__.__name__,
            'object_uuid': temp_obj.sodar_uuid,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': ref.sodar_uuid,
        }
        self.assertEqual(model_to_dict(ref), expected)

    def test_get_project_events(self):
        """Test get_project_events()"""
        event_normal = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )
        event_classified = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=True,
            extra_data=EXTRA_DATA,
        )

        events = self.timeline.get_project_events(
            self.project, classified=False
        )
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0], event_normal)

        # Test with classified
        events = self.timeline.get_project_events(self.project, classified=True)
        self.assertEqual(events.count(), 2)
        self.assertIn(event_classified, events)

    def test_get_object_url(self):
        """Test get_object_url()"""
        expected_url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        url = self.timeline.get_object_url(self.user_owner, self.project)
        self.assertEqual(expected_url, url)

    def test_get_object_url_no_project(self):
        """Test get_object_url() without project"""
        expected_url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        url = self.timeline.get_object_url(self.user_owner, None)
        self.assertEqual(expected_url, url)

    def test_get_object_link(self):
        """Test get_object_link()"""
        expected_url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        link = self.timeline.get_object_link(self.user_owner, self.project)
        self.assertIn(expected_url, link)

    def test_get_object_link_no_project(self):
        """Test get_object_link() without project"""
        expected_url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': self.user_owner.__class__.__name__,
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )
        link = self.timeline.get_object_link(self.user_owner, None)
        self.assertIn(expected_url, link)

    def test_get_event_description(self):
        """Test getting event description"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
        )
        self.assertEqual(
            self.timeline.get_event_description(event), event.description
        )

    def test_get_event_description_user(self):
        """Test getting event description with User object"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        event.add_object(
            obj=self.user_owner,
            label='obj',
            name=self.user_owner.username,
        )
        desc = self.timeline.get_event_description(event)
        self.assertIn(self.user_owner.username, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_project(self):
        """Test getting event description with Project object"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        event.add_object(
            obj=self.project,
            label='obj',
            name=self.project.title,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.user_owner, self.project)
        )
        self.assertIn(self.project.title, desc)
        self.assertIn('sodar-tl-project-link', desc)

    def test_get_event_description_remote_site(self):
        """Test getting event description with RemoteSite object"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        site = self.make_site(name=REMOTE_SITE_NAME, url=REMOTE_SITE_URL)
        event.add_object(
            obj=site,
            label='obj',
            name=site.name,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertIn(site.name, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_app(self):
        """Test getting event description with app plugin"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_FF,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            description='',
            owner=self.user_owner,
        )
        event.add_object(
            obj=folder,
            label='obj',
            name=folder.name,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertIn(folder.name, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_lookup(self):
        """Test getting event description with app plugin and lookup dict"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_FF,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            description='',
            owner=self.user_owner,
        )
        event.add_object(
            obj=folder,
            label='obj',
            name=folder.name,
        )
        desc = self.timeline.get_event_description(
            event,
            plugin_lookup=tags.get_plugin_lookup(),
            request=self.get_request(self.superuser, self.project),
        )
        self.assertIn(folder.name, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_invalid_app(self):
        """Test getting event description with non-existing app plugin"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        event.app = 'NOT_AN_ACTUAL_APP'
        event.save()
        event.add_object(
            obj=self.project,
            label='obj',
            name=self.project.title,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertNotIn(self.project.title, desc)
        self.assertIn('sodar-tl-plugin-error', desc)

    def test_get_event_description_specified_plugin(self):
        """Test getting event description with specified app plugin"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_FF,
            plugin_name=APP_NAME_FF,
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            description='',
            owner=self.user_owner,
        )
        event.add_object(
            obj=folder,
            label='obj',
            name=folder.name,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertIn(folder.name, desc)
        self.assertIn('sodar-tl-object-link', desc)

    def test_get_event_description_invalid_plugin(self):
        """Test description with an invalid specified app plugin"""
        event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_FF,
            plugin_name='NOT_A_REAL_PLUGIN',
            user=self.user_owner,
            event_name='test_event',
            description='event with {obj}',
        )
        folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            description='',
            owner=self.user_owner,
        )
        event.add_object(
            obj=folder,
            label='obj',
            name=folder.name,
        )
        desc = self.timeline.get_event_description(
            event, request=self.get_request(self.superuser, self.project)
        )
        self.assertNotIn(folder.name, desc)
        self.assertIn('sodar-tl-plugin-error', desc)
