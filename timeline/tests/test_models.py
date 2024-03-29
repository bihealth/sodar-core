"""Model tests for the timeline app"""

from test_plus.test import TestCase

from django.forms.models import model_to_dict

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)

from timeline.models import (
    ProjectEvent,
    ProjectEventObjectRef,
    ProjectEventStatus,
    OBJ_REF_UNNAMED,
)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class ProjectEventMixin:
    """Helper mixin for ProjectEvent creation"""

    @classmethod
    def make_event(
        cls,
        project,
        app,
        user,
        event_name,
        description='',
        classified=False,
        extra_data={'test': 'test'},
        plugin=None,
    ):
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
        result = ProjectEvent(**values)
        result.save()
        return result


class ProjectEventObjectRefMixin:
    """Helper mixin for ProjectEventObjectRef creation"""

    @classmethod
    def make_object_ref(cls, event, obj, label, name, uuid, extra_data=None):
        values = {
            'event': event,
            'label': label,
            'name': name,
            'object_model': obj.__class__.__name__,
            'object_uuid': uuid,
            'extra_data': extra_data or {},
        }
        result = ProjectEventObjectRef(**values)
        result.save()
        return result


class ProjectEventStatusMixin:
    """Helper mixin for ProjectEventStatus creation"""

    @classmethod
    def make_event_status(
        cls, event, status_type, description='', extra_data=None
    ):
        values = {
            'event': event,
            'status_type': status_type,
            'description': description,
            'extra_data': extra_data or {'test': 'test'},
        }
        result = ProjectEventStatus(**values)
        result.save()
        return result


