"""Tests for Ajax view permissions in the adminalerts app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.base import SiteAppPermissionTestBase

from adminalerts.tests.test_models import AdminAlertMixin


class TestAdminAlertActiveToggleAjaxView(
    AdminAlertMixin, SiteAppPermissionTestBase
):
    """Permission tests for AdminAlertActiveToggleAjaxView"""

    def setUp(self):
        super().setUp()
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )
        self.url = reverse(
            'adminalerts:ajax_active_toggle',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_post(self):
        """Test AdminAlertActiveToggleAjaxView POST"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200, method='POST')
        self.assert_response(self.url, bad_users, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self.assert_response(self.url, self.anonymous, 403, method='POST')


class TestAdminAlertDismissAjaxView(AdminAlertMixin, SiteAppPermissionTestBase):
    """Permission tests for AdminAlertDismissAjaxView"""

    def setUp(self):
        super().setUp()
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )
        self.url = reverse(
            'adminalerts:ajax_dismiss',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_get(self):
        """Test AdminAlertDismissAjaxView GET"""
        self.assert_response(
            self.url,
            [self.superuser, self.regular_user, self.anonymous],
            200,
            method='GET',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 200, method='GET')
