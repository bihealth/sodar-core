"""Test for view permissions in the appalerts app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import SiteAppPermissionTestBase

from appalerts.tests.test_models import AppAlertMixin


class AppalertsPermissionTestBase(AppAlertMixin, SiteAppPermissionTestBase):
    """Base test class for appalerts view permission tests"""

    def setUp(self):
        super().setUp()
        # Create user with no alerts
        self.no_alert_user = self.make_user('no_alert_user')
        # Create alert
        self.alert = self.make_app_alert(
            user=self.regular_user, url=reverse('home')
        )


class TestAppAlertListView(AppalertsPermissionTestBase):
    """Permission tests for AppAlertListView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('appalerts:list')

    def test_get(self):
        """Test AppAlertListView GET"""
        good_users = [
            self.superuser,
            self.regular_user,
            self.no_alert_user,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 302)


class TestAppAlertRedirectView(AppalertsPermissionTestBase):
    """Permission tests for AppAlertLinkRedirectView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'appalerts:redirect', kwargs={'appalert': self.alert.sodar_uuid}
        )
        self.bad_redirect_url = reverse('appalerts:list')

    def test_get(self):
        """Test AppAlertLinkRedirectView GET"""
        good_users = [self.regular_user]
        bad_users = [self.superuser, self.no_alert_user, self.anonymous]
        self.assert_response(
            self.url, good_users, 302, redirect_user=reverse('home')
        )
        self.assert_response(
            self.url, bad_users, 302, redirect_user=self.bad_redirect_url
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(
            self.url, self.anonymous, 302, redirect_user=self.bad_redirect_url
        )


class TestAppAlertStatusAjaxView(AppalertsPermissionTestBase):
    """Permission tests for AppAlertStatusAjaxView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('appalerts:ajax_status')

    def test_get(self):
        """Test AppAlertStatusAjaxView GET"""
        good_users = [self.superuser, self.regular_user, self.no_alert_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 403)


class TestAppAlertDismissAjaxView(AppalertsPermissionTestBase):
    """Permission tests for AppAlertDismissAjaxView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'appalerts:ajax_dismiss', kwargs={'appalert': self.alert.sodar_uuid}
        )

    def test_post(self):
        """Test AppAlertDismissAjaxView POST"""
        good_users = [self.regular_user]
        bad_users = [self.superuser, self.no_alert_user]
        self.assert_response(self.url, good_users, 200, method='POST')
        self.assert_response(self.url, bad_users, 404, method='POST')
        self.assert_response(self.url, self.anonymous, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self.assert_response(self.url, self.anonymous, 403, method='POST')
