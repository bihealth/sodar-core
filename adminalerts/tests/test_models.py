"""Tests for models in the adminalerts app"""

from django.forms.models import model_to_dict
from django.utils import timezone

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import SODARUser

from adminalerts.models import AdminAlert


class AdminAlertMixin:
    """Helper mixin for AdminAlert creation"""

    @classmethod
    def make_alert(
        cls,
        message: str,
        user: SODARUser,
        description: str,
        active: bool = True,
        require_auth: bool = True,
        date_expire_days: int = 1,
    ) -> AdminAlert:
        """Create AdminAlert object"""
        values = {
            'message': message,
            'user': user,
            'description': description,
            'date_expire': timezone.now()
            + timezone.timedelta(days=date_expire_days),
            'active': active,
            'require_auth': require_auth,
        }
        return AdminAlert.objects.create(**values)


class TestAdminAlert(AdminAlertMixin, TestCase):
    """Tests for AdminAlert model"""

    def setUp(self):
        # Create superuser
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
            require_auth=True,
        )

    def test_initialization(self):
        expected = {
            'id': self.alert.pk,
            'message': 'alert',
            'user': self.superuser.pk,
            'date_expire': self.alert.date_expire,
            'active': True,
            'require_auth': True,
            'sodar_uuid': self.alert.sodar_uuid,
        }
        model_dict = model_to_dict(self.alert)
        # HACK: Can't compare markupfields like this. Better solution?
        model_dict.pop('description', None)
        self.assertEqual(model_dict, expected)

    def test__str__(self):
        expected = 'alert [ACTIVE]'
        self.assertEqual(str(self.alert), expected)

    def test__repr__(self):
        expected = "AdminAlert('alert', 'superuser', True)"
        self.assertEqual(repr(self.alert), expected)
