"""Tests for Ajax views in the adminalerts app"""

import json

from django.urls import reverse

from adminalerts.models import AdminAlertDismissal
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


class TestAdminAlertDismissAjaxView(AdminalertsViewTestBase):
    """Tests for AdminAlertDismissAjaxView"""

    def setUp(self):
        super().setUp()
        self.alert = self._make_alert()
        self.url = reverse(
            'adminalerts:ajax_dismiss',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_get(self):
        """Test TestAdminAlertDismissAjaxView GET to dismiss alert"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            dismissal_objects = AdminAlertDismissal.objects.all()
            self.assertEqual(len(dismissal_objects), 1)
            self.assertEqual(dismissal_objects.first().user, self.superuser)

        with self.login(self.user_regular):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                AdminAlertDismissal.objects.filter(
                    user=self.user_regular
                ).count(),
                1,
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AdminAlertDismissal.objects.count(), 2)
