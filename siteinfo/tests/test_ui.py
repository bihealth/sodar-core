"""UI tests for the siteinfo app"""

from django.test import override_settings
from django.urls import reverse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from adminalerts.plugins import SiteAppPlugin as AdminAlertsSitePlugin
from projectroles.app_settings import AppSettingAPI
from projectroles.tests.base import UITestBase


app_settings = AppSettingAPI()


class TestSiteInfoUI(UITestBase):
    """Tests for the siteinfo view UI"""

    def setUp(self):
        super().setUp()
        self.url = reverse('siteinfo:info')
        # Server-side stat elements which can be located "by id" in the HTML DOM
        self.server_stats_elements = [
            'sodar-si-project-stats-card',
            'sodar-si-user-stats-card',
            'sodar-si-basic-card',
            'sodar-si-remote-card',
        ]
        # Client-side stat elements which can be located with the
        # "data-plugin-name" attribute
        self.client_stats_plugins = [
            'adminalerts',
            'example_backend_app',
            'example_project_app',
            'filesfolders',
            'timeline',
        ]
        # Apps elements can be located "by id"
        self.apps_elements = [
            'sodar-si-project-apps-card',
            'sodar-si-site-apps-card',
            'sodar-si-backend-apps-card',
        ]
        # Core settings elements which can be located "by id"
        self.settings_elements = [
            'sodar-si-settings-card-core',
        ]
        # Plugin settings element can be located by "data-plugin-name" attribute
        self.settings_plugins = [
            'bgjobs',
            'filesfolders',
            'timeline',
            'adminalerts',
            'tokens',
        ]

    def test_server_cards(self):
        """Test that the expected cards are present"""
        self.login_and_redirect(self.superuser, self.url)
        for element_id in self.server_stats_elements:
            self.assertIsNotNone(self.selenium.find_element(By.ID, element_id))
            # Test that the cards have reasonable content
            children = self.selenium.find_elements(
                By.CSS_SELECTOR, f'#{element_id} dl.row dt'
            )
            self.assertGreater(len(children), 0)

    def test_client_cards(self):
        """Test that client-side cards are shown"""
        self.login_and_redirect(self.superuser, self.url)
        for plugin_name in self.client_stats_plugins:
            parent_card_element = (
                '//div[@id="nav-general"]'
                f'//div[@data-plugin-name="{plugin_name}"]'
            )
            WebDriverWait(self.selenium, self.wait_time).until(
                ec.visibility_of_element_located(
                    (By.XPATH, parent_card_element)
                )
            )
            dt_children = self.selenium.find_elements(
                By.XPATH, parent_card_element + '//dt'
            )
            dd_children = self.selenium.find_elements(
                By.XPATH, parent_card_element + '//dd'
            )
            self.assertEqual(len(dt_children), len(dd_children))
            self.assertGreater(len(dt_children), 0)

    def test_client_cards_error(self):
        """Test that client-side card errors are shown"""

        def get_statistics_error(self):
            raise ValueError('Invalid Stats')

        # Monkey-patch the get_statistics() function to trigger an error
        get_statistics_original = AdminAlertsSitePlugin.get_statistics
        AdminAlertsSitePlugin.get_statistics = get_statistics_error

        self.login_and_redirect(self.superuser, self.url)
        parent_card_element = (
            '//div[@id="nav-general"]' '//div[@data-plugin-name="adminalerts"]'
        )
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.visibility_of_element_located((By.XPATH, parent_card_element))
        )
        error_element = self.selenium.find_element(
            By.XPATH, parent_card_element + '//div[@class="card-body"]/div'
        )
        self.assertEqual(
            error_element.text,
            'Unable to retrieve app statistics: Invalid Stats',
        )

        AdminAlertsSitePlugin.get_statistics = get_statistics_original

    @override_settings(ENABLED_BACKEND_PLUGINS=[])
    def test_client_cards_missing_backend(self):
        """Test that backend apps are not shown"""
        expected_plugins = self.client_stats_plugins.copy()
        removed_plugin = 'example_backend_app'
        expected_plugins.remove(removed_plugin)
        self.login_and_redirect(self.superuser, self.url)
        for plugin_name in expected_plugins:
            parent_card_element = (
                '//div[@id="nav-general"]'
                f'//div[@data-plugin-name="{plugin_name}"]'
            )
            WebDriverWait(self.selenium, self.wait_time).until(
                ec.visibility_of_element_located(
                    (By.XPATH, parent_card_element)
                )
            )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.XPATH, f'//div[@data-plugin-name="{removed_plugin}"]'
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

        for plugin_name in self.settings_plugins:
            parent_card_element = (
                '//div[@id="nav-settings"]'
                f'//div[@data-plugin-name="{plugin_name}"]'
            )
            self.assertIsNotNone(
                self.selenium.find_element(By.XPATH, parent_card_element)
            )
            dt_children = self.selenium.find_elements(
                By.XPATH, parent_card_element + '//dt'
            )
            dd_children = self.selenium.find_elements(
                By.XPATH, parent_card_element + '//dd'
            )
            self.assertEqual(len(dt_children), len(dd_children))
            self.assertGreater(len(dt_children), 0)
