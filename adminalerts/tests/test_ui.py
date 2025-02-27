"""UI tests for the adminalerts app"""

from django.urls import reverse
from django.utils import timezone

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

# Projectroles dependency
from projectroles.tests.test_ui import UITestBase

from adminalerts.tests.test_models import AdminAlertMixin


class AdminAlertUITestBase(AdminAlertMixin, UITestBase):
    def setUp(self):
        super().setUp()
        # Create users
        self.superuser = self.make_user('superuser', True)
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user', False)
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )


class TestAlertMessage(AdminAlertUITestBase):
    """Tests for the admin alert message"""

    def setUp(self):
        super().setUp()
        self.url = reverse('home')

    def test_message(self):
        """Test visibility of alert message in home view"""
        expected = [(self.superuser, 1), (self.regular_user, 1)]
        self.assert_element_count(
            expected, self.url, 'sodar-alert-site-app', 'class'
        )
        self.assert_element_count(
            expected, self.url, 'sodar-alert-full-text-link', 'class'
        )
        self.assert_element_count(
            expected, self.url, 'sodar-alert-detail-link', 'class'
        )

    def test_message_no_description(self):
        """Test alert message without description"""
        self.alert.description = ''
        self.alert.save()
        expected = [(self.superuser, 1), (self.regular_user, 1)]
        self.assert_element_count(
            expected, self.url, 'sodar-alert-site-app', 'class'
        )
        expected = [(self.superuser, 0), (self.regular_user, 0)]
        self.assert_element_count(
            expected, self.url, 'sodar-alert-full-text-link', 'class'
        )
        self.assert_element_count(
            expected, self.url, 'sodar-alert-detail-link', 'class'
        )

    def test_message_inactive(self):
        """Test visibility of inactive alert message"""
        self.alert.active = 0
        self.alert.save()
        expected = [(self.superuser, 0), (self.regular_user, 0)]
        self.assert_element_count(
            expected, self.url, 'sodar-alert-site-app', 'class'
        )

    def test_message_expired(self):
        """Test visibility of expired alert message"""
        self.alert.date_expire = timezone.now() - timezone.timedelta(days=1)
        self.alert.save()
        expected = [(self.superuser, 0), (self.regular_user, 0)]
        self.assert_element_count(
            expected, self.url, 'sodar-alert-site-app', 'class'
        )

    def test_message_login(self):
        """Test visibility of alert in login view with auth requirement"""
        self.selenium.get(self.build_selenium_url(reverse('login')))
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.CLASS_NAME, 'sodar-alert-site-app')

    def test_message_login_no_auth(self):
        """Test visibility of alert in login view without auth requirement"""
        self.alert.require_auth = False
        self.alert.save()
        self.selenium.get(self.build_selenium_url(reverse('login')))
        self.assertIsNotNone(
            self.selenium.find_element(By.CLASS_NAME, 'sodar-alert-site-app')
        )


class TestAdminAlertListView(AdminAlertUITestBase):
    """Tests for AdminAlertListView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('adminalerts:list')

    def test_list_items(self):
        """Test existence of items in list"""
        expected = [(self.superuser, 1)]
        self.assert_element_count(
            expected, self.url, 'sodar-aa-alert-item', 'id'
        )

    def test_list_dropdown(self):
        """Test existence of alert dropdown in list"""
        expected = [(self.superuser, 1)]
        self.assert_element_count(
            expected, self.url, 'sodar-aa-alert-dropdown', 'class'
        )
