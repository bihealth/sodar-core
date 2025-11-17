"""REST API view tests for the tokens app"""

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from test_plus.test import APITestCase

# Projectroles dependency
from projectroles.signals import ACCOUNT_LOCKED_MSG
from projectroles.tests.base import (
    SODARAPIViewTestMixin,
    AUTHENTICATION_BACKENDS_AXES,
)

from tokens.models import SODARAuthToken, TOKEN_LABEL_MAX_LENGTH
from tokens.views_api import TOKENS_API_MEDIA_TYPE, TOKENS_API_DEFAULT_VERSION


USER_NAME = 'user'
USER_PW = 'testpassword'
INVALID_PW = 'INVALID_PASSWORD'
TOKEN_LABEL = 'Test label'


class TokenCreateLoginAPIViewTestBase(SODARAPIViewTestMixin, APITestCase):
    """Base class for TokenCreateLoginAPIView tests"""

    media_type = TOKENS_API_MEDIA_TYPE
    api_version = TOKENS_API_DEFAULT_VERSION

    def _get_header(self, username: str, password: str) -> dict:
        """Return request header with basic authentication and accept header"""
        return {
            **self.get_basic_auth_header(username, password),
            **self.get_accept_header(self.media_type, self.api_version),
        }

    def setUp(self):
        self.user = self.make_user(USER_NAME, password=USER_PW)
        self.url = reverse('tokens:api_login')


class TestTokenCreateLoginAPIView(TokenCreateLoginAPIViewTestBase):
    """Tests for TokenCreateLoginAPIView"""

    def setUp(self):
        super().setUp()
        self.req_header = self._get_header(USER_NAME, USER_PW)

    def test_post(self):
        """Test TokenCreateLoginAPIView POST"""
        self.assertEqual(
            SODARAuthToken.objects.filter(user=self.user).count(), 0
        )
        response = self.client.post(self.url, **self.req_header)
        self.assertEqual(response.status_code, 201)
        tokens = SODARAuthToken.objects.filter(user=self.user)
        self.assertEqual(tokens.count(), 1)
        self.assertEqual(tokens.first().expiry, None)
        self.assertEqual(response.data['delete_count'], 0)
        self.assertEqual(response.data['expiry'], None)
        self.assertEqual(response.data['sodar_label'], '')
        self.assertEqual(len(response.data['token']), 64)
        self.assertEqual(response.data['user_uuid'], str(self.user.sodar_uuid))

    def test_post_existing(self):
        """Test POST with existing token for user"""
        token = SODARAuthToken.objects.create(user=self.user)[0]
        self.assertEqual(
            SODARAuthToken.objects.filter(user=self.user).count(), 1
        )
        response = self.client.post(self.url, **self.req_header)
        self.assertEqual(response.status_code, 201)
        # We should only have the newly created token
        self.assertEqual(
            SODARAuthToken.objects.filter(user=self.user).count(), 1
        )
        self.assertIsNone(SODARAuthToken.objects.filter(pk=token.pk).first())
        self.assertEqual(response.data['delete_count'], 1)

    def test_post_expiry(self):
        """Test POST with expiry"""
        post_data = {'expiry': 10}
        response = self.client.post(self.url, data=post_data, **self.req_header)
        self.assertEqual(response.status_code, 201)
        token = SODARAuthToken.objects.filter(user=self.user).first()
        self.assertEqual(
            token.expiry.replace(minute=0, second=0, microsecond=0),
            (timezone.now() + timezone.timedelta(hours=10)).replace(
                minute=0, second=0, microsecond=0
            ),
        )
        self.assertEqual(
            response.data['expiry'], self.get_drf_datetime(token.expiry)
        )
        self.assertEqual(response.data['user_uuid'], str(self.user.sodar_uuid))

    def test_post_label(self):
        """Test POST with label"""
        post_data = {'sodar_label': TOKEN_LABEL}
        response = self.client.post(self.url, data=post_data, **self.req_header)
        self.assertEqual(response.status_code, 201)
        token = SODARAuthToken.objects.filter(user=self.user).first()
        self.assertEqual(token.sodar_label, TOKEN_LABEL)
        self.assertEqual(response.data['sodar_label'], TOKEN_LABEL)

    def test_post_label_max_length(self):
        """Test POST with label exceeding maximum label length"""
        label = 'a' * (TOKEN_LABEL_MAX_LENGTH + 1)
        post_data = {'sodar_label': label}
        response = self.client.post(self.url, data=post_data, **self.req_header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            SODARAuthToken.objects.filter(user=self.user).count(), 0
        )


@override_settings(
    AUTHENTICATION_BACKENDS=AUTHENTICATION_BACKENDS_AXES, AXES_ENABLED=True
)
class TestTokenCreateLoginAPIViewAxes(TokenCreateLoginAPIViewTestBase):
    """Tests for TokenCreateLoginAPIView with django-axes"""

    def test_post(self):
        """Test TokenCreateLoginAPIView POST with correct credentials"""
        response = self.client.post(
            self.url, **self._get_header(USER_NAME, USER_PW)
        )
        self.assertEqual(response.status_code, 201)

    def test_post_invalid(self):
        """Test POST with invalid credentials"""
        response = self.client.post(
            self.url, **self._get_header(USER_NAME, INVALID_PW)
        )
        self.assertEqual(response.status_code, 401)

    def test_post_lock(self):
        """Test POST with axes account locking"""
        post_header = self._get_header(USER_NAME, INVALID_PW)
        for i in range(0, settings.AXES_FAILURE_LIMIT - 1):
            response = self.client.post(self.url, **post_header)
            self.assertEqual(response.status_code, 401)
            self.assertNotEqual(response.data['detail'], ACCOUNT_LOCKED_MSG)
        response = self.client.post(self.url, **post_header)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], ACCOUNT_LOCKED_MSG)
