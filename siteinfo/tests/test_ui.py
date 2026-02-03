"""UI tests for the siteinfo app"""

from django.test import override_settings
from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from projectroles.app_settings import AppSettingAPI
from projectroles.tests.base import UITestBase


app_settings = AppSettingAPI()


class TestSiteInfoUI(UITestBase):
    """Tests for the siteinfo view UI"""

    def setUp(self):
        super().setUp()
        self.url = reverse('siteinfo:info')
        self.serverside_stats_elements = [
            'sodar-si-project-stats-card',
            'sodar-si-user-stats-card',
            'sodar-si-basic-card',
            'sodar-si-remote-card',
        ]
        self.clientside_stats_elements = [
            'sodar-si-adminalerts-app-stats-card',
            'sodar-si-example_backend_app-app-stats-card',
            'sodar-si-example_project_app-app-stats-card',
            'sodar-si-filesfolders-app-stats-card',
            'sodar-si-timeline-app-stats-card',
        ]
        self.apps_elements = [
            'sodar-si-project-apps-card',
            'sodar-si-site-apps-card',
            'sodar-si-backend-apps-card',
        ]
        self.settings_elements = [
            'sodar-si-settings-card-core',
            'sodar-si-core-settings-card-app-bgjobs',
            'sodar-si-core-settings-card-app-filesfolders',
            'sodar-si-core-settings-card-app-timeline',
            'sodar-si-core-settings-card-app-adminalerts',
            'sodar-si-core-settings-card-app-tokens',
        ]

    def test_serverside_cards(self):
        """Test that the expected cards are present"""
        self.login_and_redirect(self.superuser, self.url)
        for element_id in self.serverside_stats_elements:
            self.assertIsNotNone(self.selenium.find_element(By.ID, element_id))
            # Test that the cards have reasonable content
            children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dt'
            )
            self.assertGreater(len(children), 0)

    def test_clientside_cards(self):
        """Test that client-side cards are shown"""
        self.login_and_redirect(self.superuser, self.url)
        WebDriverWait(self.selenium, self.wait_time).until_not(
            ec.presence_of_element_located(
                (By.ID, 'sodar-si-app-stats-loading')
            )
        )
        for element_id in self.clientside_stats_elements:
            self.assertIsNotNone(self.selenium.find_element(By.ID, element_id))
            dt_children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dt'
            )
            dd_children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dd'
            )
            self.assertEqual(len(dt_children), len(dd_children))
            self.assertGreater(len(dt_children), 0)

    @override_settings(ENABLED_BACKEND_PLUGINS=[])
    def test_clientside_cards_missing_backend(self):
        """Test that backend apps are not shown"""
        expected_elements = self.clientside_stats_elements.copy()
        expected_elements.remove('sodar-si-example_backend_app-app-stats-card')
        self.assert_element_set(
            [(self.superuser, expected_elements)],
            self.clientside_stats_elements,
            self.url,
            wait_elem=expected_elements[0],
        )

    def test_apps_tab_cards(self):
        """Test the cards in the "Apps" tab"""
        self.login_and_redirect(self.superuser, self.url)
        for element_id in self.apps_elements:
            self.assertIsNotNone(self.selenium.find_element(By.ID, element_id))
            dt_children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dt'
            )
            dd_children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dd'
            )
            self.assertEqual(len(dt_children), len(dd_children))
            self.assertGreater(len(dt_children), 0)

    @override_settings(ENABLED_BACKEND_PLUGINS=[])
    def test_apps_tab_cards_missing_backend(self):
        """Test the cards in the "Apps" tab without backend apps"""
        self.login_and_redirect(self.superuser, self.url)
        backend_card_id = 'sodar-si-backend-apps-card'
        self.assertIsNotNone(self.selenium.find_element(By.ID, backend_card_id))
        dt_children = self.selenium.find_elements(
            By.CSS_SELECTOR, f'#{backend_card_id} dl.row dt'
        )
        dd_children = self.selenium.find_elements(
            By.CSS_SELECTOR, f'#{backend_card_id} dl.row dd'
        )
        self.assertEqual(len(dt_children), 0)
        self.assertEqual(len(dd_children), 0)

    def test_settings_tab_cards(self):
        """Test the cards in the "Settings" tab"""
        self.login_and_redirect(self.superuser, self.url)
        for element_id in self.settings_elements:
            self.assertIsNotNone(self.selenium.find_element(By.ID, element_id))
            dt_children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dt'
            )
            dd_children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dd'
            )
            self.assertEqual(len(dt_children), len(dd_children))
            self.assertGreater(len(dt_children), 0)
