"""Tests for RemoteProjectAPI in the projectroles app"""

import uuid

from copy import deepcopy

from django.conf import settings
from django.contrib import auth
from django.forms.models import model_to_dict
from django.test import override_settings

from test_plus.test import TestCase

from projectroles.models import (
    Project,
    RoleAssignment,
    RemoteProject,
    RemoteSite,
    SODARUserAdditionalEmail,
    SODAR_CONSTANTS,
    AppSetting,
)
from projectroles.plugins import get_app_plugin
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SODARUserMixin,
    AppSettingMixin,
    SODARUserAdditionalEmailMixin,
    ADD_EMAIL,
)
from projectroles.utils import build_secret


User = auth.get_user_model()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
REMOTE_LEVEL_REVOKED = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']

# Local constants
APP_NAME = 'projectroles'
SOURCE_SITE_NAME = 'Test source site'
SOURCE_SITE_URL = 'https://sodar.bihealth.org'
SOURCE_SITE_DESC = 'Source description'
SOURCE_SITE_SECRET = build_secret()

SOURCE_USER_DOMAIN = 'TESTDOMAIN'
SOURCE_USER_USERNAME = 'source_user@' + SOURCE_USER_DOMAIN
SOURCE_USER_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER_NAME = 'Firstname Lastname'
SOURCE_USER_FIRST_NAME = SOURCE_USER_NAME.split(' ')[0]
SOURCE_USER_LAST_NAME = SOURCE_USER_NAME.split(' ')[1]
SOURCE_USER_EMAIL = SOURCE_USER_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER_UUID = str(uuid.uuid4())

SOURCE_USER2_DOMAIN = SOURCE_USER_DOMAIN
SOURCE_USER2_USERNAME = 'source_user2@' + SOURCE_USER_DOMAIN
SOURCE_USER2_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER2_NAME = 'Firstname2 Lastname2'
SOURCE_USER2_FIRST_NAME = SOURCE_USER2_NAME.split(' ')[0]
SOURCE_USER2_LAST_NAME = SOURCE_USER2_NAME.split(' ')[1]
SOURCE_USER2_EMAIL = SOURCE_USER2_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER2_UUID = str(uuid.uuid4())

SOURCE_USER3_DOMAIN = SOURCE_USER_DOMAIN
SOURCE_USER3_USERNAME = 'source_user3@' + SOURCE_USER_DOMAIN
SOURCE_USER3_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER3_NAME = 'Firstname3 Lastname3'
SOURCE_USER3_FIRST_NAME = SOURCE_USER3_NAME.split(' ')[0]
SOURCE_USER3_LAST_NAME = SOURCE_USER3_NAME.split(' ')[1]
SOURCE_USER3_EMAIL = SOURCE_USER3_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER3_UUID = str(uuid.uuid4())

SOURCE_USER4_DOMAIN = SOURCE_USER_DOMAIN
SOURCE_USER4_USERNAME = 'source_user4@' + SOURCE_USER_DOMAIN
SOURCE_USER4_GROUP = SOURCE_USER_DOMAIN.lower()
SOURCE_USER4_NAME = 'Firstname4 Lastname4'
SOURCE_USER4_FIRST_NAME = SOURCE_USER4_NAME.split(' ')[0]
SOURCE_USER4_LAST_NAME = SOURCE_USER4_NAME.split(' ')[1]
SOURCE_USER4_EMAIL = SOURCE_USER4_USERNAME.split('@')[0] + '@example.com'
SOURCE_USER4_UUID = str(uuid.uuid4())

SOURCE_CATEGORY_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_TITLE = 'TestCategory'
SOURCE_PROJECT_UUID = str(uuid.uuid4())
SOURCE_PROJECT_TITLE = 'TestProject'
SOURCE_PROJECT_DESCRIPTION = 'Description'
SOURCE_PROJECT_README = 'Readme'
SOURCE_PROJECT_FULL_TITLE = SOURCE_CATEGORY_TITLE + ' / ' + SOURCE_PROJECT_TITLE
SOURCE_CATEGORY_ROLE_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_ROLE2_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_ROLE3_UUID = str(uuid.uuid4())
SOURCE_CATEGORY_ROLE4_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE2_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE3_UUID = str(uuid.uuid4())
SOURCE_PROJECT_ROLE4_UUID = str(uuid.uuid4())

TARGET_SITE_NAME = 'Target name'
TARGET_SITE_URL = 'https://target.url'
TARGET_SITE_DESC = 'Target description'
TARGET_SITE_SECRET = build_secret()

PEER_SITE_UUID = str(uuid.uuid4())
PEER_SITE_NAME = 'Peer name'
PEER_SITE_URL = 'https://peer.url'
PEER_SITE_DESC = 'peer description'
PEER_SITE_SECRET = build_secret()
PEER_SITE_USER_DISPLAY = True

NEW_PEER_NAME = PEER_SITE_NAME + ' new'
NEW_PEER_DESC = PEER_SITE_DESC + ' new'
NEW_PEER_USER_DISPLAY = not PEER_SITE_USER_DISPLAY

SET_IP_RESTRICT_UUID = str(uuid.uuid4())
SET_IP_ALLOWLIST_UUID = str(uuid.uuid4())
SET_STAR_UUID = str(uuid.uuid4())

EXAMPLE_APP_NAME = 'example_project_app'


class RemoteProjectAPITestBase(RoleMixin, TestCase):
    """Base class for RemoteProjectAPI tests"""

    def assert_app_setting(self, uuid, expected):
        """
        Assert app setting model data. Model id and sodar_uuid fields can be
        left out of the expected dict, they will be populated automatically.

        :param uuid: AppSetting UUID
        :param expected: Dict of expected data as model_to_dict output
        """
        set_obj = AppSetting.objects.get(sodar_uuid=uuid)
        expected['id'] = set_obj.id
        expected['sodar_uuid'] = set_obj.sodar_uuid
        set_dict = model_to_dict(set_obj)
        self.assertEqual(set_dict, expected)

    def setUp(self):
        # Init roles
        self.init_roles()


