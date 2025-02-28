"""UI view tests for the tokens app"""

from django.contrib.messages import get_messages
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from knox.models import AuthToken

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)

from tokens.views import (
    TOKEN_CREATE_MSG,
    TOKEN_DELETE_MSG,
    TOKEN_CREATE_RESTRICT_MSG,
)


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']


class TestUserTokenListView(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, TestCase
):
    """Tests for UserTokenListView"""

    def _make_token(self):
        self.tokens = [AuthToken.objects.create(self.regular_user, None)]

    def setUp(self):
        self.regular_user = self.make_user('regular_user')
        self.url = reverse('tokens:list')

    def test_get(self):
        """Test UserTokenListView GET with token"""
        self._make_token()
        with self.login(self.regular_user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['token_create_enable'], True)
        self.assertEqual(response.context['token_create_msg'], '')

    def test_get_no_tokens(self):
        """Test GET with no tokens"""
        with self.login(self.regular_user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_get_restrict(self):
        """Test GET with restriction"""
        with self.login(self.regular_user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['token_create_enable'], False)
        self.assertEqual(
            response.context['token_create_msg'], TOKEN_CREATE_RESTRICT_MSG
        )

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_get_restrict_role(self):
        """Test GET with restriction and user with role"""
        self.init_roles()
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.regular_user, self.role_guest)
        with self.login(self.regular_user):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['token_create_enable'], True)
        self.assertEqual(response.context['token_create_msg'], '')

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_get_restrict_superuser(self):
        """Test GET with restriction as superuser"""
        superuser = self.make_user('superuser')
        superuser.is_superuser = True
        superuser.save()
        with self.login(superuser):
            response = self.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['token_create_enable'], True)
        self.assertEqual(response.context['token_create_msg'], '')


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
