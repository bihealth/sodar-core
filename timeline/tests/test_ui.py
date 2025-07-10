"""UI tests for the timeline app"""

import json

from django.urls import reverse
from django.utils.timezone import localtime
from django.test import override_settings
from urllib.parse import urlencode

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAPI
from projectroles.tests.test_ui import UITestBase

from timeline.models import TL_STATUS_OK
from timeline.tests.test_models import (
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


class TestProjectListView(
    TimelineEventMixin, TimelineEventStatusMixin, UITestBase
):
    """Tests for the timeline project list view UI"""

    def setUp(self):
        super().setUp()
        self.timeline = plugin_api.get_backend_api('timeline_backend')
        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_OK,
        )
        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data=EXTRA_DATA,
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in project event list"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 1),
            (self.user_guest, 1),
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
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 1),
            (self.user_guest, 1),
        ]
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_object(self):
        """Test visibility of object related events in project list"""
        # Add user as an object reference
        self.obj_ref = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        self.classified_obj_ref = self.classified_event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 1),
            (self.user_guest, 1),
        ]
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.obj_ref.object_model,
                'object_uuid': self.obj_ref.object_uuid,
            },
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_details(self):
        """Test visibility of events on the project details page"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 1),
            (self.user_guest, 1),
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')


class TestSiteListView(
    TimelineEventMixin, TimelineEventStatusMixin, UITestBase
):
    """Tests for the timeline site-wide list view UI"""

    def setUp(self):
        super().setUp()
        self.timeline = plugin_api.get_backend_api('timeline_backend')
        # Init default event
        self.event = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_OK,
        )
        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data=EXTRA_DATA,
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in the site-wide event list"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
        ]
        url = reverse('timeline:list_site')
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_object(self):
        """Test visibility of object related events in site-wide event list"""
        obj_ref = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        self.classified_event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
        ]
        url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': obj_ref.object_model,
                'object_uuid': obj_ref.object_uuid,
            },
        )
        self.assert_element_count(expected, url, 'sodar-tl-list-event')

    def test_render_back_button(self):
        """Test visibility of back button in object view"""
        obj_ref = self.event.add_object(
            obj=self.superuser, label='user', name=self.superuser.username
        )
        url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': obj_ref.object_model,
                'object_uuid': obj_ref.object_uuid,
            },
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-tl-back-btn')
        )


class TestAdminListView(
    TimelineEventMixin, TimelineEventStatusMixin, UITestBase
):
    """Test for the timeline view of all events in UI"""

    def setUp(self):
        super().setUp()
        self.timeline = plugin_api.get_backend_api('timeline_backend')
        self.url = reverse('timeline:list_admin')
        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_OK,
        )
        # Init default site event
        self.site_event = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='test_site_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_OK,
        )
        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data=EXTRA_DATA,
            classified=True,
        )

    def test_render(self):
        """Test visibility of events in the admin event list"""
        expected = [(self.superuser, 3)]
        self.assert_element_count(expected, self.url, 'sodar-tl-list-event')

    def test_badge(self):
        """Test visibility of badges in description of event"""
        self.login_and_redirect(
            self.superuser, self.url, wait_elem=None, wait_loc='ID'
        )
        self.assertIsNotNone(self.selenium.find_element(By.CLASS_NAME, 'badge'))


class TestModals(TimelineEventMixin, TimelineEventStatusMixin, UITestBase):
    """Test UI of modals in timeline event list"""

    def setUp(self):
        super().setUp()
        self.timeline = plugin_api.get_backend_api('timeline_backend')
        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data=json.dumps(EXTRA_DATA),
            status_type=self.timeline.TL_STATUS_OK,
        )
        self.url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )

    def test_details_modal(self):
        """Test details modal"""
        self.login_and_redirect(
            self.superuser, self.url, wait_elem=None, wait_loc='ID'
        )
        link = self.selenium.find_element(By.CLASS_NAME, 'sodar-tl-link-detail')
        link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'sodar-tl-table-detail'))
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.CLASS_NAME, 'sodar-card-table')
        )
        title = self.selenium.find_element(By.CLASS_NAME, 'modal-title')
        self.assertIn('Event Details: ', title.text)
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-event-detail-timestamp'
        )
        self.assertEqual(
            elem.text,
            localtime(self.event.get_timestamp()).strftime('%Y-%m-%d %H:%M:%S'),
        )
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-event-detail-description'
        )
        self.assertEqual(elem.text, self.event.get_status().description)
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-event-detail-status-type'
        )
        self.assertEqual(elem.text, TL_STATUS_OK)

    def test_details_modal_description_line_break(self):
        """Test details modal with line breaks in description"""
        desc = 'Test\nwith\nline breaks'
        status = self.event.get_status()
        status.description = desc
        status.save()
        self.login_and_redirect(
            self.superuser, self.url, wait_elem=None, wait_loc='ID'
        )
        link = self.selenium.find_element(By.CLASS_NAME, 'sodar-tl-link-detail')
        link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'sodar-tl-table-detail'))
        )
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-event-detail-description'
        )
        self.assertEqual(
            elem.get_attribute('innerHTML'), desc.replace('\n', '<br>')
        )

    def test_extra_data_modal(self):
        """Test extra data modal"""
        self.login_and_redirect(
            self.superuser, self.url, wait_elem=None, wait_loc='ID'
        )
        link = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-link-extra-data'
        )
        link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sodar-tl-json'))
        )
        title = self.selenium.find_element(By.CLASS_NAME, 'modal-title')
        self.assertIn('Extra', title.text)
        body = self.selenium.find_element(By.CLASS_NAME, 'modal-body')
        self.assertIn('"{"test_key": "test_val"}"', body.text)

    def test_status_extra_data_modal(self):
        """Test status extra data modal"""
        status = self.event.get_status()
        status.extra_data = {'test': 170}
        status.save()
        self.login_and_redirect(
            self.superuser, self.url, wait_elem=None, wait_loc='ID'
        )
        link = self.selenium.find_element(By.CLASS_NAME, 'sodar-tl-link-detail')
        link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'sodar-tl-link-status-extra-data')
            )
        )
        self.assertIsNotNone(
            self.selenium.find_element(
                By.CLASS_NAME, 'sodar-tl-link-status-extra-data'
            )
        )

    def test_copy_button(self):
        """Test for copy button"""
        self.login_and_redirect(
            self.superuser, self.url, wait_elem=None, wait_loc='ID'
        )
        link = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-tl-link-extra-data'
        )
        link.click()
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sodar-tl-copy-btn'))
        )
        button = self.selenium.find_element(By.CLASS_NAME, 'sodar-tl-copy-btn')
        button.click()


class TestSearch(TimelineEventMixin, TimelineEventStatusMixin, UITestBase):
    """Tests for the project search UI functionalities"""

    def setUp(self):
        super().setUp()
        self.timeline = plugin_api.get_backend_api('timeline_backend')
        # Init default event
        self.event = self.timeline.add_event(
            project=self.project,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='test_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_OK,
        )
        self.make_event_status(
            event=self.event,
            status_type=self.timeline.TL_STATUS_SUBMIT,
            description=self.timeline.TL_STATUS_SUBMIT,
            extra_data=EXTRA_DATA,
        )
        # Init default site event
        self.site_event = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='test_site_event',
            description='description',
            extra_data=EXTRA_DATA,
            status_type=self.timeline.TL_STATUS_OK,
        )
        self.make_event_status(
            event=self.site_event,
            status_type=self.timeline.TL_STATUS_SUBMIT,
            description=self.timeline.TL_STATUS_SUBMIT,
            extra_data=EXTRA_DATA,
        )
        # Init classified event
        self.classified_event = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='classified_event',
            description='description',
            extra_data=EXTRA_DATA,
            classified=True,
        )
        self.make_event_status(
            event=self.classified_event,
            status_type=self.timeline.TL_STATUS_SUBMIT,
            description=self.timeline.TL_STATUS_SUBMIT,
            extra_data=EXTRA_DATA,
        )
        self.classified_site_event = self.timeline.add_event(
            project=None,
            app_name=APP_NAME_PR,
            user=self.superuser,
            event_name='classified_site_event',
            description='description',
            extra_data=EXTRA_DATA,
            classified=True,
        )
        self.make_event_status(
            event=self.classified_site_event,
            status_type=self.timeline.TL_STATUS_SUBMIT,
            description=self.timeline.TL_STATUS_SUBMIT,
            extra_data=EXTRA_DATA,
        )

    def test_search_results(self):
        """Test search results"""
        expected = [
            (self.superuser, 4),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_viewer_cat, 1),
            (self.user_finder_cat, 1),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_viewer, 1),
            (self.user_no_roles, 1),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'description'})
        )
        for user, count in expected:
            self.login_and_redirect(user, url, wait_elem=None, wait_loc='ID')
            elements = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-project-list-item'
            )
            elem_set = set()
            for elem in elements:
                elem_set.add(elem.get_attribute('id'))
            self.assertEqual(len(elem_set), count)

    @override_settings(TIMELINE_SEARCH_LIMIT=2)
    def test_search_limit(self):
        """Test search limit"""
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'event'})
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        elements = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-project-list-item'
        )
        self.assertEqual(len(elements), 2)
