"""Tests for Ajax views in the adminalerts app"""

import json

from django.urls import reverse

from adminalerts.tests.test_views import AdminalertsViewTestBase


class TestAdminAlertActiveToggleAjaxView(AdminalertsViewTestBase):
    """Tests for AdminAlertActiveToggleAjaxView"""

    def setUp(self):
        super().setUp()
        self.alert = self._make_alert()
        self.url = reverse(
            'adminalerts:ajax_active_toggle',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_post_deactivate(self):
        """Test AdminAlertActiveToggleAjaxView POST to deactivate alert"""
        self.assertTrue(self.alert.active)
        with self.login(self.superuser):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.alert.refresh_from_db()
        self.assertFalse(self.alert.active)
        self.assertFalse(data['is_active'])

    def test_post_activate(self):
        """Test POST to activate alert"""
        self.alert.active = False
        self.alert.save()
        with self.login(self.superuser):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.active)
        self.assertTrue(data['is_active'])
