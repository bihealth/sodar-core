"""Tests for Django checks in the projectroles app"""

from django.test import override_settings

from test_plus.test import TestCase

import projectroles.checks as checks
from projectroles.apps import ProjectrolesConfig


# Local constants
AC = [ProjectrolesConfig]


class TestCheckAuthMethods(TestCase):
    """Tests for check_auth_methods()"""

    def test_check(self):
        """Test check_auth_methods() with default test settings"""
        self.assertEqual(checks.check_auth_methods(AC), [])

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_check_disabled_auth(self):
        """Test check_auth_methods() with disabled auth settings"""
        # NOTE: Other settings are already false in the test config
        self.assertEqual(checks.check_auth_methods(AC), [checks.W001])
