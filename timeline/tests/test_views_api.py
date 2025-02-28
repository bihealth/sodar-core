"""REST API view tests for the timeline app"""

import json
import uuid

from django.urls import reverse

from test_plus.test import APITestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)
from projectroles.tests.test_views_api import (
    SODARAPIViewTestMixin,
    TEST_SERVER_URL,
)

from timeline.tests.test_models import (
    TimelineEventMixin,
    TimelineEventStatusMixin,
    TimelineEventObjectRefMixin,
    EXTRA_DATA,
)
from timeline.views_api import (
    TIMELINE_API_MEDIA_TYPE,
    TIMELINE_API_DEFAULT_VERSION,
)


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']

# Local constants
APP_NAME_PR = 'projectroles'
EVENT_NAME = 'test_event'
EVENT_NAME_CLASSIFIED = 'test_event_classified'
EVENT_DESC = 'description'
OBJ_REF_LABEL = 'test_label'
OBJ_REF_NAME = 'test_obj_name'


class TimelineAPIViewTestBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    TimelineEventMixin,
    TimelineEventStatusMixin,
    TimelineEventObjectRefMixin,
    SODARAPIViewTestMixin,
    APITestCase,
):
    """Base class for timeline API view tests"""

    media_type = TIMELINE_API_MEDIA_TYPE
    api_version = TIMELINE_API_DEFAULT_VERSION

    def setUp(self):
        self.maxDiff = None
        # Init roles
        self.init_roles()
        # Init users
        self.superuser = self.make_user('superuser')
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        self.user_owner = self.make_user('user_owner')
        self.user_delegate = self.make_user('user_delegate')
        self.user_contributor = self.make_user('user_contributor')
        # Init category and project
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )
        # Init project
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.delegate_as = self.make_assignment(
            self.project, self.user_delegate, self.role_delegate
        )
        self.contrib_as = self.make_assignment(
            self.project, self.user_contributor, self.role_contributor
        )
        # Get knox token for self.user
        self.knox_token = self.get_token(self.superuser)


