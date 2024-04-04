"""Tests for UI views in the adminalerts app"""

from django.urls import reverse
from django.utils import timezone

from test_plus.test import TestCase

from adminalerts.models import AdminAlert
from adminalerts.tests.test_models import AdminAlertMixin


class AdminalertsViewTestBase(AdminAlertMixin, TestCase):
    """Base class for adminalerts view testing"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        # No user
        self.anonymous = None
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
            require_auth=True,
        )
        self.expiry_str = (
            timezone.now() + timezone.timedelta(days=1)
        ).strftime('%Y-%m-%d')


class TestAdminAlertListView(AdminalertsViewTestBase):
    """Tests for AdminAlertListView"""

    def test_get(self):
        """Test AdminAlertListView GET"""
        with self.login(self.superuser):
            response = self.client.get(reverse('adminalerts:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['object_list'])
        self.assertEqual(response.context['object_list'][0].pk, self.alert.pk)


class TestAdminAlertDetailView(AdminalertsViewTestBase):
    """Tests for AdminAlertDetailView"""

    def test_get(self):
        """Test AdminAlertDetailView GET"""
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    'adminalerts:detail',
                    kwargs={'adminalert': self.alert.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.alert)


class TestAdminAlertCreateView(AdminalertsViewTestBase):
    """Tests for AdminAlertCreateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('adminalerts:create')

    def test_get(self):
        """Test AdminAlertCreateView GET"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test POST"""
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        post_data = {
            'message': 'new alert',
            'description': 'description',
            'date_expire': self.expiry_str,
            'active': 1,
            'require_auth': 1,
        }
        with self.login(self.superuser):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.assertEqual(AdminAlert.objects.all().count(), 2)

    def test_post_expired(self):
        """Test POST with old expiry date (should fail)"""
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        expiry_fail = (timezone.now() + timezone.timedelta(days=-1)).strftime(
            '%Y-%m-%d'
        )
        post_data = {
            'message': 'new alert',
            'description': 'description',
            'date_expire': expiry_fail,
            'active': 1,
            'require_auth': 1,
        }
        with self.login(self.superuser):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AdminAlert.objects.all().count(), 1)


class TestAdminAlertUpdateView(AdminalertsViewTestBase):
    """Tests for AdminAlertUpdateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'adminalerts:update',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_get(self):
        """Test AdminAlertUpdateView GET"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test POST"""
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        post_data = {
            'message': 'updated alert',
            'description': 'updated description',
            'date_expire': self.expiry_str,
            'active': '',
        }
        with self.login(self.superuser):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.message, 'updated alert')
        self.assertEqual(self.alert.description.raw, 'updated description')
        self.assertEqual(self.alert.active, False)

    def test_post_user(self):
        """Test POST by different user"""
        superuser2 = self.make_user('superuser2')
        superuser2.is_superuser = True
        superuser2.save()
        post_data = {
            'message': 'updated alert',
            'description': 'updated description',
            'date_expire': self.expiry_str,
            'active': '',
        }
        with self.login(superuser2):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.user, superuser2)


class TestAdminAlertDeleteView(AdminalertsViewTestBase):
    """Tests for AdminAlertDeleteView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'adminalerts:delete',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_get(self):
        """Test AdminAlertDeleteView GET"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test POST"""
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        with self.login(self.superuser):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.assertEqual(AdminAlert.objects.all().count(), 0)
