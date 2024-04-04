"""UI view tests for the tokens app"""

from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from knox.models import AuthToken

from test_plus.test import TestCase

from tokens.views import TOKEN_CREATE_MSG, TOKEN_DELETE_MSG


class TestUserTokenListView(TestCase):
    """Tests for UserTokenListView"""

    def _make_token(self):
        self.tokens = [AuthToken.objects.create(self.user, None)]

    def setUp(self):
        self.user = self.make_user()
        self.url = reverse('tokens:list')

    def test_get(self):
        """Test UserTokenListView GET with a token"""
        self._make_token()
        with self.login(self.user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_get_no_tokens(self):
        """Test GET with no tokens"""
        with self.login(self.user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)


class TestUserTokenCreateView(TestCase):
    """Tests for UserTokenCreateView"""

    def setUp(self):
        self.user = self.make_user()
        self.url = reverse('tokens:create')

    def test_get(self):
        """Test UserTokenCreateView GET"""
        with self.login(self.user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])

    def test_post_no_ttl(self):
        """Test POST with TTL=0"""
        self.assertEqual(AuthToken.objects.count(), 0)
        with self.login(self.user):
            response = self.post(self.url, data={'ttl': 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            TOKEN_CREATE_MSG,
        )
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(AuthToken.objects.first().expiry, None)

    def test_post_ttl(self):
        """Test POST with TTL != 0"""
        self.assertEqual(AuthToken.objects.count(), 0)
        with self.login(self.user):
            response = self.post(self.url, data={'ttl': 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            TOKEN_CREATE_MSG,
        )
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(
            AuthToken.objects.first().expiry.replace(
                minute=0, second=0, microsecond=0
            ),
            (timezone.now() + timezone.timedelta(hours=10)).replace(
                minute=0, second=0, microsecond=0
            ),
        )


class TestUserTokenDeleteView(TestCase):
    """Tests for UserTokenDeleteView"""

    def setUp(self):
        self.user = self.make_user()
        self.token = AuthToken.objects.create(user=self.user)[0]
        self.url = reverse('tokens:delete', kwargs={'pk': self.token.pk})

    def test_get(self):
        """Test UserTokenDeleteView GET"""
        with self.login(self.user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test token deletion"""
        self.assertEqual(AuthToken.objects.count(), 1)
        with self.login(self.user):
            response = self.post(self.url)
            self.assertRedirects(
                response, reverse('tokens:list'), fetch_redirect_response=False
            )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            TOKEN_DELETE_MSG,
        )
        self.assertEqual(AuthToken.objects.count(), 0)
