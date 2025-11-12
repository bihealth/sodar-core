"""Model tests for the tokens app"""

import datetime

from typing import Optional

from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict

from tokens.models import SODARAuthToken

from test_plus import TestCase


User = get_user_model()


# Local constants
TOKEN_LABEL = 'Test token label'


class SODARAuthTokenMixin:
    """Helpers for SODARAuthToken testing"""

    @classmethod
    def make_token(
        cls,
        user: User,
        label: Optional[str] = None,
        expiry: Optional[datetime] = None,
    ) -> tuple[SODARAuthToken, str]:
        """
        Create SODARAuthToken object.

        :param user: User object
        :param label: Token label (string or None, optional)
        :param expiry: Expiry date (datetime, optional)
        :return: SODARAuthToken, str
        """
        return SODARAuthToken.objects.create(
            user=user, sodar_label=label or '', expiry=expiry
        )


class TestSODARAuthToken(SODARAuthTokenMixin, TestCase):
    """Tests for the SODARAuthToken model"""

    def setUp(self):
        self.user = self.make_user('user')
        self.expiry = datetime.timedelta(hours=10)

    def test_initialization(self):
        """Test SODARAuthToken initialization"""
        instance, token = self.make_token(
            user=self.user, label=TOKEN_LABEL, expiry=self.expiry
        )
        expected = {
            'digest': instance.digest,
            'token_key': token[:15],
            'user': self.user.pk,
            'expiry': instance.expiry,
            'sodar_label': TOKEN_LABEL,
        }
        self.assertEqual(model_to_dict(instance), expected)
        self.assertIsInstance(instance.expiry, datetime.datetime)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token), 64)

    def test_initialization_no_label(self):
        """Test initialization without label"""
        instance, token = self.make_token(
            user=self.user, label=None, expiry=self.expiry
        )
        self.assertEqual(instance.sodar_label, '')

    def test_initialization_no_expiry(self):
        """Test initialization without expiry"""
        instance, token = self.make_token(
            user=self.user, label=TOKEN_LABEL, expiry=None
        )
        self.assertEqual(instance.expiry, None)

    def test_initialization_multiple(self):
        """Test initialization with multiple tokens for user"""
        self.make_token(self.user)
        instance2, token2 = self.make_token(self.user)
        self.assertIsInstance(instance2, SODARAuthToken)
        self.assertIsInstance(token2, str)
        self.assertEqual(
            SODARAuthToken.objects.filter(user=self.user).count(), 2
        )

    def test_str(self):
        """Test __str__()"""
        instance, token = self.make_token(user=self.user, label=TOKEN_LABEL)
        self.assertEqual(
            str(instance),
            f'{instance.digest} : {self.user.username} : {TOKEN_LABEL}',
        )

    def test_str_no_label(self):
        """Test __str__() without label"""
        instance, token = self.make_token(user=self.user)
        self.assertEqual(
            str(instance), f'{instance.digest} : {self.user.username}'
        )
