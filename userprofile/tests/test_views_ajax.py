"""Ajax API view tests for the userprofile app"""

from django.urls import reverse
from django.utils.timezone import localtime

from userprofile.tests.test_views import UserViewTestBase


class TestUserListAjaxView(UserViewTestBase):
    def setUp(self):
        super().setUp()
        self.regular_user = self.make_user('regular_user')
        self.regular_user.first_name = 'Roger'
        self.regular_user.last_name = 'Larsen'
        self.regular_user.save()
        self.other_user = self.make_user('other_user')
        self.other_user.is_active = False
        self.other_user.save()
        self.url = reverse('userprofile:ajax_list')
        self.expected = [
            {
                'username': 'other_user',
                'first_name': '',
                'last_name': '',
                'email': 'other_user@example.com',
                'is_active': False,
                'date_joined': localtime(self.other_user.date_joined).strftime(
                    '%Y-%m-%d %H:%M:%S'
                ),
                'sodar_uuid': str(self.other_user.sodar_uuid),
            },
            {
                'username': 'regular_user',
                'first_name': 'Roger',
                'last_name': 'Larsen',
                'email': 'regular_user@example.com',
                'is_active': True,
                'date_joined': localtime(
                    self.regular_user.date_joined
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'sodar_uuid': str(self.regular_user.sodar_uuid),
            },
            {
                'username': 'superuser',
                'first_name': '',
                'last_name': '',
                'email': 'superuser@example.com',
                'is_active': True,
                'date_joined': localtime(self.user.date_joined).strftime(
                    '%Y-%m-%d %H:%M:%S'
                ),
                'sodar_uuid': str(self.user.sodar_uuid),
            },
        ]

    def test_get(self):
        """Test UserListAjaxView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(response.data, key=lambda x: x['username']), self.expected
        )

    def test_get_as_regular_user(self):
        """Test UserListAjaxView GET as regular user"""
        with self.login(self.regular_user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(response.data, key=lambda x: x['username']), self.expected
        )

    def test_get_as_anonymous_user(self):
        """Test UserListAjaxView GET as regular user"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