class TestProjectEventBase(
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


class TestProjectEvent(
    ProjectEventMixin,
    ProjectEventStatusMixin,
    TestProjectEventBase,
    ProjectEventObjectRefMixin,
):
    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )

        self.obj_ref = self.make_object_ref(
            event=self.event,
            obj=self.assignment_owner,
            label='test_label',
            name='test_object_name',
            uuid=self.assignment_owner.sodar_uuid,
            extra_data={'test_key': 'test_val'},
        )

    def test_initialization(self):
        """Test ProjectEvent initialization"""
        expected = {
            'id': self.event.pk,
            'project': self.project.pk,
            'app': 'projectroles',
            'plugin': None,
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': {'test_key': 'test_val'},
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_initialization_no_project(self):
        """Test ProjectEvent initialization with no project"""
        self.event = self.make_event(
            project=None,
            app='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )
        expected = {
            'id': self.event.pk,
            'project': None,
            'app': 'projectroles',
            'plugin': None,
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': {'test_key': 'test_val'},
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_initialization_no_user(self):
        """Test ProjectEvent initialization with no user"""
        self.event = self.make_event(
            project=self.project,
            app='projectroles',
            user=None,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )
        expected = {
            'id': self.event.pk,
            'project': self.project.pk,
            'app': 'projectroles',
            'plugin': None,
            'user': None,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': {'test_key': 'test_val'},
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_initialization_plugin(self):
        """Test ProjectEvent initialization with specific plugin name"""
        self.event = self.make_event(
            project=None,
            app='projectroles',
            plugin='plugin_name',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )
        expected = {
            'id': self.event.pk,
            'project': None,
            'app': 'projectroles',
            'plugin': 'plugin_name',
            'user': self.user_owner.pk,
            'event_name': 'test_event',
            'description': 'description',
            'classified': False,
            'extra_data': {'test_key': 'test_val'},
            'sodar_uuid': self.event.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.event), expected)

    def test_str(self):
        """Test ProjectEvent __str__()"""
        expected = 'TestProject: test_event/owner'
        self.assertEqual(str(self.event), expected)

    def test_str_no_user(self):
        """Test ProjectEvent __str__() with no user"""
        self.event.user = None
        self.event.save()
        expected = 'TestProject: test_event'
        self.assertEqual(str(self.event), expected)

    def test_str_no_project(self):
        """Test ProjectEvent __str__() with no project"""
        self.event.project = None
        self.event.save()
        expected = 'test_event/owner'
        self.assertEqual(str(self.event), expected)

    def test_str_no_project_no_user(self):
        """Test ProjectEvent __str__() with no project or user"""
        self.event.project = None
        self.event.user = None
        self.event.save()
        expected = 'test_event'
        self.assertEqual(str(self.event), expected)

    def test_repr(self):
        """Test ProjectEventStatus __repr__()"""
        expected = "ProjectEvent('TestProject', 'test_event', 'owner')"
        self.assertEqual(repr(self.event), expected)

    def test_repr_no_user(self):
        """Test ProjectEventStatus __repr__() with no user"""
        self.event.user = None
        self.event.save()
        expected = "ProjectEvent('TestProject', 'test_event', 'N/A')"
        self.assertEqual(repr(self.event), expected)

    def test_repr_no_project(self):
        """Test ProjectEventStatus __repr__() with no project"""
        self.event.project = None
        self.event.save()
        expected = "ProjectEvent('N/A', 'test_event', 'owner')"
        self.assertEqual(repr(self.event), expected)

    def test_repr_no_project_no_user(self):
        """Test ProjectEventStatus __repr__() with no project or user"""
        self.event.project = None
        self.event.user = None
        self.event.save()
        expected = "ProjectEvent('N/A', 'test_event', 'N/A')"
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
        }
        self.assertEqual(model_to_dict(new_obj), expected)

    def test_add_object_no_name(self):
        """Test add_object() with no name for object"""
        new_user = self.make_user('new_user')
        new_as = self.make_assignment(
            self.project, new_user, self.role_delegate
        )
        new_obj = self.event.add_object(obj=new_as, label='new_label', name='')
        self.assertEqual(new_obj.name, OBJ_REF_UNNAMED)

    def test_find_name(self):
        """Test ProjectEvent.find() with event name"""
        objects = ProjectEvent.objects.find(['test_event'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_description(self):
        """Test ProjectEvent.find() with event description"""
        objects = ProjectEvent.objects.find(['description'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_object(self):
        """Test ProjectEvent.find() with object reference"""
        objects = ProjectEvent.objects.find(['test_object_name'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.event)

    def test_find_fail(self):
        """Test ProjectEvent.find() with no matches"""
        objects = ProjectEvent.objects.find(['asdfasdfafasdf'])
        self.assertEqual(len(objects), 0)


class TestProjectEventObjectRef(
    ProjectEventMixin, ProjectEventObjectRefMixin, TestProjectEventBase
):
    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )
        self.obj_ref = self.make_object_ref(
            event=self.event,
            obj=self.assignment_owner,
            label='test_label',
            name='test_name',
            uuid=self.assignment_owner.sodar_uuid,
            extra_data={'test_key': 'test_val'},
        )

    def test_initialization(self):
        """Test ProjectEventObject initialization"""
        expected = {
            'id': self.obj_ref.pk,
            'event': self.event.pk,
            'label': 'test_label',
            'name': 'test_name',
            'object_model': 'RoleAssignment',
            'object_uuid': self.assignment_owner.sodar_uuid,
            'extra_data': {'test_key': 'test_val'},
        }
        self.assertEqual(model_to_dict(self.obj_ref), expected)

    def test__str__(self):
        """Test ProjectEventObject __str__()"""
        expected = 'TestProject: test_event/owner (test_name)'
        self.assertEqual(str(self.obj_ref), expected)

    def test__repr__(self):
        """Test ProjectEventObject __repr__()"""
        expected = (
            "ProjectEventObjectRef('TestProject', 'test_event', "
            "'owner', 'test_name')"
        )
        self.assertEqual(repr(self.obj_ref), expected)

    def test_get_object_events(self):
        """Test get_object_events() in ProjectEventManager"""
        events = ProjectEvent.objects.get_object_events(
            project=self.project,
            object_model=self.obj_ref.object_model,
            object_uuid=self.obj_ref.object_uuid,
        )
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0], self.event)


class TestProjectEventStatus(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectEventBase
):
    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app='projectroles',
            user=self.user_owner,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )
        self.event_status_submit = self.make_event_status(
            event=self.event,
            status_type='SUBMIT',
            description='SUBMIT',
            extra_data={'test_key': 'test_val'},
        )
        self.event_status_ok = self.make_event_status(
            event=self.event,
            status_type='OK',
            description='OK',
            extra_data={'test_key': 'test_val'},
        )

    def test_initialization(self):
        """Test ProjectEventStatus init"""
        expected = {
            'id': self.event_status_ok.pk,
            'sodar_uuid': self.event_status_ok.sodar_uuid,
            'event': self.event.pk,
            'status_type': 'OK',
            'description': 'OK',
            'extra_data': {'test_key': 'test_val'},
        }
        self.assertEqual(model_to_dict(self.event_status_ok), expected)

    def test_initialization_no_user(self):
        """Test ProjectEventStatus without user"""
        expected = {
            'id': self.event_status_ok.pk,
            'sodar_uuid': self.event_status_ok.sodar_uuid,
            'event': self.event.pk,
            'status_type': 'OK',
            'description': 'OK',
            'extra_data': {'test_key': 'test_val'},
        }
        self.event = self.make_event(
            project=self.project,
            app='projectroles',
            user=None,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )
        self.assertEqual(model_to_dict(self.event_status_ok), expected)

    def test__str__(self):
        """Test ProjectEventStatus __str__()"""
        expected = 'TestProject: test_event/owner (OK)'
        self.assertEqual(str(self.event_status_ok), expected)

    def test__str__no_user(self):
        """Test __str__() with no user"""
        self.event.user = None
        self.event.save()
        expected = 'TestProject: test_event (OK)'
        self.assertEqual(str(self.event_status_ok), expected)

    def test__repr__(self):
        """Test ProjectEventStatus __repr__()"""
        expected = (
            "ProjectEventStatus('TestProject', 'test_event', 'owner', 'OK')"
        )
        self.assertEqual(repr(self.event_status_ok), expected)

    def test__repr__no_user(self):
        """Test __repr__() with no user"""
        self.event.user = None
        self.event.save()
        expected = (
            "ProjectEventStatus('TestProject', 'test_event', 'N/A', 'OK')"
        )
        self.assertEqual(repr(self.event_status_ok), expected)

    def test_get_status(self):
        """Test the get_status() function of ProjectEvent"""
        status = self.event.get_status()
        expected = {
            'id': status.pk,
            'sodar_uuid': self.event_status_ok.sodar_uuid,
            'event': self.event.pk,
            'status_type': 'OK',
            'description': 'OK',
            'extra_data': {'test_key': 'test_val'},
        }
        self.assertEqual(model_to_dict(status), expected)

    def test_get_timestamp(self):
        """Test the get_timestamp() function of ProjectEvent"""
        timestamp = self.event.get_timestamp()
        self.assertEqual(timestamp, self.event_status_ok.timestamp)

    def test_get_status_changes(self):
        """Test the get_status_changes() function of ProjectEvent"""
        status_changes = self.event.get_status_changes()
        self.assertEqual(status_changes.count(), 2)
        self.assertEqual(status_changes[0], self.event_status_submit)

    def test_get_status_changes_reverse(self):
        """Test the get_status_changes() function of ProjectEvent with
        reverse=True"""
        status_changes = self.event.get_status_changes(reverse=True)
        self.assertEqual(status_changes.count(), 2)
        self.assertEqual(status_changes[0], self.event_status_ok)

    def test_set_status(self):
        """Test the set_status() function of ProjectEvent"""
        new_status = self.event.set_status(
            'FAILED', status_desc='FAILED', extra_data={'test_key': 'test_val'}
        )
        expected = {
            'id': new_status.pk,
            'sodar_uuid': new_status.sodar_uuid,
            'event': self.event.pk,
            'status_type': 'FAILED',
            'description': 'FAILED',
            'extra_data': {'test_key': 'test_val'},
        }
        self.assertEqual(model_to_dict(new_status), expected)
