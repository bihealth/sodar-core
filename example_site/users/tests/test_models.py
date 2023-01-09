from test_plus.test import TestCase


class TestUser(TestCase):
    def setUp(self):
        self.user = self.make_user()

    def test__str__(self):
        """Test __str__ method."""
        self.assertEqual(
            self.user.__str__(), 'testuser'
        )  # This is the default username for self.make_user()

    def test_get_form_label(self):
        """Test get_form_label method."""
        self.assertEqual(
            self.user.get_form_label(), ' (testuser) <testuser@example.com>'
        )