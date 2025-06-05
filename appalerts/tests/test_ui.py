"""UI tests for the appalerts app"""

import time

from django.urls import reverse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.tests.test_ui import UITestBase

from appalerts.models import AppAlert
from appalerts.tests.test_models import AppAlertMixin


app_settings = AppSettingAPI()


# Local constants
APP_NAME_PR = 'projectroles'


class AlertUITestBase(AppAlertMixin, UITestBase):
    def setUp(self):
        super().setUp()
        # Create users
        self.superuser = self.make_user('superuser', superuser=True)
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        self.no_alert_user = self.make_user('no_alert_user')
        # No user
        self.anonymous = None
        # Create alerts
        self.alert = self.make_app_alert(
            user=self.regular_user, url=reverse('home')
        )
        self.alert2 = self.make_app_alert(
            user=self.regular_user, url=reverse('home')
        )


class TestAppAlertListView(AlertUITestBase):
    """Tests for AppAlertListView"""

    def _find_alert_element(self, alert: AppAlert) -> WebElement:
        """Return element for AppAlert object"""
        return self.selenium.find_element(
            By.XPATH, f'//div[@data-alert-uuid="{alert.sodar_uuid}"]'
        )

    def setUp(self):
        super().setUp()
        self.url = reverse('appalerts:list')
        self.url_dismiss = reverse('appalerts:list_dismissed')

    def test_render(self):
        """Test existence of alert items in list"""
        expected = [
            (self.superuser, 0),
            (self.regular_user, 2),
            (self.no_alert_user, 0),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-app-alert-item', 'class'
        )

    def test_render_links(self):
        """Test rendering alert dismiss links"""
        self.login_and_redirect(self.regular_user, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-ap-ops-dismiss-all')
        self.assertIsNone(elem.get_attribute('disabled'))
        elem = self.selenium.find_element(By.CLASS_NAME, 'sodar-ap-btn-link')
        self.assertIsNone(elem.get_attribute('disabled'))
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-ap-btn-dismiss-single'
        )
        self.assertIsNone(elem.get_attribute('disabled'))

    def test_render_links_read_only(self):
        """Test rendering alert dismiss links with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        self.login_and_redirect(self.regular_user, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-ap-ops-dismiss-all')
        self.assertEqual(elem.get_attribute('disabled'), 'true')
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.CLASS_NAME, 'sodar-ap-btn-link')
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.CLASS_NAME, 'sodar-ap-btn-dismiss-single'
            )

    def test_render_links_read_only_superuser(self):
        """Test rendering links with site read-only mode as superuser"""
        self.alert.user = self.superuser
        self.alert.save()
        self.alert2.user = self.superuser
        self.alert2.save()
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-ap-ops-dismiss-all')
        self.assertIsNone(elem.get_attribute('disabled'))
        elem = self.selenium.find_element(By.CLASS_NAME, 'sodar-ap-btn-link')
        self.assertIsNone(elem.get_attribute('disabled'))
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-ap-btn-dismiss-single'
        )
        self.assertIsNone(elem.get_attribute('disabled'))

    def test_render_dismissed(self):
        """Test displaying dismissed alerts"""
        self.alert.active = False
        self.alert.save()
        self.alert2.active = False
        self.alert2.save()
        self.login_and_redirect(self.regular_user, self.url_dismiss)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-ap-btn-active')
        )
        self.assertIsNotNone(self._find_alert_element(self.alert))
        self.assertIsNotNone(self._find_alert_element(self.alert2))

    def test_render_dismissed_project(self):
        """Test displaying dismissed alerts with project"""
        self.make_assignment(
            self.project, self.regular_user, self.role_contributor
        )
        self.alert.project = self.project
        self.alert.active = False
        self.alert.save()
        self.login_and_redirect(self.regular_user, self.url_dismiss)
        alert_cat = self._find_alert_element(self.alert)
        self.assertIn('alert-info', alert_cat.get_attribute('class'))

    def test_render_dismissed_project_no_role(self):
        """Test displaying dismissed alerts with project and no access"""
        # No role assignment created
        self.alert.project = self.project
        self.alert.active = False
        self.alert.save()
        self.login_and_redirect(self.regular_user, self.url_dismiss)
        alert_cat = self._find_alert_element(self.alert)
        self.assertIn('alert-secondary', alert_cat.get_attribute('class'))

    def test_alert_dismiss(self):
        """Test dismissing alert"""
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 2)
        self.login_and_redirect(self.regular_user, self.url)
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, '2'
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            'alerts',
        )

        button = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-ap-btn-dismiss-single'
        )[0]
        button.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located(
                (By.CLASS_NAME, 'sodar-app-alert-item')
            )
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, '1'
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            'alert',
        )
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 1)
        self.assertFalse(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-empty'
            ).is_displayed()
        )

    def test_alert_dismiss_all(self):
        """Test dismissing all alerts for user"""
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 2)
        self.login_and_redirect(self.regular_user, self.url)
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, '2'
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            'alerts',
        )

        self.selenium.find_element(By.ID, 'sodar-ap-ops-dropdown').click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.element_to_be_clickable((By.ID, 'sodar-ap-ops-dismiss-all'))
        )
        self.selenium.find_element(By.ID, 'sodar-ap-ops-dismiss-all').click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located(
                (By.CLASS_NAME, 'sodar-app-alert-item')
            )
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-count').text, ''
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'sodar-app-alert-legend').text,
            '',
        )
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 0)
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.visibility_of_element_located((By.ID, 'sodar-app-alert-empty'))
        )
        self.assertTrue(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-empty'
            ).is_displayed()
        )

    def test_alert_reload(self):
        """Test displaying reload link for new alerts"""
        AppAlert.objects.filter(active=True).delete()
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 0)
        self.login_and_redirect(self.regular_user, self.url)
        self.assertTrue(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-empty'
            ).is_displayed()
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-app-alert-reload')

        self.make_app_alert(user=self.regular_user, url=reverse('home'))

        WebDriverWait(self.selenium, self.wait_time).until(
            ec.visibility_of_element_located((By.ID, 'sodar-app-alert-reload'))
        )
        self.assertTrue(
            self.selenium.find_element(
                By.ID, 'sodar-app-alert-reload'
            ).is_displayed()
        )


class TestTitlebarBadge(AlertUITestBase):
    """Tests for the site titlebar badge"""

    def setUp(self):
        super().setUp()
        self.url = reverse('home')

    def test_render(self):
        """Test existence of alert badge for user with alerts"""
        self.login_and_redirect(self.regular_user, self.url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertIsNotNone(alert_badge)
        self.assertTrue(alert_badge.is_displayed())
        alert_link = self.selenium.find_element(
            By.ID, 'sodar-app-alert-badge-dismiss'
        )
        self.assertIsNotNone(alert_link)
        self.assertTrue(alert_link.is_displayed())
        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '2')
        self.assertEqual(alert_legend.text, 'alerts')

    def test_render_no_alerts(self):
        """Test existence of alert badge for user without alerts"""
        self.login_and_redirect(self.no_alert_user, self.url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertIsNotNone(alert_badge)
        self.assertFalse(alert_badge.is_displayed())

    def test_render_add(self):
        """Test adding an alert for user with alerts"""
        self.login_and_redirect(self.regular_user, self.url)
        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '2')
        self.assertEqual(alert_legend.text, 'alerts')

        self.make_app_alert(user=self.regular_user, url=reverse('home'))
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element(
                (By.ID, 'sodar-app-alert-count'), '3'
            )
        )
        self.assertEqual(alert_count.text, '3')
        self.assertEqual(alert_legend.text, 'alerts')

    def test_render_delete(self):
        """Test deleting an alert from user with alerts"""
        self.login_and_redirect(self.regular_user, self.url)
        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '2')
        self.assertEqual(alert_legend.text, 'alerts')

        self.alert2.delete()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element(
                (By.ID, 'sodar-app-alert-count'), '1'
            )
        )
        self.assertEqual(alert_count.text, '1')
        self.assertEqual(alert_legend.text, 'alert')

    def test_render_delete_all(self):
        """Test deleting all alerts from user with alerts"""
        self.login_and_redirect(self.regular_user, self.url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertTrue(alert_badge.is_displayed())

        self.alert.delete()
        self.alert2.delete()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located((By.ID, 'sodar-app-alert-badge'))
        )
        self.assertFalse(alert_badge.is_displayed())

    def test_render_add_no_alerts(self):
        """Test adding an alert for user without prior alerts"""
        self.login_and_redirect(self.no_alert_user, self.url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertFalse(alert_badge.is_displayed())

        self.make_app_alert(user=self.no_alert_user, url=reverse('home'))
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.visibility_of_element_located((By.ID, 'sodar-app-alert-badge'))
        )
        self.assertTrue(alert_badge.is_displayed())

        alert_count = self.selenium.find_element(By.ID, 'sodar-app-alert-count')
        alert_legend = self.selenium.find_element(
            By.ID, 'sodar-app-alert-legend'
        )
        self.assertEqual(alert_count.text, '1')
        self.assertEqual(alert_legend.text, 'alert')

    def test_alert_dismiss_all(self):
        """Test dismissing all alerts for the user"""
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 2)
        self.login_and_redirect(self.regular_user, self.url)
        self.selenium.find_element(
            By.ID, 'sodar-app-alert-badge-dismiss'
        ).click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.invisibility_of_element_located(
                (By.CLASS_NAME, 'sodar-app-alert-legend')
            )
        )
        time.sleep(2)  # HACK: Timing issue, must wait just in case
        self.assertEqual(AppAlert.objects.filter(active=True).count(), 0)

    def test_render_read_only(self):
        """Test rendering alert badge with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        self.login_and_redirect(self.regular_user, self.url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertIsNotNone(alert_badge)
        self.assertTrue(alert_badge.is_displayed())
        # Link should not be displayed
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-app-alert-badge-dismiss')

    def test_render_read_only_superuser(self):
        """Test rendering alert badge with site read-only mode as superuser"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        self.alert.user = self.superuser
        self.alert.save()
        self.login_and_redirect(self.superuser, self.url)
        alert_badge = self.selenium.find_element(By.ID, 'sodar-app-alert-badge')
        self.assertIsNotNone(alert_badge)
        self.assertTrue(alert_badge.is_displayed())
        alert_link = self.selenium.find_element(
            By.ID, 'sodar-app-alert-badge-dismiss'
        )
        self.assertIsNotNone(alert_link)
