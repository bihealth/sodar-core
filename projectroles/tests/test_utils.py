"""Utils tests for the projectroles app"""

import re

from django.conf import settings
from django.test import override_settings

from test_plus import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.utils import get_display_name, build_secret, get_app_names


app_settings = AppSettingAPI()


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
CONSTANTS_OVERRIDE = {
    'DISPLAY_NAMES': {
        'CATEGORY': {'default': 'bar', 'plural': 'bars'},
        'PROJECT': {'default': 'foo', 'plural': 'foos'},
    }
}


class TestUtils(TestCase):
    """Tests for general utilities"""

    def test_get_display_name(self):
        """Test get_display_name()"""
        self.assertEqual(get_display_name(PROJECT_TYPE_PROJECT), 'project')
        self.assertEqual(
            get_display_name(PROJECT_TYPE_PROJECT, title=True), 'Project'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_PROJECT, count=3), 'projects'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_PROJECT, title=True, count=3),
            'Projects',
        )
        self.assertEqual(get_display_name(PROJECT_TYPE_CATEGORY), 'category')
        self.assertEqual(
            get_display_name(PROJECT_TYPE_CATEGORY, title=True), 'Category'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_CATEGORY, count=3), 'categories'
        )
        self.assertEqual(
            get_display_name(PROJECT_TYPE_CATEGORY, title=True, count=3),
            'Categories',
        )

    # TODO: Test with override

    def test_build_secret(self):
        """Test build_secret()"""
        secret = build_secret()
        self.assertEqual(re.match(r'[a-z\d]{32}', secret).string, secret)
        self.assertEqual(len(build_secret(16)), 16)

    @override_settings(PROJECTROLES_SECRET_LENGTH=16)
    def test_build_secret_override(self):
        """Test build_secret() with default length setting override"""
        self.assertEqual(len(build_secret()), 16)

    def test_get_app_names(self):
        """Test get_app_names()"""
        app_names = get_app_names()
        self.assertNotEqual(len(app_names), 0)
        self.assertFalse(any([a.startswith('django.') for a in app_names]))
        self.assertFalse(any(['.apps.' in a for a in app_names]))
        self.assertNotIn(settings.SITE_PACKAGE, app_names)
