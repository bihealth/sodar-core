"""Permission tests for the adminalerts app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestSiteAppPermissionBase

from adminalerts.tests.test_models import AdminAlertMixin


class TestAdminAlertPermissions(AdminAlertMixin, TestSiteAppPermissionBase):
    """Tests for AdminAlert permissions"""

    def setUp(self):
        super().setUp()
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )

    def test_alert_list(self):
        """Test permissions for AdminAlert list"""
        url = reverse('adminalerts:list')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_alert_list_anon(self):
        """Test permissions for AdminAlert list with anonymous access"""
        url = reverse('adminalerts:list')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_detail(self):
        """Test permissions for AdminAlert details"""
        url = reverse(
            'adminalerts:detail', kwargs={'adminalert': self.alert.sodar_uuid}
        )
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_alert_detail_anon(self):
        """Test permissions for AdminAlert details with anonymous access"""
        url = reverse(
            'adminalerts:detail', kwargs={'adminalert': self.alert.sodar_uuid}
        )
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_create(self):
        """Test permissions for AdminAlert creation"""
        url = reverse('adminalerts:create')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_alert_create_anon(self):
        """Test permissions for AdminAlert creation with anonymous access"""
        url = reverse('adminalerts:create')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_update(self):
        """Test permissions for AdminAlert updating"""
        url = reverse(
            'adminalerts:update', kwargs={'adminalert': self.alert.sodar_uuid}
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_alert_update_anon(self):
        """Test permissions for AdminAlert updating with anonymous access"""
        url = reverse(
            'adminalerts:update', kwargs={'adminalert': self.alert.sodar_uuid}
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_alert_delete(self):
        """Test permissions for AdminAlert deletion"""
        url = reverse(
            'adminalerts:delete', kwargs={'adminalert': self.alert.sodar_uuid}
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_alert_delete_anon(self):
        """Test permissions for AdminAlert deletion with anonymous access"""
        url = reverse(
            'adminalerts:delete', kwargs={'adminalert': self.alert.sodar_uuid}
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