class TestProjectTimelineEventListAPIView(TimelineAPIViewTestBase):
    """Tests for ProjectTimelineEventListAPIView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=EVENT_NAME,
            description=EVENT_DESC,
            classified=False,
            extra_data=EXTRA_DATA,
        )
        self.event_classified = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=EVENT_NAME_CLASSIFIED,
            description=EVENT_DESC,
            classified=True,
            extra_data=EXTRA_DATA,
        )
        self.url = reverse(
            'timeline:api_list_project',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get_superuser(self):
        """Test ProjectTimelineEventListAPIView GET as superuser"""
        response = self.request_knox(
            self.url, token=self.get_token(self.superuser)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        expected = {
            'project': str(self.project.sodar_uuid),
            'app': APP_NAME_PR,
            'plugin': None,
            'user': str(self.user_owner.sodar_uuid),
            'event_name': EVENT_NAME,
            'description': EVENT_DESC,
            'extra_data': EXTRA_DATA,
            'classified': False,
            'status_changes': [],
            'event_objects': [],
            'sodar_uuid': str(self.event.sodar_uuid),
        }
        self.assertEqual(response_data[1], expected)
        expected = {
            'project': str(self.project.sodar_uuid),
            'app': APP_NAME_PR,
            'plugin': None,
            'user': str(self.user_owner.sodar_uuid),
            'event_name': EVENT_NAME_CLASSIFIED,
            'description': EVENT_DESC,
            'extra_data': EXTRA_DATA,
            'classified': True,
            'status_changes': [],
            'event_objects': [],
            'sodar_uuid': str(self.event_classified.sodar_uuid),
        }
        self.assertEqual(response_data[0], expected)

    def test_get_pagination(self):
        """Test GET with pagination"""
        url = self.url + '?page=1'
        response = self.request_knox(url, token=self.get_token(self.superuser))
        self.assertEqual(response.status_code, 200)
        expected = {
            'count': 2,
            'next': TEST_SERVER_URL + self.url + '?page=2',
            'previous': None,
            'results': [
                {
                    'project': str(self.project.sodar_uuid),
                    'app': APP_NAME_PR,
                    'plugin': None,
                    'user': str(self.user_owner.sodar_uuid),
                    'event_name': EVENT_NAME_CLASSIFIED,
                    'description': EVENT_DESC,
                    'extra_data': EXTRA_DATA,
                    'classified': True,
                    'status_changes': [],
                    'event_objects': [],
                    'sodar_uuid': str(self.event_classified.sodar_uuid),
                }
            ],
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_get_owner(self):
        """Test GET as owner"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_owner)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['extra_data'], EXTRA_DATA)
        self.assertEqual(response_data[1]['extra_data'], EXTRA_DATA)

    def test_get_delegate(self):
        """Test GET as delegate"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_delegate)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['extra_data'], EXTRA_DATA)
        self.assertEqual(response_data[1]['extra_data'], EXTRA_DATA)

    def test_get_contributor(self):
        """Test GET as contributor"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_contributor)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(
            response_data[0]['sodar_uuid'], str(self.event.sodar_uuid)
        )
        self.assertNotIn('extra_data', response_data[0])

    def test_get_object_ref_owner(self):
        """Test GET with object reference as owner"""
        obj_ref = self.make_object_ref(
            event=self.event,
            obj=self.user_owner,
            label=OBJ_REF_LABEL,
            name=OBJ_REF_NAME,
            uuid=self.user_owner.sodar_uuid,
            extra_data=EXTRA_DATA,
        )
        response = self.request_knox(
            self.url, token=self.get_token(self.user_owner)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = [
            {
                'event': str(self.event.sodar_uuid),
                'label': OBJ_REF_LABEL,
                'name': OBJ_REF_NAME,
                'object_model': 'User',
                'object_uuid': str(self.user_owner.sodar_uuid),
                'extra_data': EXTRA_DATA,
                'sodar_uuid': str(obj_ref.sodar_uuid),
            }
        ]
        self.assertEqual(response_data[1]['event_objects'], expected)

    def test_get_object_ref_delegate(self):
        """Test GET with object reference as delegate"""
        self.make_object_ref(
            event=self.event,
            obj=self.user_owner,
            label=OBJ_REF_LABEL,
            name=OBJ_REF_NAME,
            uuid=self.user_owner.sodar_uuid,
            extra_data=EXTRA_DATA,
        )
        response = self.request_knox(
            self.url, token=self.get_token(self.user_delegate)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data[1]['event_objects']), 1)
        self.assertEqual(
            response_data[1]['event_objects'][0]['extra_data'], EXTRA_DATA
        )

    def test_get_object_ref_contributor(self):
        """Test GET with object reference as contributor"""
        self.make_object_ref(
            event=self.event,
            obj=self.user_owner,
            label=OBJ_REF_LABEL,
            name=OBJ_REF_NAME,
            uuid=self.user_owner.sodar_uuid,
            extra_data=EXTRA_DATA,
        )
        response = self.request_knox(
            self.url, token=self.get_token(self.user_contributor)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data[0]['event_objects']), 1)
        # No extra data should be returned for contributors and below
        self.assertNotIn('extra_data', response_data[0]['event_objects'][0])

    def test_get_status_owner(self):
        """Test GET with status changes as owner"""
        status_init = self.make_event_status(
            event=self.event,
            status_type='INIT',
            description='INIT',
            extra_data=EXTRA_DATA,
        )
        status_ok = self.make_event_status(
            event=self.event,
            status_type='OK',
            description='OK',
            extra_data=EXTRA_DATA,
        )
        response = self.request_knox(
            self.url, token=self.get_token(self.user_owner)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = [
            {
                'event': str(self.event.sodar_uuid),
                'timestamp': self.get_drf_datetime(status_init.timestamp),
                'status_type': 'INIT',
                'description': 'INIT',
                'extra_data': EXTRA_DATA,
                'sodar_uuid': str(status_init.sodar_uuid),
            },
            {
                'event': str(self.event.sodar_uuid),
                'timestamp': self.get_drf_datetime(status_ok.timestamp),
                'status_type': 'OK',
                'description': 'OK',
                'extra_data': EXTRA_DATA,
                'sodar_uuid': str(status_ok.sodar_uuid),
            },
        ]
        self.assertEqual(response_data[1]['status_changes'], expected)

    def test_get_status_delegate(self):
        """Test GET with status changes as delegate"""
        self.make_event_status(
            event=self.event,
            status_type='INIT',
            description='INIT',
            extra_data=EXTRA_DATA,
        )
        response = self.request_knox(
            self.url, token=self.get_token(self.user_delegate)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data[1]['status_changes'][0]['extra_data'], EXTRA_DATA
        )

    def test_get_status_contributor(self):
        """Test GET with status changes as contributor"""
        self.make_event_status(
            event=self.event,
            status_type='INIT',
            description='INIT',
            extra_data=EXTRA_DATA,
        )
        response = self.request_knox(
            self.url, token=self.get_token(self.user_contributor)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertNotIn('extra_data', response_data[0]['status_changes'][0])


class TestSiteTimelineEventListAPIView(TimelineAPIViewTestBase):
    """Tests for SiteTimelineEventListAPIView"""

    def setUp(self):
        super().setUp()
        self.project_event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=EVENT_NAME,
            description=EVENT_DESC,
            classified=False,
            extra_data=EXTRA_DATA,
        )
        self.site_event = self.make_event(
            project=None,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=EVENT_NAME,
            description=EVENT_DESC,
            classified=False,
            extra_data=EXTRA_DATA,
        )
        self.site_event_classified = self.make_event(
            project=None,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=EVENT_NAME_CLASSIFIED,
            description=EVENT_DESC,
            classified=True,
            extra_data=EXTRA_DATA,
        )
        self.url = reverse('timeline:api_list_site')

    def test_get_superuser(self):
        """Test SiteTimelineEventListAPIView GET as superuser"""
        response = self.request_knox(
            self.url, token=self.get_token(self.superuser)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(
            response_data[0]['sodar_uuid'],
            str(self.site_event_classified.sodar_uuid),
        )
        self.assertEqual(
            response_data[1]['sodar_uuid'], str(self.site_event.sodar_uuid)
        )

    def test_get_regular_user(self):
        """Test GET as regular_user"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_owner)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(
            response_data[0]['sodar_uuid'], str(self.site_event.sodar_uuid)
        )


class TestTimelineEventRetrieveAPIView(TimelineAPIViewTestBase):
    """Tests for TimelineEventRetrieveAPIView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name=EVENT_NAME,
            description=EVENT_DESC,
            classified=False,
            extra_data=EXTRA_DATA,
        )

    def test_get(self):
        """Test TimelineEventRetrieveAPIView GET"""
        url = reverse(
            'timeline:api_retrieve',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )
        response = self.request_knox(url, token=self.get_token(self.superuser))
        self.assertEqual(response.status_code, 200)
        expected = {
            'project': str(self.project.sodar_uuid),
            'app': APP_NAME_PR,
            'plugin': None,
            'user': str(self.user_owner.sodar_uuid),
            'event_name': EVENT_NAME,
            'description': EVENT_DESC,
            'extra_data': EXTRA_DATA,
            'classified': False,
            'status_changes': [],
            'event_objects': [],
            'sodar_uuid': str(self.event.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_get_not_found(self):
        """Test GET with invalid UUID"""
        invalid_uuid = uuid.uuid4()
        self.assertNotEqual(self.event.sodar_uuid, invalid_uuid)
        url = reverse(
            'timeline:api_retrieve', kwargs={'timelineevent': invalid_uuid}
        )
        response = self.request_knox(url, token=self.get_token(self.superuser))
        self.assertEqual(response.status_code, 404)
