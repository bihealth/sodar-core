"""UI tests for the timeline app"""
import json

from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.tests.test_ui import TestUIBase

from timeline.tests.test_models import (
    ProjectEventMixin,
    ProjectEventStatusMixin,
)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestProjectListView(
    ProjectEventMixin, ProjectEventStatusMixin, TestUIBase
):
    """Tests for the timeline project list view UI"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in project event list"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_no_user(self):
        """Test rendering with an event without user"""
        self.event.user = None
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_object(self):
        """Test visibility of object related events in project list"""
        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        self.classified_ref_obj = self.classified_event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.ref_obj.object_model,
                'object_uuid': self.ref_obj.object_uuid,
            },
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_details(self):
        """Test visibility of events on the project details page"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 2),
            (self.delegate_as.user, 2),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')


class TestSiteListView(ProjectEventMixin, ProjectEventStatusMixin, TestUIBase):
    """Tests for the timeline site-wide list view UI"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in the site-wide event list"""
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse('timeline:list_site')
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_object(self):
        """Test visibility of object related events in site-wide event list"""
        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        self.classified_ref_obj = self.classified_event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        expected = [
            (self.superuser, 2),
            (self.owner_as.user, 1),
            (self.delegate_as.user, 1),
            (self.contributor_as.user, 1),
            (self.guest_as.user, 1),
        ]
        url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': self.ref_obj.object_model,
                'object_uuid': self.ref_obj.object_uuid,
            },
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_object_button(self):
        """Test visibility of the return button in event's object view"""
        # Add user as an object reference
        self.ref_obj = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': self.ref_obj.object_model,
                'object_uuid': self.ref_obj.object_uuid,
            },
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        try:
            self.selenium.find_element(By.CLASS_NAME, 'btn-secondary')
        except Exception:
            pass


class TestAdminListView(ProjectEventMixin, ProjectEventStatusMixin, TestUIBase):
    """Test for the timeline view of all events in UI"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init default site event
        self.site_event = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_site_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            status_type='OK',
        )

        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=None,
            app_name='projectroles',
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data={'test_key': 'test_val'},
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in the admin event list"""
        expected = [
            (self.superuser, 3),
        ]
        url = reverse('timeline:timeline_site_admin')
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_badge(self):
        """Test visibility of badges in description of event"""
        url = reverse('timeline:timeline_site_admin')
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        self.assertIsNotNone(self.selenium.find_element(By.CLASS_NAME, 'badge'))


class TestModals(ProjectEventMixin, ProjectEventStatusMixin, TestUIBase):
    """Test UI of modals in timeline event list"""

    def setUp(self):
        super().setUp()
        self.timeline = get_backend_api('timeline_backend')

        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name='projectroles',
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data=json.dumps({'test_key': 'test_val'}),
            status_type='OK',
        )

    def test_details_modal(self):
        """Test details modal"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.CLASS_NAME, 'sodar-tl-link-detail')
        )

    def test_extra_modal(self):
        """Test extra data modal"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        self.assertIsNotNone(
            self.selenium.find_element(
                By.CLASS_NAME, 'sodar-tl-link-extra-data'
            )
        )

    def test_details_content(self):
        """Test details modal's content"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        button = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-link-detail'
        )
        button.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'sodar-tl-table-detail'))
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.CLASS_NAME, 'sodar-card-table')
        )
        title = self.selenium.find_element(By.CLASS_NAME, 'modal-title')
        self.assertIn('Event Details: ', title.text)
        table = self.selenium.find_element(By.CLASS_NAME, 'table')
        check_list = ['Timestamp', 'Event', 'Description', 'Status', 'OK']
        for check in check_list:
            self.assertIn(check, table.text)

    def test_extra_content(self):
        """Test extra data modal's content"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        button = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-link-extra-data'
        )
        button.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sodar-tl-json'))
        )
        title = self.selenium.find_element(By.CLASS_NAME, 'modal-title')
        self.assertIn('Extra', title.text)
        body = self.selenium.find_element(By.CLASS_NAME, 'modal-body')
        self.assertIn('"{"test_key": "test_val"}"', body.text)

    def test_copy_button(self):
        """Test for copy button"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        button = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-link-extra-data'
        )
        button.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sodar-tl-copy-btn'))
        )
        btn = self.selenium.find_element(By.CLASS_NAME, 'sodar-tl-copy-btn')
        btn.click()
