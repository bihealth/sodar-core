"""Tests for models in the sodarcache app"""

from typing import Union

from django.forms.models import model_to_dict

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import Project, SODARUser, SODAR_CONSTANTS
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)

from sodarcache.models import JSONCacheItem


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
APP_NAME = 'sodarcache'


class JSONCacheItemMixin:
    """Helper mixin for JSONCacheItem creation"""

    @classmethod
    def make_item(
        cls,
        project: Project,
        app_name: str,
        name: str,
        user: SODARUser,
        data: Union[dict, list],
    ) -> JSONCacheItem:
        """Create JSONCacheItem object"""
        values = {
            'project': project,
            'app_name': app_name,
            'user': user,
            'name': name,
            'data': data,
        }
        return JSONCacheItem.objects.create(**values)


class JSONCacheItemTestBase(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, TestCase
):
    def setUp(self):
        # Make owner user
        self.user_owner = self.make_user('owner')
        # Init roles
        self.init_roles()
        # Init project and assignment
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.assignment_owner = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )


class TestJSONCacheItem(JSONCacheItemMixin, JSONCacheItemTestBase):
    def setUp(self):
        super().setUp()
        self.item = self.make_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )

    def test_initialization(self):
        expected = {
            'id': self.item.pk,
            'project': self.project.pk,
            'app_name': APP_NAME,
            'name': 'test_item',
            'user': self.user_owner.pk,
            'sodar_uuid': self.item.sodar_uuid,
            'data': {'test_key': 'test_val'},
        }
        self.assertEqual(model_to_dict(self.item), expected)

    def test__str__(self):
        expected = 'TestProject: sodarcache: test_item'
        self.assertEqual(str(self.item), expected)

    def test__repr__(self):
        expected = "JSONCacheItem('TestProject', 'sodarcache', 'test_item')"
        self.assertEqual(repr(self.item), expected)

    def test__repr__no_project(self):
        """Test __repr__() with no project"""
        new_item = self.make_item(
            project=None,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item2',
            data={'test_key': 'test_val'},
        )
        expected = "JSONCacheItem('N/A', 'sodarcache', 'test_item2')"
        self.assertEqual(repr(new_item), expected)