@override_settings(AUTH_LDAP_USERNAME_DOMAIN=SOURCE_USER_DOMAIN)
class TestGetSourceData(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SODARUserMixin,
    AppSettingMixin,
    RemoteProjectAPITestBase,
):
    """Tests for get_source_data()"""

    def setUp(self):
        super().setUp()
        # Init an LDAP user on the source site
        self.user_source = self.make_sodar_user(
            username=SOURCE_USER_USERNAME,
            name=SOURCE_USER_NAME,
            first_name=SOURCE_USER_FIRST_NAME,
            last_name=SOURCE_USER_LAST_NAME,
            email=SOURCE_USER_EMAIL,
        )
        # Init local category and project
        self.category = self.make_project(
            SOURCE_CATEGORY_TITLE, PROJECT_TYPE_CATEGORY, None
        )
        self.project = self.make_project(
            SOURCE_PROJECT_TITLE, PROJECT_TYPE_PROJECT, self.category
        )
        # Init role assignments
        self.category_owner_as = self.make_assignment(
            self.category, self.user_source, self.role_owner
        )
        self.project_owner_as = self.make_assignment(
            self.project, self.user_source, self.role_owner
        )

        # Init target site
        self.target_site = self.make_site(
            name=TARGET_SITE_NAME,
            url=TARGET_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=TARGET_SITE_DESC,
            secret=TARGET_SITE_SECRET,
        )
        # Init peer site
        self.peer_site = self.make_site(
            name=PEER_SITE_NAME,
            url=PEER_SITE_URL,
            mode=SITE_MODE_PEER,
            description=PEER_SITE_DESC,
            secret=PEER_SITE_SECRET,
        )
        self.remote_api = RemoteProjectAPI()

    def test_get_view_avail(self):
        """Test getting data with VIEW_AVAIL level"""
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_VIEW_AVAIL,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_VIEW_AVAIL,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_VIEW_AVAIL,
                    'available': True,
                    'remote_sites': [],
                }
            },
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_get_read_info(self):
        """Test getting data with READ_INFO level"""
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_INFO,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_READ_INFO,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'remote_sites': [str(self.peer_site.sodar_uuid)],
                },
            },
            'peer_sites': {
                str(self.peer_site.sodar_uuid): {
                    'name': self.peer_site.name,
                    'url': self.peer_site.url,
                    'description': self.peer_site.description,
                    'user_display': self.peer_site.user_display,
                }
            },
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_get_read_info_nested(self):
        """Test getting data with READ_INFO and nested categories"""
        sub_category = self.make_project(
            'SubCategory', PROJECT_TYPE_CATEGORY, parent=self.category
        )
        self.make_assignment(sub_category, self.user_source, self.role_owner)
        self.project.parent = sub_category
        self.project.save()
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_INFO,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                },
                str(sub_category.sodar_uuid): {
                    'title': sub_category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'description': sub_category.description,
                    'readme': sub_category.readme.raw,
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(sub_category.sodar_uuid),
                    'remote_sites': [],
                },
            },
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_get_read_roles(self):
        """Test getting data with READ_ROLES level"""
        self.maxDiff = None
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {
                str(self.user_source.sodar_uuid): {
                    'username': self.user_source.username,
                    'name': self.user_source.name,
                    'first_name': self.user_source.first_name,
                    'last_name': self.user_source.last_name,
                    'email': self.user_source.email,
                    'additional_emails': [],
                    'groups': [SOURCE_USER_GROUP],
                    'sodar_uuid': str(self.user_source.sodar_uuid),
                }
            },
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                    'roles': {
                        str(self.category_owner_as.sodar_uuid): {
                            'user': self.user_source.username,
                            'role': self.role_owner.name,
                        }
                    },
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'roles': {
                        str(self.project_owner_as.sodar_uuid): {
                            'user': self.user_source.username,
                            'role': self.role_owner.name,
                        }
                    },
                    'remote_sites': [str(self.peer_site.sodar_uuid)],
                },
            },
            'peer_sites': {
                str(self.peer_site.sodar_uuid): {
                    'name': self.peer_site.name,
                    'url': self.peer_site.url,
                    'description': self.peer_site.description,
                    'user_display': self.peer_site.user_display,
                }
            },
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_get_read_roles_inherited(self):
        """Test getting data with READ_ROLES and inherited contributor"""
        user_new_name = 'user_new@' + SOURCE_USER_DOMAIN
        user_new = self.make_sodar_user(
            username=user_new_name,
            name='New User',
            first_name='New',
            last_name='User',
            email='user_new@example.com',
        )
        contrib_as = self.make_assignment(
            self.category, user_new, self.role_contributor
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )

        sync_data = self.remote_api.get_source_data(self.target_site)
        c_uuid = str(self.category.sodar_uuid)
        a_uuid = str(contrib_as.sodar_uuid)
        self.assertIn(str(user_new.sodar_uuid), sync_data['users'].keys())
        self.assertIn(a_uuid, sync_data['projects'][c_uuid]['roles'].keys())
        self.assertEqual(
            sync_data['projects'][c_uuid]['roles'][a_uuid]['user'],
            user_new_name,
        )
        self.assertEqual(
            sync_data['projects'][c_uuid]['roles'][a_uuid]['role'],
            PROJECT_ROLE_CONTRIBUTOR,
        )

    def test_get_settings(self):
        """Test getting data with app settings"""
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        # Init local project (settings should not be synced)
        local_project = self.make_project(
            'LocalProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.make_assignment(local_project, self.user_source, self.role_owner)
        # Init settings for synced project
        set_ip_restrict = self.make_setting(
            plugin_name=APP_NAME,
            name='ip_restrict',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
        )
        set_ip_allowlist = self.make_setting(
            plugin_name=APP_NAME,
            name='ip_allowlist',
            setting_type=APP_SETTING_TYPE_JSON,
            value=None,
            value_json=['127.0.0.1'],
            project=self.project,
        )
        set_star = self.make_setting(
            plugin_name=APP_NAME,
            name='project_star',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=self.user_source,
        )
        # Init setting for local project (should not be synced)
        set_local = self.make_setting(
            plugin_name=APP_NAME,
            name='project_star',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=local_project,
            user=self.user_source,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)

        self.assertEqual(len(sync_data['app_settings']), 3)
        self.assertNotIn(set_local, sync_data['app_settings'])
        set_data = sync_data['app_settings'][str(set_ip_restrict.sodar_uuid)]
        expected = {
            'name': set_ip_restrict.name,
            'type': set_ip_restrict.type,
            'value': set_ip_restrict.value,
            'value_json': {},
            'app_plugin': None,
            'project_uuid': str(self.project.sodar_uuid),
            'user_uuid': None,
            'user_name': None,
            'global': True,
        }
        self.assertEqual(set_data, expected)
        set_data = sync_data['app_settings'][str(set_ip_allowlist.sodar_uuid)]
        expected = {
            'name': set_ip_allowlist.name,
            'type': set_ip_allowlist.type,
            'value': None,
            'value_json': set_ip_allowlist.value_json,
            'app_plugin': None,
            'project_uuid': str(self.project.sodar_uuid),
            'user_uuid': None,
            'user_name': None,
            'global': True,
        }
        self.assertEqual(set_data, expected)
        set_data = sync_data['app_settings'][str(set_star.sodar_uuid)]
        expected = {
            'name': set_star.name,
            'type': set_star.type,
            'value': '1',
            'value_json': {},
            'app_plugin': None,
            'project_uuid': str(self.project.sodar_uuid),
            'user_uuid': str(self.user_source.sodar_uuid),
            'user_name': self.user_source.username,
            'global': False,
        }
        self.assertEqual(set_data, expected)

    def test_get_settings_user(self):
        """Test getting user app settings"""
        user_global_setting = self.make_setting(
            plugin_name=APP_NAME,
            name='notify_email_project',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=False,
            user=self.user_source,
        )
        user_local_setting = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_str_setting',
            setting_type=APP_SETTING_TYPE_STRING,
            value='Local value',
            user=self.user_source,
        )
        self.assertEqual(
            AppSetting.objects.filter(project=None).exclude(user=None).count(),
            2,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)

        # NOTE: Local setting should also be included
        self.assertEqual(len(sync_data['app_settings']), 2)
        expected = {
            'name': 'notify_email_project',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '0',
            'value_json': {},
            'app_plugin': None,
            'project_uuid': None,
            'user_uuid': str(self.user_source.sodar_uuid),
            'user_name': SOURCE_USER_USERNAME,
            'global': True,
        }
        self.assertEqual(
            sync_data['app_settings'][str(user_global_setting.sodar_uuid)],
            expected,
        )
        expected = {
            'name': 'user_str_setting',
            'type': APP_SETTING_TYPE_STRING,
            'value': 'Local value',
            'value_json': {},
            'app_plugin': EXAMPLE_APP_NAME,
            'project_uuid': None,
            'user_uuid': str(self.user_source.sodar_uuid),
            'user_name': SOURCE_USER_USERNAME,
            'global': False,
        }
        self.assertEqual(
            sync_data['app_settings'][str(user_local_setting.sodar_uuid)],
            expected,
        )

    def test_get_revoked(self):
        """Test getting data with REVOKED level"""
        user_source_new = self.make_user('new_source_user')
        self.make_assignment(self.project, user_source_new, self.role_guest)
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=REMOTE_LEVEL_REVOKED,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.peer_site,
            level=REMOTE_LEVEL_REVOKED,
        )
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {
                str(self.user_source.sodar_uuid): {
                    'username': self.user_source.username,
                    'name': self.user_source.name,
                    'first_name': self.user_source.first_name,
                    'last_name': self.user_source.last_name,
                    'email': self.user_source.email,
                    'additional_emails': [],
                    'groups': [SOURCE_USER_GROUP],
                    'sodar_uuid': str(self.user_source.sodar_uuid),
                }
            },
            'projects': {
                str(self.category.sodar_uuid): {
                    'title': self.category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_INFO,
                    'parent_uuid': None,
                    'description': self.category.description,
                    'readme': self.category.readme.raw,
                },
                str(self.project.sodar_uuid): {
                    'title': self.project.title,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_REVOKED,
                    'description': self.project.description,
                    'readme': self.project.readme.raw,
                    'parent_uuid': str(self.category.sodar_uuid),
                    'roles': {
                        str(self.project_owner_as.sodar_uuid): {
                            'user': self.user_source.username,
                            'role': self.role_owner.name,
                        }  # NOTE: Another user should not be synced
                    },
                    'remote_sites': [],
                },
            },
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)

    def test_get_no_access(self):
        """Test getting data with no project access set in source site"""
        sync_data = self.remote_api.get_source_data(self.target_site)
        expected = {
            'users': {},
            'projects': {},
            'peer_sites': {},
            'app_settings': {},
        }
        self.assertEqual(sync_data, expected)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class SyncRemoteDataTestBase(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    SODARUserMixin,
    AppSettingMixin,
    RemoteProjectAPITestBase,
):
    """Base class for tests for sync_remote_data()"""

    def setUp(self):
        super().setUp()
        # Init users
        self.admin_user = self.make_user(settings.PROJECTROLES_DEFAULT_ADMIN)
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.maxDiff = None
        # Init source site
        self.source_site = self.make_site(
            name=SOURCE_SITE_NAME,
            url=SOURCE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=SOURCE_SITE_DESC,
            secret=SOURCE_SITE_SECRET,
        )
        self.remote_api = RemoteProjectAPI()

        # Default data to receive from source when testing site in target mode
        self.default_data = {
            'users': {
                SOURCE_USER_UUID: {
                    'sodar_uuid': SOURCE_USER_UUID,
                    'username': SOURCE_USER_USERNAME,
                    'name': SOURCE_USER_NAME,
                    'first_name': SOURCE_USER_FIRST_NAME,
                    'last_name': SOURCE_USER_LAST_NAME,
                    'email': SOURCE_USER_EMAIL,
                    'additional_emails': [],
                    'groups': [SOURCE_USER_GROUP],
                },
            },
            'projects': {
                SOURCE_CATEGORY_UUID: {
                    'title': SOURCE_CATEGORY_TITLE,
                    'type': PROJECT_TYPE_CATEGORY,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'parent_uuid': None,
                    'description': SOURCE_PROJECT_DESCRIPTION,
                    'readme': SOURCE_PROJECT_README,
                    'roles': {
                        SOURCE_CATEGORY_ROLE_UUID: {
                            'user': SOURCE_USER_USERNAME,
                            'role': self.role_owner.name,
                        },
                    },
                },
                SOURCE_PROJECT_UUID: {
                    'title': SOURCE_PROJECT_TITLE,
                    'type': PROJECT_TYPE_PROJECT,
                    'level': REMOTE_LEVEL_READ_ROLES,
                    'description': SOURCE_PROJECT_DESCRIPTION,
                    'readme': SOURCE_PROJECT_README,
                    'parent_uuid': SOURCE_CATEGORY_UUID,
                    'roles': {
                        SOURCE_PROJECT_ROLE_UUID: {
                            'user': SOURCE_USER_USERNAME,
                            'role': self.role_owner.name,
                        },
                    },
                    'remote_sites': [PEER_SITE_UUID],
                },
            },
            'peer_sites': {
                PEER_SITE_UUID: {
                    'name': PEER_SITE_NAME,
                    'url': PEER_SITE_URL,
                    'description': PEER_SITE_DESC,
                    'user_display': PEER_SITE_USER_DISPLAY,
                }
            },
            'app_settings': {
                SET_IP_RESTRICT_UUID: {
                    'name': 'ip_restrict',
                    'type': APP_SETTING_TYPE_BOOLEAN,
                    'value': False,
                    'value_json': {},
                    'app_plugin': None,  # None is for 'projectroles' app
                    'project_uuid': SOURCE_PROJECT_UUID,
                    'user_uuid': None,
                    'global': True,
                },
                SET_IP_ALLOWLIST_UUID: {
                    'name': 'ip_allowlist',
                    'type': APP_SETTING_TYPE_JSON,
                    'value': '',
                    'value_json': [],
                    'app_plugin': None,  # None is for 'projectroles' app
                    'project_uuid': SOURCE_PROJECT_UUID,
                    'user_uuid': None,
                    'global': True,
                },
                SET_STAR_UUID: {
                    'name': 'project_star',
                    'type': APP_SETTING_TYPE_BOOLEAN,
                    'value': '1',
                    'value_json': {},
                    'app_plugin': None,
                    'project_uuid': SOURCE_PROJECT_UUID,
                    'user_uuid': SOURCE_USER_UUID,
                    'user_name': SOURCE_USER_USERNAME,
                    'global': False,
                },
            },
        }


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestSyncRemoteDataCreate(SyncRemoteDataTestBase):
    """Tests for project creation with sync_remote_data()"""

    def test_create(self):
        """Test sync with non-existing project data and READ_ROLE access"""
        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        self.default_data['users'].update(
            {
                SOURCE_USER2_UUID: {
                    'sodar_uuid': SOURCE_USER2_UUID,
                    'username': SOURCE_USER2_USERNAME,
                    'name': SOURCE_USER2_NAME,
                    'first_name': SOURCE_USER2_FIRST_NAME,
                    'last_name': SOURCE_USER2_LAST_NAME,
                    'email': SOURCE_USER2_EMAIL,
                    'additional_emails': [],
                    'groups': [SOURCE_USER2_GROUP],
                },
                SOURCE_USER3_UUID: {
                    'sodar_uuid': SOURCE_USER3_UUID,
                    'username': SOURCE_USER3_USERNAME,
                    'name': SOURCE_USER3_NAME,
                    'first_name': SOURCE_USER3_FIRST_NAME,
                    'last_name': SOURCE_USER3_LAST_NAME,
                    'email': SOURCE_USER3_EMAIL,
                    'additional_emails': [],
                    'groups': [SOURCE_USER3_GROUP],
                },
                SOURCE_USER4_UUID: {
                    'sodar_uuid': SOURCE_USER4_UUID,
                    'username': SOURCE_USER4_USERNAME,
                    'name': SOURCE_USER4_NAME,
                    'first_name': SOURCE_USER4_FIRST_NAME,
                    'last_name': SOURCE_USER4_LAST_NAME,
                    'email': SOURCE_USER4_EMAIL,
                    'additional_emails': [],
                    'groups': [SOURCE_USER4_GROUP],
                },
            }
        )
        self.default_data['projects'][SOURCE_CATEGORY_UUID]['roles'].update(
            {
                SOURCE_CATEGORY_ROLE2_UUID: {
                    'user': SOURCE_USER2_USERNAME,
                    'role': self.role_delegate.name,
                },
                SOURCE_CATEGORY_ROLE3_UUID: {
                    'user': SOURCE_USER3_USERNAME,
                    'role': self.role_contributor.name,
                },
                SOURCE_CATEGORY_ROLE4_UUID: {
                    'user': SOURCE_USER4_USERNAME,
                    'role': self.role_guest.name,
                },
            }
        )
        self.default_data['projects'][SOURCE_PROJECT_UUID]['roles'].update(
            {
                SOURCE_PROJECT_ROLE2_UUID: {
                    'user': SOURCE_USER2_USERNAME,
                    'role': self.role_delegate.name,
                },
                SOURCE_PROJECT_ROLE3_UUID: {
                    'user': SOURCE_USER3_USERNAME,
                    'role': self.role_contributor.name,
                },
                SOURCE_PROJECT_ROLE4_UUID: {
                    'user': SOURCE_USER4_USERNAME,
                    'role': self.role_guest.name,
                },
            }
        )
        og_data = deepcopy(self.default_data)
        # Do sync
        self.remote_api.sync_remote_data(self.source_site, self.default_data)

        # Assert database status
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 8)
        self.assertEqual(User.objects.all().count(), 5)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        self.assertEqual(AppSetting.objects.count(), 3)

        new_user = User.objects.get(username=SOURCE_USER_USERNAME)
        new_user2 = User.objects.get(username=SOURCE_USER2_USERNAME)
        new_user3 = User.objects.get(username=SOURCE_USER3_USERNAME)
        new_user4 = User.objects.get(username=SOURCE_USER4_USERNAME)
        category_obj = Project.objects.get(sodar_uuid=SOURCE_CATEGORY_UUID)
        expected = {
            'id': category_obj.pk,
            'title': SOURCE_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': None,
            'public_guest_access': False,
            'archive': False,
            'full_title': SOURCE_CATEGORY_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_UUID),
        }
        model_dict = model_to_dict(category_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        c_owner_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE_UUID
        )
        c_delegate_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE2_UUID
        )
        c_contributor_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE3_UUID
        )
        c_guest_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_CATEGORY_ROLE4_UUID
        )

        expected = {
            'id': c_owner_obj.pk,
            'project': category_obj.pk,
            'user': new_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE_UUID),
        }
        self.assertEqual(model_to_dict(c_owner_obj), expected)
        expected = {
            'id': c_delegate_obj.pk,
            'project': category_obj.pk,
            'user': new_user2.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE2_UUID),
        }
        self.assertEqual(model_to_dict(c_delegate_obj), expected)
        expected = {
            'id': c_contributor_obj.pk,
            'project': category_obj.pk,
            'user': new_user3.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE3_UUID),
        }
        self.assertEqual(model_to_dict(c_contributor_obj), expected)
        expected = {
            'id': c_guest_obj.pk,
            'project': category_obj.pk,
            'user': new_user4.pk,
            'role': self.role_guest.pk,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_ROLE4_UUID),
        }
        self.assertEqual(model_to_dict(c_guest_obj), expected)

        project_obj = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        expected = {
            'id': project_obj.pk,
            'title': SOURCE_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': category_obj.pk,
            'public_guest_access': False,
            'archive': False,
            'full_title': SOURCE_PROJECT_FULL_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_UUID),
        }
        model_dict = model_to_dict(project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        p_owner_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE_UUID
        )
        p_delegate_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE2_UUID
        )
        p_contributor_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE3_UUID
        )
        p_guest_obj = RoleAssignment.objects.get(
            sodar_uuid=SOURCE_PROJECT_ROLE4_UUID
        )

        expected = {
            'id': p_owner_obj.pk,
            'project': project_obj.pk,
            'user': new_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE_UUID),
        }
        self.assertEqual(model_to_dict(p_owner_obj), expected)
        expected = {
            'id': p_delegate_obj.pk,
            'project': project_obj.pk,
            'user': new_user2.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE2_UUID),
        }
        self.assertEqual(model_to_dict(p_delegate_obj), expected)
        expected = {
            'id': p_contributor_obj.pk,
            'project': project_obj.pk,
            'user': new_user3.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE3_UUID),
        }
        self.assertEqual(model_to_dict(p_contributor_obj), expected)
        expected = {
            'id': p_guest_obj.pk,
            'project': project_obj.pk,
            'user': new_user4.pk,
            'role': self.role_guest.pk,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_ROLE4_UUID),
        }
        self.assertEqual(model_to_dict(p_guest_obj), expected)

        remote_cat_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=category_obj.sodar_uuid
        )
        expected = {
            'id': remote_cat_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': category_obj.sodar_uuid,
            'project': category_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_cat_obj.date_access,
            'sodar_uuid': remote_cat_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_cat_obj), expected)

        remote_project_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=project_obj.sodar_uuid
        )
        expected = {
            'id': remote_project_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': project_obj.sodar_uuid,
            'project': project_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_project_obj.date_access,
            'sodar_uuid': remote_project_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_project_obj), expected)

        peer_site_obj = RemoteSite.objects.get(
            sodar_uuid=PEER_SITE_UUID, mode=SITE_MODE_PEER
        )
        expected = {
            'name': PEER_SITE_NAME,
            'url': PEER_SITE_URL,
            'mode': SITE_MODE_PEER,
            'description': PEER_SITE_DESC,
            'secret': None,
            'sodar_uuid': uuid.UUID(PEER_SITE_UUID),
            'user_display': PEER_SITE_USER_DISPLAY,
            'owner_modifiable': True,
        }
        peer_site_dict = model_to_dict(peer_site_obj)
        peer_site_dict.pop('id')
        self.assertEqual(peer_site_dict, expected)

        peer_project_obj = RemoteProject.objects.get(site=peer_site_obj)
        expected = {
            'site': peer_site_obj.pk,
            'project_uuid': project_obj.sodar_uuid,
            'project': project_obj.pk,
        }
        peer_project_dict = model_to_dict(peer_project_obj)
        peer_project_dict.pop('id')
        peer_project_dict.pop('sodar_uuid')
        peer_project_dict.pop('level')
        peer_project_dict.pop('date_access')
        self.assertEqual(peer_project_dict, expected)

        # Assert app settings
        expected = {
            'name': 'ip_restrict',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '0',
            'value_json': {},
            'project': project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_IP_RESTRICT_UUID, expected)
        expected = {
            'name': 'ip_allowlist',
            'type': APP_SETTING_TYPE_JSON,
            'value': '',
            'value_json': [],
            'project': project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_IP_ALLOWLIST_UUID, expected)
        expected = {
            'name': 'project_star',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '1',
            'value_json': {},
            'app_plugin': None,
            'project': project_obj.id,
            'user': new_user.id,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_STAR_UUID, expected)

        # Assert remote_data changes
        expected = og_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'created'
        expected['users'][SOURCE_USER2_UUID]['status'] = 'created'
        expected['users'][SOURCE_USER3_UUID]['status'] = 'created'
        expected['users'][SOURCE_USER4_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE2_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE3_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE4_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE2_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE3_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE4_UUID
        ]['status'] = 'created'
        expected['app_settings'][SET_IP_RESTRICT_UUID]['status'] = 'created'
        expected['app_settings'][SET_IP_ALLOWLIST_UUID]['status'] = 'created'
        expected['app_settings'][SET_STAR_UUID]['status'] = 'created'
        self.assertEqual(self.default_data, expected)

    def test_create_app_setting_local(self):
        """Test sync with local app setting"""
        remote_data = self.default_data
        remote_data['app_settings'][SET_IP_RESTRICT_UUID]['global'] = False
        remote_data['app_settings'][SET_IP_ALLOWLIST_UUID]['global'] = False
        expected = deepcopy(remote_data)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        expected['users'][SOURCE_USER_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['status'] = 'created'
        expected['app_settings'][SET_IP_RESTRICT_UUID]['status'] = 'created'
        expected['app_settings'][SET_IP_ALLOWLIST_UUID]['status'] = 'created'
        expected['app_settings'][SET_STAR_UUID]['status'] = 'created'
        self.assertEqual(remote_data, expected)

    def test_create_multiple(self):
        """Test sync with multiple non-existing projects"""
        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        remote_data = self.default_data
        new_project_uuid = str(uuid.uuid4())
        new_project_title = 'New Project Title'
        new_role_uuid = str(uuid.uuid4())
        remote_data['projects'][new_project_uuid] = {
            'title': new_project_title,
            'type': PROJECT_TYPE_PROJECT,
            'level': REMOTE_LEVEL_READ_ROLES,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'readme': SOURCE_PROJECT_README,
            'parent_uuid': SOURCE_CATEGORY_UUID,
            'roles': {
                new_role_uuid: {
                    'user': SOURCE_USER_USERNAME,
                    'role': self.role_owner.name,
                }
            },
        }
        og_data = deepcopy(remote_data)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 3)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 4)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        new_user = User.objects.get(username=SOURCE_USER_USERNAME)
        category_obj = Project.objects.get(sodar_uuid=SOURCE_CATEGORY_UUID)
        new_project_obj = Project.objects.get(sodar_uuid=new_project_uuid)
        expected = {
            'id': new_project_obj.pk,
            'title': new_project_title,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': category_obj.pk,
            'public_guest_access': False,
            'archive': False,
            'full_title': SOURCE_CATEGORY_TITLE + ' / ' + new_project_title,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(new_project_uuid),
        }
        model_dict = model_to_dict(new_project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        p_new_owner_obj = RoleAssignment.objects.get(sodar_uuid=new_role_uuid)
        expected = {
            'id': p_new_owner_obj.pk,
            'project': new_project_obj.pk,
            'user': new_user.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': uuid.UUID(new_role_uuid),
        }
        self.assertEqual(model_to_dict(p_new_owner_obj), expected)

        expected = og_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'created'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['status'] = 'created'
        expected['projects'][new_project_uuid]['status'] = 'created'
        expected['projects'][new_project_uuid]['roles'][new_role_uuid][
            'status'
        ] = 'created'
        expected['app_settings'][SET_IP_RESTRICT_UUID]['status'] = 'created'
        expected['app_settings'][SET_IP_ALLOWLIST_UUID]['status'] = 'created'
        expected['app_settings'][SET_STAR_UUID]['status'] = 'created'
        self.assertEqual(remote_data, expected)

    def test_create_local_owner(self):
        """Test sync with non-existing project data and local owner"""
        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        remote_data = self.default_data
        remote_data['users'][SOURCE_USER_UUID]['username'] = 'source_admin'
        remote_data['users'][SOURCE_USER_UUID]['groups'] = [SYSTEM_USER_GROUP]
        remote_data['projects'][SOURCE_CATEGORY_UUID]['roles'][
            SOURCE_CATEGORY_ROLE_UUID
        ]['user'] = 'source_admin'
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][
            SOURCE_PROJECT_ROLE_UUID
        ]['user'] = 'source_admin'
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        category_obj = Project.objects.get(sodar_uuid=SOURCE_CATEGORY_UUID)
        self.assertEqual(category_obj.get_owner().user, self.admin_user)
        project_obj = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        self.assertEqual(project_obj.get_owner().user, self.admin_user)

    def test_create_category_conflict(self):
        """Test sync with conflict in local categories (should fail)"""
        self.make_project(
            title=SOURCE_CATEGORY_TITLE,
            type=PROJECT_TYPE_CATEGORY,
            parent=None,
        )
        self.assertEqual(Project.objects.all().count(), 1)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        remote_data = self.default_data
        # Do sync, assert an exception is raised
        with self.assertRaises(ValueError):
            self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 1)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)

    def test_create_inherited(self):
        """Test sync with inherited contributor"""
        self.assertEqual(User.objects.all().count(), 1)
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        new_user_uuid = str(uuid.uuid4())
        new_role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        remote_data['users'][str(new_user_uuid)] = {
            'sodar_uuid': new_user_uuid,
            'username': new_user_username,
            'name': 'Some Name',
            'first_name': 'Some',
            'last_name': 'Name',
            'email': 'some@example.com',
            'additional_emails': [],
            'groups': [SOURCE_USER_GROUP],
        }
        remote_data['projects'][SOURCE_CATEGORY_UUID]['roles'][
            new_role_uuid
        ] = {'user': new_user_username, 'role': PROJECT_ROLE_CONTRIBUTOR}
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(User.objects.all().count(), 3)
        new_user = User.objects.get(username=new_user_username)
        category = Project.objects.get(sodar_uuid=SOURCE_CATEGORY_UUID)
        self.assertEqual(
            RoleAssignment.objects.get(project=category, user=new_user).role,
            self.role_contributor,
        )

    def test_create_no_access(self):
        """Test sync with no READ_ROLE access set"""
        remote_data = self.default_data
        remote_data['projects'][SOURCE_CATEGORY_UUID][
            'level'
        ] = REMOTE_LEVEL_READ_INFO
        remote_data['projects'][SOURCE_PROJECT_UUID][
            'level'
        ] = REMOTE_LEVEL_READ_INFO
        og_data = deepcopy(remote_data)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 0)
        self.assertEqual(RoleAssignment.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        # Assert no changes between update_data and remote_data
        self.assertEqual(og_data, remote_data)

    def test_create_local_user(self):
        """Test sync with local non-owner user"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'additional_emails': [],
            'groups': [SYSTEM_USER_GROUP],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][role_uuid] = {
            'user': local_user_username,
            'role': self.role_contributor.name,
        }
        self.assertEqual(User.objects.all().count(), 1)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        # Assert database status (the new user and role should not be created)
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_user_allow(self):
        """Test sync with local user with local users allowed"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        self.make_user(local_user_username)
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'additional_emails': [],
            'groups': [SYSTEM_USER_GROUP],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][role_uuid] = {
            'user': local_user_username,
            'role': self.role_contributor.name,
        }
        self.assertEqual(User.objects.all().count(), 2)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_user_allow_unavailable(self):
        """Test sync with non-existent local user and local users allowed"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'additional_emails': [],
            'groups': [SYSTEM_USER_GROUP],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][role_uuid] = {
            'user': local_user_username,
            'role': self.role_contributor.name,
        }
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_owner_allow(self):
        """Test sync with local owner and local users allowed"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        # Create the user on the target site
        new_user = self.make_user(local_user_username)
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'additional_emails': [],
            'groups': [SYSTEM_USER_GROUP],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'] = {
            role_uuid: {
                'user': local_user_username,
                'role': self.role_owner.name,
            }
        }
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        # Assert owner role
        new_project = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        self.assertEqual(new_project.get_owner().user, new_user)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_create_local_owner_allow_unavailable(self):
        """Test sync with unavailable local owner"""
        local_user_username = 'localusername'
        local_user_uuid = str(uuid.uuid4())
        role_uuid = str(uuid.uuid4())
        remote_data = self.default_data
        # Create the user on the target site
        remote_data['users'][local_user_uuid] = {
            'sodar_uuid': local_user_uuid,
            'username': local_user_username,
            'name': SOURCE_USER_NAME,
            'first_name': SOURCE_USER_FIRST_NAME,
            'last_name': SOURCE_USER_LAST_NAME,
            'email': SOURCE_USER_EMAIL,
            'additional_emails': [],
            'groups': [SYSTEM_USER_GROUP],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'] = {
            role_uuid: {
                'user': local_user_username,
                'role': self.role_owner.name,
            }
        }
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        new_project = Project.objects.get(sodar_uuid=SOURCE_PROJECT_UUID)
        self.assertEqual(new_project.get_owner().user, self.admin_user)

    def test_create_settings_user(self):
        """Test sync with USER scope settings"""
        self.assertEqual(AppSetting.objects.count(), 0)
        remote_data = self.default_data
        global_set_uuid = str(uuid.uuid4())
        local_set_uuid = str(uuid.uuid4())
        remote_data['app_settings'][global_set_uuid] = {
            'name': 'notify_email_project',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '0',
            'value_json': {},
            'app_plugin': None,
            'project_uuid': None,
            'user_uuid': SOURCE_USER_UUID,
            'user_name': SOURCE_USER_USERNAME,
            'global': True,
        }
        remote_data['app_settings'][local_set_uuid] = {
            'name': 'user_str_setting',
            'type': APP_SETTING_TYPE_STRING,
            'value': 'Local value',
            'value_json': {},
            'app_plugin': EXAMPLE_APP_NAME,
            'project_uuid': None,
            'user_uuid': SOURCE_USER_UUID,
            'user_name': SOURCE_USER_USERNAME,
            'global': False,
        }

        self.remote_api.sync_remote_data(self.source_site, remote_data)
        self.assertEqual(AppSetting.objects.count(), 5)
        target_user = User.objects.get(username=SOURCE_USER_USERNAME)

        obj = AppSetting.objects.get(
            app_plugin=None, name='notify_email_project'
        )
        expected = {
            'id': obj.pk,
            'app_plugin': None,
            'project': None,
            'name': 'notify_email_project',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'user': target_user.pk,
            'value': '0',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(obj), expected)
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME).get_model()

        obj = AppSetting.objects.get(
            app_plugin=app_plugin, name='user_str_setting'
        )
        expected = {
            'id': obj.pk,
            'app_plugin': app_plugin.pk,
            'project': None,
            'name': 'user_str_setting',
            'type': APP_SETTING_TYPE_STRING,
            'user': target_user.pk,
            'value': 'Local value',
            'value_json': {},
            'user_modifiable': True,
            'sodar_uuid': obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(obj), expected)
        # Assert sync data
        self.assertEqual(
            remote_data['app_settings'][global_set_uuid]['status'], 'created'
        )
        self.assertEqual(
            remote_data['app_settings'][local_set_uuid]['status'], 'created'
        )

    def test_create_user_add_email(self):
        """Test sync with additional email on user"""
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 0)
        remote_data = self.default_data
        remote_data['users'][SOURCE_USER_UUID]['additional_emails'] = [
            ADD_EMAIL
        ]
        self.remote_api.sync_remote_data(self.source_site, remote_data)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)
        email = SODARUserAdditionalEmail.objects.first()
        target_user = User.objects.get(sodar_uuid=SOURCE_USER_UUID)
        self.assertEqual(email.user, target_user)
        self.assertEqual(email.email, ADD_EMAIL)
        self.assertEqual(email.verified, True)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestSyncRemoteDataUpdate(
    SODARUserAdditionalEmailMixin, SyncRemoteDataTestBase
):
    """Tests for project updating with sync_remote_data()"""

    def setUp(self):
        super().setUp()
        # Set up target category and project
        self.category_obj = self.make_project(
            title='NewCategoryTitle',
            type=PROJECT_TYPE_CATEGORY,
            parent=None,
            description='New description',
            readme='New readme',
            sodar_uuid=SOURCE_CATEGORY_UUID,
        )
        self.project_obj = self.make_project(
            title='NewProjectTitle',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category_obj,
            description='New description',
            readme='New readme',
            sodar_uuid=SOURCE_PROJECT_UUID,
        )

        # Set up user and roles
        self.user_target = self.make_sodar_user(
            username=SOURCE_USER_USERNAME,
            name='NewFirstName NewLastName',
            first_name='NewFirstName',
            last_name='NewLastName',
            email='newemail@example.com',
            sodar_uuid=SOURCE_USER_UUID,
        )
        self.c_owner_obj = self.make_assignment(
            self.category_obj, self.user_target, self.role_owner
        )
        self.p_owner_obj = self.make_assignment(
            self.project_obj, self.user_target, self.role_owner
        )

        # Set up RemoteProject objects
        self.make_remote_project(
            project_uuid=self.category_obj.sodar_uuid,
            project=self.category_obj,
            site=self.source_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        self.make_remote_project(
            project_uuid=self.project_obj.sodar_uuid,
            project=self.project_obj,
            site=self.source_site,
            level=REMOTE_LEVEL_READ_ROLES,
        )

        # Set up Peer Objects
        self.peer_site = RemoteSite.objects.create(
            **{
                'name': PEER_SITE_NAME,
                'url': PEER_SITE_URL,
                'mode': SITE_MODE_PEER,
                'description': PEER_SITE_DESC,
                'secret': None,
                'sodar_uuid': PEER_SITE_UUID,
                'user_display': PEER_SITE_USER_DISPLAY,
            }
        )
        self.make_remote_project(
            project_uuid=self.project_obj.sodar_uuid,
            project=self.project_obj,
            site=self.peer_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_NONE'],
        )

        # Init app settings
        self.make_setting(
            plugin_name=APP_NAME,
            name='ip_restrict',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=False,
            project=self.project_obj,
            sodar_uuid=SET_IP_RESTRICT_UUID,
        )
        self.make_setting(
            plugin_name=APP_NAME,
            name='ip_allowlist',
            setting_type=APP_SETTING_TYPE_JSON,
            value=None,
            value_json=[],
            project=self.project_obj,
            sodar_uuid=SET_IP_ALLOWLIST_UUID,
        )
        self.make_setting(
            plugin_name=APP_NAME,
            name='project_star',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=False,
            project=self.project_obj,
            user=self.user_target,
            sodar_uuid=SET_STAR_UUID,
        )

        # Update default data
        self.default_data['projects'][SOURCE_CATEGORY_UUID][
            'status'
        ] = 'updated'
        self.default_data['projects'][SOURCE_PROJECT_UUID]['status'] = 'updated'
        self.default_data['users'][SOURCE_USER_UUID]['status'] = 'updated'

    def test_update(self):
        """Test sync with existing project data and READ_ROLE access"""
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        self.assertEqual(AppSetting.objects.count(), 3)

        remote_data = self.default_data
        # Add new user and contributor role to source project
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        new_user_uuid = str(uuid.uuid4())
        new_role_uuid = str(uuid.uuid4())
        remote_data['users'][str(new_user_uuid)] = {
            'sodar_uuid': new_user_uuid,
            'username': new_user_username,
            'name': 'Some Name',
            'first_name': 'Some',
            'last_name': 'Name',
            'email': 'some@example.com',
            'additional_emails': [],
            'groups': [SOURCE_USER_GROUP],
        }
        remote_data['projects'][SOURCE_PROJECT_UUID]['roles'][new_role_uuid] = {
            'user': new_user_username,
            'role': PROJECT_ROLE_CONTRIBUTOR,
        }

        # Change Peer Site data
        remote_data['peer_sites'][PEER_SITE_UUID]['name'] = NEW_PEER_NAME
        remote_data['peer_sites'][PEER_SITE_UUID]['description'] = NEW_PEER_DESC
        remote_data['peer_sites'][PEER_SITE_UUID][
            'user_display'
        ] = NEW_PEER_USER_DISPLAY
        og_data = deepcopy(remote_data)
        # Change projectroles app settings
        remote_data['app_settings'][SET_IP_RESTRICT_UUID]['value'] = True
        remote_data['app_settings'][SET_IP_ALLOWLIST_UUID]['value_json'] = [
            '192.168.1.1'
        ]
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        self.assertEqual(AppSetting.objects.count(), 3)

        new_user = User.objects.get(username=new_user_username)
        self.category_obj.refresh_from_db()
        expected = {
            'id': self.category_obj.pk,
            'title': SOURCE_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': None,
            'public_guest_access': False,
            'archive': False,
            'full_title': SOURCE_CATEGORY_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_UUID),
        }
        model_dict = model_to_dict(self.category_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.c_owner_obj.refresh_from_db()
        expected = {
            'id': self.c_owner_obj.pk,
            'project': self.category_obj.pk,
            'user': self.user_target.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.c_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.c_owner_obj), expected)

        self.project_obj.refresh_from_db()
        expected = {
            'id': self.project_obj.pk,
            'title': SOURCE_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': self.category_obj.pk,
            'public_guest_access': False,
            'archive': False,
            'full_title': SOURCE_PROJECT_FULL_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_UUID),
        }
        model_dict = model_to_dict(self.project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.p_owner_obj.refresh_from_db()
        expected = {
            'id': self.p_owner_obj.pk,
            'project': self.project_obj.pk,
            'user': self.user_target.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.p_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.p_owner_obj), expected)

        p_contrib_obj = RoleAssignment.objects.get(
            project__sodar_uuid=SOURCE_PROJECT_UUID,
            role__name=PROJECT_ROLE_CONTRIBUTOR,
        )
        expected = {
            'id': p_contrib_obj.pk,
            'project': self.project_obj.pk,
            'user': new_user.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': p_contrib_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(p_contrib_obj), expected)

        remote_cat_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.category_obj.sodar_uuid
        )
        expected = {
            'id': remote_cat_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.category_obj.sodar_uuid,
            'project': self.category_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_cat_obj.date_access,
            'sodar_uuid': remote_cat_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_cat_obj), expected)

        remote_project_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.project_obj.sodar_uuid
        )
        expected = {
            'id': remote_project_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_project_obj.date_access,
            'sodar_uuid': remote_project_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_project_obj), expected)

        peer_site_obj = RemoteSite.objects.get(
            sodar_uuid=PEER_SITE_UUID, mode=SITE_MODE_PEER
        )
        expected = {
            'name': NEW_PEER_NAME,
            'url': PEER_SITE_URL,
            'mode': SITE_MODE_PEER,
            'description': NEW_PEER_DESC,
            'secret': None,
            'user_display': NEW_PEER_USER_DISPLAY,
            'owner_modifiable': True,
        }
        peer_site_dict = model_to_dict(peer_site_obj)
        peer_site_dict.pop('id')
        peer_site_dict.pop('sodar_uuid')
        self.assertEqual(peer_site_dict, expected)

        peer_project_obj = RemoteProject.objects.get(site=peer_site_obj)
        expected = {
            'site': peer_site_obj.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
        }
        peer_project_dict = model_to_dict(peer_project_obj)
        peer_project_dict.pop('id')
        peer_project_dict.pop('sodar_uuid')
        peer_project_dict.pop('level')
        peer_project_dict.pop('date_access')
        self.assertEqual(peer_project_dict, expected)

        # Assert app settings
        # NOTE: Global app settings should not be updated
        expected = {
            'name': 'ip_restrict',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '1',
            'value_json': {},
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_IP_RESTRICT_UUID, expected)
        expected = {
            'name': 'ip_allowlist',
            'type': APP_SETTING_TYPE_JSON,
            'value': '',
            'value_json': ['192.168.1.1'],
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_IP_ALLOWLIST_UUID, expected)
        expected = {
            'name': 'project_star',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '0',
            'value_json': {},
            'app_plugin': None,
            'project': self.project_obj.id,
            'user': self.user_target.id,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_STAR_UUID, expected)

        # Assert update_data changes
        expected = og_data
        expected['users'][SOURCE_USER_UUID]['status'] = 'updated'
        expected['users'][new_user_uuid]['status'] = 'created'
        expected['projects'][SOURCE_CATEGORY_UUID]['status'] = 'updated'
        expected['projects'][SOURCE_PROJECT_UUID]['status'] = 'updated'
        expected['projects'][SOURCE_PROJECT_UUID]['roles'][new_role_uuid][
            'status'
        ] = 'created'
        expected['app_settings'][SET_IP_RESTRICT_UUID]['value'] = True
        expected['app_settings'][SET_IP_ALLOWLIST_UUID]['value_json'] = [
            '192.168.1.1'
        ]
        expected['app_settings'][SET_IP_RESTRICT_UUID]['status'] = 'updated'
        expected['app_settings'][SET_IP_ALLOWLIST_UUID]['status'] = 'updated'
        expected['app_settings'][SET_STAR_UUID]['status'] = 'skipped'
        self.assertEqual(remote_data, expected)

    def test_update_user_uuid_ldap(self):
        """Test sync with legacy UUID for LDAP user"""
        # Set different UUID for target user
        target_uuid = str(uuid.uuid4())
        self.assertNotEqual(SOURCE_USER_UUID, target_uuid)
        self.user_target.sodar_uuid = target_uuid
        self.user_target.save()
        self.assertEqual(User.objects.all().count(), 2)
        self.remote_api.sync_remote_data(self.source_site, self.default_data)
        self.assertEqual(User.objects.all().count(), 2)
        self.user_target.refresh_from_db()
        self.assertEqual(str(self.user_target.sodar_uuid), SOURCE_USER_UUID)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_update_user_uuid_local_allow(self):
        """Test sync with legacy UUID for local user with local users allowed"""
        local_username = 'localusername'
        local_name = 'Local User'
        user_local = self.make_user(local_username)
        local_uuid_target = str(user_local.sodar_uuid)
        local_uuid_source = str(uuid.uuid4())
        self.assertNotEqual(local_uuid_target, local_uuid_source)
        self.assertNotEqual(user_local.name, local_name)
        remote_data = self.default_data
        remote_data['users'][local_uuid_source] = {
            'username': local_username,
            'name': local_name,
            'first_name': local_name.split(' ')[0],
            'last_name': local_name.split(' ')[1],
            'email': 'some@example.com',
            'additional_emails': [],
            'groups': [SOURCE_USER_GROUP],
        }
        self.assertEqual(User.objects.all().count(), 3)
        self.remote_api.sync_remote_data(self.source_site, remote_data)
        self.assertEqual(User.objects.all().count(), 3)
        user_local.refresh_from_db()
        self.assertEqual(str(user_local.sodar_uuid), local_uuid_source)
        self.assertEqual(user_local.name, local_name)
        self.assertEqual(user_local.first_name, local_name.split(' ')[0])
        self.assertEqual(user_local.last_name, local_name.split(' ')[1])

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_update_user_uuid_local_disallow(self):
        """Test sync with legacy UUID for local user with local users disallowed (should fail)"""
        local_username = 'localusername'
        local_name = 'Local User'
        user_local = self.make_user(local_username)
        local_uuid_target = str(user_local.sodar_uuid)
        local_uuid_source = str(uuid.uuid4())  # Source UUID
        self.assertNotEqual(local_uuid_target, local_uuid_source)
        self.assertNotEqual(user_local.name, local_name)
        remote_data = self.default_data
        remote_data['users'][local_uuid_source] = {
            'username': local_username,
            'name': local_name,
            'first_name': local_name.split(' ')[0],
            'last_name': local_name.split(' ')[1],
            'email': 'some@example.com',
            'additional_emails': [],
            'groups': [SYSTEM_USER_GROUP],
        }
        self.assertEqual(User.objects.all().count(), 3)
        self.remote_api.sync_remote_data(self.source_site, remote_data)
        self.assertEqual(User.objects.all().count(), 3)
        user_local.refresh_from_db()
        self.assertEqual(str(user_local.sodar_uuid), local_uuid_target)
        self.assertNotEqual(user_local.name, local_name)

    def test_update_inherited(self):
        """Test sync with existing project data and inherited contributor"""
        self.assertEqual(User.objects.all().count(), 2)
        remote_data = self.default_data
        # Add new user and contributor role to source category
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        new_user_uuid = str(uuid.uuid4())
        new_role_uuid = str(uuid.uuid4())
        remote_data['users'][str(new_user_uuid)] = {
            'sodar_uuid': new_user_uuid,
            'username': new_user_username,
            'name': 'Some Name',
            'first_name': 'Some',
            'last_name': 'Name',
            'email': 'some@example.com',
            'additional_emails': [],
            'groups': [SOURCE_USER_GROUP],
        }
        remote_data['projects'][SOURCE_CATEGORY_UUID]['roles'][
            new_role_uuid
        ] = {'user': new_user_username, 'role': PROJECT_ROLE_CONTRIBUTOR}
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(User.objects.all().count(), 3)
        new_user = User.objects.get(username=new_user_username)
        self.assertEqual(
            RoleAssignment.objects.get(
                project=self.category_obj, user=new_user
            ).role,
            self.role_contributor,
        )

    def test_update_settings_local(self):
        """Test update with local app settings (should not be updated)"""
        remote_data = self.default_data
        remote_data['app_settings'][SET_IP_RESTRICT_UUID]['global'] = False
        remote_data['app_settings'][SET_IP_ALLOWLIST_UUID]['global'] = False
        remote_data['app_settings'][SET_IP_RESTRICT_UUID]['value'] = True
        remote_data['app_settings'][SET_IP_ALLOWLIST_UUID]['value_json'] = [
            '192.168.1.1'
        ]
        og_data = deepcopy(remote_data)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        expected = {
            'name': 'ip_restrict',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '0',
            'value_json': {},
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_IP_RESTRICT_UUID, expected)
        expected = {
            'name': 'ip_allowlist',
            'type': APP_SETTING_TYPE_JSON,
            'value': None,
            'value_json': [],
            'project': self.project_obj.id,
            'app_plugin': None,
            'user': None,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_IP_ALLOWLIST_UUID, expected)
        expected = {
            'name': 'project_star',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '0',
            'value_json': {},
            'app_plugin': None,
            'project': self.project_obj.id,
            'user': self.user_target.id,
            'user_modifiable': True,
        }
        self.assert_app_setting(SET_STAR_UUID, expected)

        og_data['users'][SOURCE_USER_UUID]['status'] = 'updated'
        og_data['projects'][SOURCE_CATEGORY_UUID]['status'] = 'updated'
        og_data['projects'][SOURCE_PROJECT_UUID]['status'] = 'updated'
        og_data['app_settings'][SET_IP_RESTRICT_UUID]['status'] = 'skipped'
        og_data['app_settings'][SET_IP_ALLOWLIST_UUID]['status'] = 'skipped'
        og_data['app_settings'][SET_STAR_UUID]['status'] = 'skipped'
        self.assertEqual(remote_data, og_data)

    def test_update_settings_no_app(self):
        """Test update with app setting for app not present on target site"""
        self.assertEqual(AppSetting.objects.count(), 3)
        remote_data = self.default_data
        setting_uuid = str(uuid.uuid4())
        setting_name = 'NOT_A_VALID_SETTING'
        # Change projectroles app settings
        remote_data['app_settings'][setting_uuid] = {
            'name': setting_name,
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': False,
            'value_json': {},
            'app_plugin': 'NOT_A_VALID_APP',
            'project_uuid': SOURCE_PROJECT_UUID,
            'user_uuid': None,
            'global': True,
        }
        self.remote_api.sync_remote_data(self.source_site, remote_data)
        # Make sure setting was not set
        self.assertIsNone(AppSetting.objects.filter(name=setting_name).first())

    def test_update_settings_user(self):
        """Test update with USER scope settings"""
        # Create target settings
        target_global_setting = self.make_setting(
            plugin_name=APP_NAME,
            name='notify_email_project',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            user=self.user_target,
        )
        target_local_setting = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_str_setting',
            setting_type=APP_SETTING_TYPE_STRING,
            value='Target value',
            user=self.user_target,
        )
        self.assertEqual(AppSetting.objects.count(), 5)

        remote_data = self.default_data
        global_set_uuid = str(uuid.uuid4())
        local_set_uuid = str(uuid.uuid4())
        remote_data['app_settings'][global_set_uuid] = {
            'name': 'notify_email_project',
            'type': APP_SETTING_TYPE_BOOLEAN,
            'value': '0',
            'value_json': {},
            'app_plugin': None,
            'project_uuid': None,
            'user_uuid': SOURCE_USER_UUID,
            'user_name': SOURCE_USER_USERNAME,
            'global': True,
        }
        remote_data['app_settings'][local_set_uuid] = {
            'name': 'user_str_setting',
            'type': APP_SETTING_TYPE_STRING,
            'value': 'Source value',
            'value_json': {},
            'app_plugin': EXAMPLE_APP_NAME,
            'project_uuid': None,
            'user_uuid': SOURCE_USER_UUID,
            'user_name': SOURCE_USER_USERNAME,
            'global': False,
        }
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(AppSetting.objects.count(), 5)
        # Global setting should be updated
        target_global_setting.refresh_from_db()
        self.assertEqual(target_global_setting.value, '0')
        # Local setting value should remain as is
        target_local_setting.refresh_from_db()
        self.assertEqual(target_local_setting.value, 'Target value')
        # Assert sync data
        self.assertEqual(
            remote_data['app_settings'][global_set_uuid]['status'], 'updated'
        )
        self.assertEqual(
            remote_data['app_settings'][local_set_uuid]['status'], 'skipped'
        )

    def test_update_revoke(self):
        """Test sync with existing project data and REVOKED access"""
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        target_user2 = self.make_sodar_user(
            username=new_user_username,
            name='Some OtherName',
            first_name='Some',
            last_name='OtherName',
            email='othername@example.com',
        )
        self.make_assignment(
            self.project_obj, target_user2, self.role_contributor
        )
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        remote_data = self.default_data
        # Revoke access to project
        remote_data['projects'][SOURCE_PROJECT_UUID][
            'level'
        ] = REMOTE_LEVEL_REVOKED
        remote_data['projects'][SOURCE_PROJECT_UUID]['remote_sites'] = []
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 2)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        new_user = User.objects.get(username=new_user_username)
        with self.assertRaises(RoleAssignment.DoesNotExist):
            RoleAssignment.objects.get(
                project__sodar_uuid=SOURCE_PROJECT_UUID,
                user=new_user,
                role__name=PROJECT_ROLE_CONTRIBUTOR,
            )
        self.assertEqual(
            remote_data['projects'][SOURCE_PROJECT_UUID]['level'],
            REMOTE_LEVEL_REVOKED,
        )
        self.assertNotIn(str(new_user.sodar_uuid), remote_data['users'].keys())

    def test_delete_role(self):
        """Test sync with existing project data and removed role"""
        # Add new user and contributor role in target site
        new_user_username = 'newuser@' + SOURCE_USER_DOMAIN
        new_user = self.make_user(new_user_username)
        new_role_obj = self.make_assignment(
            self.project_obj, new_user, self.role_contributor
        )
        new_role_uuid = str(new_role_obj.sodar_uuid)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        remote_data = self.default_data
        og_data = deepcopy(remote_data)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        with self.assertRaises(RoleAssignment.DoesNotExist):
            RoleAssignment.objects.get(
                project__sodar_uuid=SOURCE_PROJECT_UUID,
                role__name=PROJECT_ROLE_CONTRIBUTOR,
            )

        og_data['projects'][SOURCE_PROJECT_UUID]['roles'][new_role_uuid] = {
            'user': new_user_username,
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'status': 'deleted',
        }
        og_data['app_settings'][SET_IP_RESTRICT_UUID]['status'] = 'skipped'
        og_data['app_settings'][SET_IP_ALLOWLIST_UUID]['status'] = 'skipped'
        og_data['app_settings'][SET_STAR_UUID]['status'] = 'skipped'
        self.assertEqual(remote_data, og_data)

    def test_update_no_changes(self):
        """Test sync with existing project data and no changes"""
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        remote_data = self.default_data
        og_data = deepcopy(remote_data)
        self.remote_api.sync_remote_data(self.source_site, remote_data)

        self.assertEqual(Project.objects.all().count(), 2)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(User.objects.all().count(), 2)
        self.assertEqual(RemoteProject.objects.all().count(), 3)
        self.assertEqual(RemoteSite.objects.all().count(), 2)

        self.category_obj.refresh_from_db()
        expected = {
            'id': self.category_obj.pk,
            'title': SOURCE_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': None,
            'public_guest_access': False,
            'archive': False,
            'full_title': SOURCE_CATEGORY_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_CATEGORY_UUID),
        }
        model_dict = model_to_dict(self.category_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.c_owner_obj.refresh_from_db()
        expected = {
            'id': self.c_owner_obj.pk,
            'project': self.category_obj.pk,
            'user': self.user_target.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.c_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.c_owner_obj), expected)

        self.project_obj.refresh_from_db()
        expected = {
            'id': self.project_obj.pk,
            'title': SOURCE_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'description': SOURCE_PROJECT_DESCRIPTION,
            'parent': self.category_obj.pk,
            'public_guest_access': False,
            'archive': False,
            'full_title': SOURCE_PROJECT_FULL_TITLE,
            'has_public_children': False,
            'sodar_uuid': uuid.UUID(SOURCE_PROJECT_UUID),
        }
        model_dict = model_to_dict(self.project_obj)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self.p_owner_obj.refresh_from_db()
        expected = {
            'id': self.p_owner_obj.pk,
            'project': self.project_obj.pk,
            'user': self.user_target.pk,
            'role': self.role_owner.pk,
            'sodar_uuid': self.p_owner_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.p_owner_obj), expected)

        remote_cat_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.category_obj.sodar_uuid
        )
        expected = {
            'id': remote_cat_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.category_obj.sodar_uuid,
            'project': self.category_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_cat_obj.date_access,
            'sodar_uuid': remote_cat_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_cat_obj), expected)

        remote_project_obj = RemoteProject.objects.get(
            site=self.source_site, project_uuid=self.project_obj.sodar_uuid
        )
        expected = {
            'id': remote_project_obj.pk,
            'site': self.source_site.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
            'level': REMOTE_LEVEL_READ_ROLES,
            'date_access': remote_project_obj.date_access,
            'sodar_uuid': remote_project_obj.sodar_uuid,
        }
        self.assertEqual(model_to_dict(remote_project_obj), expected)

        peer_site_obj = RemoteSite.objects.get(
            sodar_uuid=PEER_SITE_UUID, mode=SITE_MODE_PEER
        )
        expected = {
            'name': PEER_SITE_NAME,
            'url': PEER_SITE_URL,
            'mode': SITE_MODE_PEER,
            'description': PEER_SITE_DESC,
            'secret': None,
            'sodar_uuid': uuid.UUID(PEER_SITE_UUID),
            'user_display': PEER_SITE_USER_DISPLAY,
            'owner_modifiable': True,
        }
        peer_site_dict = model_to_dict(peer_site_obj)
        peer_site_dict.pop('id')
        self.assertEqual(peer_site_dict, expected)

        peer_project_obj = RemoteProject.objects.get(site=peer_site_obj)
        expected = {
            'site': peer_site_obj.pk,
            'project_uuid': self.project_obj.sodar_uuid,
            'project': self.project_obj.pk,
        }
        peer_project_dict = model_to_dict(peer_project_obj)
        peer_project_dict.pop('id')
        peer_project_dict.pop('sodar_uuid')
        peer_project_dict.pop('level')
        peer_project_dict.pop('date_access')
        self.assertEqual(peer_project_dict, expected)

        og_data['app_settings'][SET_IP_RESTRICT_UUID]['status'] = 'skipped'
        og_data['app_settings'][SET_IP_ALLOWLIST_UUID]['status'] = 'skipped'
        og_data['app_settings'][SET_STAR_UUID]['status'] = 'skipped'
        self.assertEqual(og_data, remote_data)

    def test_update_user_add_email(self):
        """Test sync with new additional email on user"""
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 0)
        remote_data = self.default_data
        remote_data['users'][SOURCE_USER_UUID]['additional_emails'] = [
            ADD_EMAIL
        ]
        self.remote_api.sync_remote_data(self.source_site, remote_data)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)
        email = SODARUserAdditionalEmail.objects.first()
        target_user = User.objects.get(sodar_uuid=SOURCE_USER_UUID)
        self.assertEqual(email.user, target_user)
        self.assertEqual(email.email, ADD_EMAIL)
        self.assertEqual(email.verified, True)

    def test_update_user_add_email_exists(self):
        """Test sync with existing additional email on user"""
        target_user = User.objects.get(sodar_uuid=SOURCE_USER_UUID)
        SODARUserAdditionalEmail.objects.create(
            user=target_user,
            email=ADD_EMAIL,
            verified=True,
            secret=build_secret(16),
        )
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)
        remote_data = self.default_data
        remote_data['users'][SOURCE_USER_UUID]['additional_emails'] = [
            ADD_EMAIL
        ]
        self.remote_api.sync_remote_data(self.source_site, remote_data)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)

    def test_update_user_add_email_delete(self):
        """Test sync with deleting existing additional email on user"""
        self.make_email(self.user_target, ADD_EMAIL)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)
        remote_data = self.default_data
        remote_data['users'][SOURCE_USER_UUID]['additional_emails'] = []
        self.remote_api.sync_remote_data(self.source_site, remote_data)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 0)
