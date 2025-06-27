"""Model tests for the timeline app"""

from typing import Any, Optional, Union
from uuid import UUID

from django.forms.models import model_to_dict

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import Project, SODARUser, SODAR_CONSTANTS
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)

from timeline.models import (
    TimelineEvent,
    TimelineEventObjectRef,
    TimelineEventStatus,
    OBJ_REF_UNNAMED,
    TL_STATUS_OK,
    TL_STATUS_FAILED,
)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


# Local constants
APP_NAME_PR = 'projectroles'
EXTRA_DATA = {'test_key': 'test_val'}


class TimelineEventMixin:
    """Helper mixin for TimelineEvent creation"""

    @classmethod
    def make_event(
        cls,
        project: Optional[Project],
        app: str,
        user: Optional[SODARUser],
        event_name: str,
        description: str = '',
        classified: bool = False,
        extra_data: Union[dict, list] = {'test': 'test'},
        plugin: Optional[str] = None,
    ) -> TimelineEvent:
        """Create TimelineEvent object"""
        values = {
            'project': project,
            'app': app,
            'user': user,
            'event_name': event_name,
            'description': description,
            'classified': classified,
            'extra_data': extra_data or {},
            'plugin': plugin,
        }
        return TimelineEvent.objects.create(**values)


class TimelineEventObjectRefMixin:
    """Helper mixin for TimelineEventObjectRef creation"""

    @classmethod
    def make_object_ref(
        cls,
        event: TimelineEvent,
        obj: Any,
        label: str,
        name: str,
        uuid: Union[str, UUID],
        extra_data: Union[dict, list, None] = None,
    ) -> TimelineEventObjectRef:
        values = {
            'event': event,
            'label': label,
            'name': name,
            'object_model': obj.__class__.__name__,
            'object_uuid': uuid,
            'extra_data': extra_data or {},
        }
        """Create TimelineEventObjectRef object"""
        return TimelineEventObjectRef.objects.create(**values)


class TimelineEventStatusMixin:
    """Helper mixin for TimelineEventStatus creation"""

    @classmethod
    def make_event_status(
        cls,
        event: TimelineEvent,
        status_type: str,
        description: str = '',
        extra_data: Union[dict, list, None] = None,
    ) -> TimelineEventStatus:
        values = {
            'event': event,
            'status_type': status_type,
            'description': description,
            'extra_data': extra_data or {'test': 'test'},
        }
        """Create TimelineEventStatus object"""
        return TimelineEventStatus.objects.create(**values)


class TimelineEventTestBase(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, TestCase
):
    def setUp(self):
        # Make owner user
        self.user_owner = self.make_user('owner')
        # Init roles
        self.init_roles()
        # Init project and assignment
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.assignment_owner = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )


