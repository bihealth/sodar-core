"""Tests for template tags in the appalerts app"""

from django.contrib.auth import get_user_model

from test_plus.test import TestCase

from appalerts.templatetags import appalerts_tags as tags
from appalerts.tests.test_models import AppAlertMixin


User = get_user_model()


# Local constants
ALERT_MSG = 'Test message'


class TestAppAlertsTags(AppAlertMixin, TestCase):
    """Tests for appalerts template tags"""

    def setUp(self):
        self.user = self.make_user('user')
        self.alert = self.make_app_alert(user=self.user, message=ALERT_MSG)

    def test_get_alert_message(self):
        """Test get_alert_message() with basic message"""
        self.assertEqual(tags.get_alert_message(self.alert), ALERT_MSG)

    def test_get_alert_message_line_break(self):
        """Test get_alert_message() with message containing line break"""
        self.alert.message = 'Test\nmessage'
        self.assertEqual(
            tags.get_alert_message(self.alert), '<br />Test<br />message'
        )
