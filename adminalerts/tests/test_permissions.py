"""Test for UI view permissions in the adminalerts app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import SiteAppPermissionTestBase

from adminalerts.tests.test_models import AdminAlertMixin


class AdminalertsPermissionTestBase(AdminAlertMixin, SiteAppPermissionTestBase):
    """Base test class for adminalerts UI view permission tests"""

    def setUp(self):
        super().setUp()
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )


class TestAdminAlertListView(AdminalertsPermissionTestBase):
    """Permission tests for AdminAlertListView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('adminalerts:list')

    def test_get(self):
        """Test AdminAlertListView GET"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)


class TestAdminAlertDetailView(AdminalertsPermissionTestBase):
    """Permission tests for dminAlertDetailView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'adminalerts:detail', kwargs={'adminalert': self.alert.sodar_uuid}
        )

    def test_get(self):
        """Test AdminAlertDetailView GET"""
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)


class TestAdminAlertCreateView(AdminalertsPermissionTestBase):
    """Permission tests for AdminAlertCreateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('adminalerts:create')

    def test_get(self):
        """Test AdminAlertCreateView GET"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)


class TestAdminAlertUpdateView(AdminalertsPermissionTestBase):
    """Permission tests for AdminAlertUpdateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'adminalerts:update', kwargs={'adminalert': self.alert.sodar_uuid}
        )

    def test_get(self):
        """Test AdminAlertUpdateView GET"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)


class TestAdminAlertDeleteView(AdminalertsPermissionTestBase):
    """Permission tests for AdminAlertDeleteView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'adminalerts:delete', kwargs={'adminalert': self.alert.sodar_uuid}
        )

    def test_get(self):
        """Test AdminAlertDeleteView GET"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
