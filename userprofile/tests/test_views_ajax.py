"""Ajax API view tests for the userprofile app"""

from django.urls import reverse

from userprofile.tests.test_views import UserViewTestBase


class TestUserListAjaxView(UserViewTestBase):
    def setUp(self):
        super().setUp()
        self.regular_user = self.make_user('regular_user')
        self.other_user = self.make_user('other_user')
        self.url = reverse('userprofile:ajax_list')

    def test_get(self):
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