class TestTimelineEvent(
    TimelineEventMixin,
    TimelineEventStatusMixin,
    TimelineEventObjectRefMixin,
    TimelineEventTestBase,
):
    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data=EXTRA_DATA,
        )

        self.obj_ref = self.make_object_ref(
            event=self.event,
            obj=self.assignment_owner,
            label='test_label',
            name='test_object_name',
            uuid=self.assignment_owner.sodar_uuid,
            extra_data=EXTRA_DATA,
        )

    def test_initialization(self):
        """Test TimelineEvent initialization"""
        expected = {
            'id': self.event.pk,
            'project': self.project.pk,
            'app': APP_NAME_PR,
            'plugin': None,
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_initialization_no_project(self):
        """Test TimelineEvent initialization with no project"""
        self.event = self.make_event(
            project=None,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data=EXTRA_DATA,
        )
        expected = {
            'id': self.event.pk,
            'project': None,
            'app': APP_NAME_PR,
            'plugin': None,
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_initialization_no_user(self):
        """Test TimelineEvent initialization with no user"""
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=None,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data=EXTRA_DATA,
        )
        expected = {
            'id': self.event.pk,
            'project': self.project.pk,
            'app': APP_NAME_PR,
            'plugin': None,
            'user': None,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_initialization_plugin(self):
        """Test TimelineEvent initialization with specific plugin name"""
        self.event = self.make_event(
            project=None,
            app=APP_NAME_PR,
            plugin='plugin_name',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data=EXTRA_DATA,
        )
        expected = {
            'id': self.event.pk,
            'project': None,
            'app': APP_NAME_PR,
            'plugin': 'plugin_name',
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_str(self):
        """Test TimelineEvent __str__()"""
        expected = 'TestProject: test_event/owner'
        self.assertEqual(str(self.event), expected)

    def test_str_no_user(self):
        """Test TimelineEvent __str__() with no user"""
        self.event.user = None
        self.event.save()
        expected = 'TestProject: test_event'
        self.assertEqual(str(self.event), expected)

    def test_str_no_project(self):
        """Test TimelineEvent __str__() with no project"""
        self.event.project = None
        self.event.save()
        expected = 'test_event/owner'
        self.assertEqual(str(self.event), expected)

    def test_str_no_project_no_user(self):
        """Test TimelineEvent __str__() with no project or user"""
        self.event.project = None
        self.event.user = None
        self.event.save()
        expected = 'test_event'
        self.assertEqual(str(self.event), expected)

    def test_repr(self):
        """Test TimelineEvent __repr__()"""
        expected = "TimelineEvent('TestProject', 'test_event', 'owner')"
        self.assertEqual(repr(self.event), expected)

    def test_repr_no_user(self):
        """Test TimelineEvent __repr__() with no user"""
        self.event.user = None
        self.event.save()
        expected = "TimelineEvent('TestProject', 'test_event', 'N/A')"
        self.assertEqual(repr(self.event), expected)

    def test_repr_no_project(self):
        """Test TimelineEvent __repr__() with no project"""
        self.event.project = None
        self.event.save()
        expected = "TimelineEvent('N/A', 'test_event', 'owner')"
        self.assertEqual(repr(self.event), expected)

    def test_repr_no_project_no_user(self):
        """Test TimelineEvent __repr__() with no project or user"""
        self.event.project = None
        self.event.user = None
        self.event.save()
        expected = "TimelineEvent('N/A', 'test_event', 'N/A')"
        self.assertEqual(repr(self.event), expected)

    def test_add_object(self):
        """Test add_object()"""
        # Init new user and role
        new_user = self.make_user('new_user')
        new_as = self.make_assignment(
            self.project, new_user, self.role_delegate
        )
        new_obj = self.event.add_object(
            obj=new_as, label='new_label', name='new_name'
        )
        expected = {
            'id': new_obj.pk,
            'event': self.event.pk,
            'label': 'new_label',
            'name': 'new_name',
            'object_uuid': new_as.sodar_uuid,
            'object_model': 'RoleAssignment',
            'extra_data': {},
            'sodar_uuid': new_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(new_obj), expected)

    def test_add_object_no_name(self):
        """Test add_object() with no name for object"""
        new_user = self.make_user('new_user')
        new_user.name = 'New User'
        new_as = self.make_assignment(
            self.project, new_user, self.role_delegate
        )
        new_obj = self.event.add_object(obj=new_as, label='new_label', name='')
        self.assertEqual(new_obj.name, OBJ_REF_UNNAMED)

    def test_find_event_name(self):
        """Test TimelineEvent.find() with event name"""
        objects = TimelineEvent.objects.find(['test_event'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_description(self):
        """Test TimelineEvent.find() with event description"""
        objects = TimelineEvent.objects.find(['description'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_object(self):
        """Test TimelineEvent.find() with object reference"""
        objects = TimelineEvent.objects.find(['test_object_name'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_fail(self):
        """Test TimelineEvent.find() with no matches"""
        objects = TimelineEvent.objects.find(['asdfasdfafasdf'])
        self.assertEqual(len(objects), 0)

    def test_find_user_username(self):
        """Test TimelineEvent.find() with user username"""
        objects = TimelineEvent.objects.find([self.user_owner.username])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_user_username_not_found(self):
        """Test TimelineEvent.find() with user username not found"""
        user_new = self.make_user('user_new')
        objects = TimelineEvent.objects.find([user_new.username])
        self.assertEqual(len(objects), 0)

    def test_find_user_full_name(self):
        """Test TimelineEvent.find() with user full name"""
        self.user_owner.name = 'Owner User'
        self.user_owner.save()
        objects = TimelineEvent.objects.find([self.user_owner.name])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_user_full_name_not_found(self):
        """Test TimelineEvent.find() with user full name not found"""
        self.user_owner.name = 'Owner User'
        self.user_owner.save()
        objects = TimelineEvent.objects.find(['Other User'])
        self.assertEqual(len(objects), 0)


class TestTimelineEventObjectRef(
    TimelineEventMixin, TimelineEventObjectRefMixin, TimelineEventTestBase
):
    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data=EXTRA_DATA,
        )
        self.obj_ref = self.make_object_ref(
            event=self.event,
            obj=self.assignment_owner,
            label='test_label',
            name='test_name',
            uuid=self.assignment_owner.sodar_uuid,
            extra_data=EXTRA_DATA,
        )

    def test_initialization(self):
        """Test TimelineEventObjectRef initialization"""
        expected = {
            'id': self.obj_ref.pk,
            'event': self.event.pk,
            'label': 'test_label',
            'name': 'test_name',
            'object_model': 'RoleAssignment',
            'object_uuid': self.assignment_owner.sodar_uuid,
            'extra_data': EXTRA_DATA,
            'sodar_uuid': self.obj_ref.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.obj_ref), expected)

    def test__str__(self):
        """Test TimelineEventObjectRef __str__()"""
        expected = 'TestProject: test_event/owner (test_name)'
        self.assertEqual(str(self.obj_ref), expected)

    def test__repr__(self):
        """Test TimelineEventObjectRef __repr__()"""
        expected = (
            "TimelineEventObjectRef('TestProject', 'test_event', "
            "'owner', 'test_name')"
        )
        self.assertEqual(repr(self.obj_ref), expected)

    def test_get_object_events(self):
        """Test get_object_events() in TimelineEventManager"""
        events = TimelineEvent.objects.get_object_events(
            project=self.project,
            object_model=self.obj_ref.object_model,
            object_uuid=self.obj_ref.object_uuid,
        )
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0], self.event)


class TestTimelineEventStatus(
    TimelineEventMixin, TimelineEventStatusMixin, TimelineEventTestBase
):
    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data=EXTRA_DATA,
        )
        self.event_status_submit = self.make_event_status(
            event=self.event,
            status_type='SUBMIT',
            description='SUBMIT',
            extra_data=EXTRA_DATA,
        )
        self.event_status_ok = self.make_event_status(
            event=self.event,
            status_type=TL_STATUS_OK,
            description=TL_STATUS_OK,
            extra_data=EXTRA_DATA,
        )

    def test_initialization(self):
        """Test TimelineEventStatus init"""
        expected = {
            'id': self.event_status_ok.pk,
            'sodar_uuid': self.event_status_ok.sodar_uuid,
            'event': self.event.pk,
            'status_type': TL_STATUS_OK,
            'description': TL_STATUS_OK,
            'extra_data': EXTRA_DATA,
        }
        self.assertEqual(model_to_dict(self.event_status_ok), expected)

    def test_initialization_no_user(self):
        """Test TimelineEventStatus without user"""
        expected = {
            'id': self.event_status_ok.pk,
            'sodar_uuid': self.event_status_ok.sodar_uuid,
            'event': self.event.pk,
            'status_type': TL_STATUS_OK,
            'description': TL_STATUS_OK,
            'extra_data': EXTRA_DATA,
        }
        self.event = self.make_event(
            project=self.project,
            app=APP_NAME_PR,
            user=None,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data=EXTRA_DATA,
        )
        self.assertEqual(model_to_dict(self.event_status_ok), expected)

    def test__str__(self):
        """Test TimelineEventStatus __str__()"""
        expected = f'TestProject: test_event/owner ({TL_STATUS_OK})'
        self.assertEqual(str(self.event_status_ok), expected)

    def test__str__no_user(self):
        """Test __str__() with no user"""
        self.event.user = None
        self.event.save()
        expected = f'TestProject: test_event ({TL_STATUS_OK})'
        self.assertEqual(str(self.event_status_ok), expected)

    def test__repr__(self):
        """Test TimelineEventStatus __repr__()"""
        expected = f"TimelineEventStatus('TestProject', 'test_event', 'owner', '{TL_STATUS_OK}')"
        self.assertEqual(repr(self.event_status_ok), expected)

    def test__repr__no_user(self):
        """Test __repr__() with no user"""
        self.event.user = None
        self.event.save()
        expected = f"TimelineEventStatus('TestProject', 'test_event', 'N/A', '{TL_STATUS_OK}')"
        self.assertEqual(repr(self.event_status_ok), expected)

    def test_get_status(self):
        """Test TimelineEventStatus get_status()"""
        status = self.event.get_status()
        expected = {
            'id': status.pk,
            'sodar_uuid': self.event_status_ok.sodar_uuid,
            'event': self.event.pk,
            'status_type': TL_STATUS_OK,
            'description': TL_STATUS_OK,
            'extra_data': EXTRA_DATA,
        }
        self.assertEqual(model_to_dict(status), expected)

    def test_get_timestamp(self):
        """Test TimelineEventStatus get_timestamp()"""
        timestamp = self.event.get_timestamp()
        self.assertEqual(timestamp, self.event_status_ok.timestamp)

    def test_get_status_changes(self):
        """Test TimelineEventStatus get_status_changes()"""
        status_changes = self.event.get_status_changes()
        self.assertEqual(status_changes.count(), 2)
        self.assertEqual(status_changes[0], self.event_status_submit)

    def test_get_status_changes_reverse(self):
        """Test the get_status_changes() function of TimelineEvent with
        reverse=True"""
        status_changes = self.event.get_status_changes(reverse=True)
        self.assertEqual(status_changes.count(), 2)
        self.assertEqual(status_changes[0], self.event_status_ok)

    def test_set_status(self):
        """Test TimelineEventStatus set_status()"""
        new_status = self.event.set_status(
            TL_STATUS_FAILED,
            status_desc=TL_STATUS_FAILED,
            extra_data=EXTRA_DATA,
        )
        expected = {
            'id': new_status.pk,
            'sodar_uuid': new_status.sodar_uuid,
            'event': self.event.pk,
            'status_type': TL_STATUS_FAILED,
            'description': TL_STATUS_FAILED,
            'extra_data': EXTRA_DATA,
        }
        self.assertEqual(model_to_dict(new_status), expected)
