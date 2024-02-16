"""UI view tests for the projectroles app"""

import json

from urllib.parse import urlencode

from django.contrib import auth
from django.contrib.messages import get_messages
from django.core import mail
from django.forms import HiddenInput
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from test_plus.test import TestCase

# Timeline dependency
from timeline.models import ProjectEvent
from timeline.tests.test_models import (
    ProjectEventMixin,
    ProjectEventStatusMixin,
)

from projectroles.app_settings import AppSettingAPI
from projectroles.forms import get_role_option, EMPTY_CHOICE_LABEL
from projectroles.models import (
    Project,
    AppSetting,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    RemoteProject,
    SODAR_CONSTANTS,
    CAT_DELIMITER,
)
from projectroles.plugins import (
    get_backend_api,
    get_active_plugins,
)
from projectroles.utils import (
    build_secret,
    get_display_name,
    get_user_display_name,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    RemoteTargetMixin,
)
from projectroles.views import (
    MSG_FORM_INVALID,
    MSG_PROJECT_WELCOME,
    MSG_USER_PROFILE_LDAP,
    MSG_INVITE_LDAP_LOCAL_VIEW,
    MSG_INVITE_LOCAL_NOT_ALLOWED,
    MSG_INVITE_LOGGED_IN_ACCEPT,
    MSG_INVITE_USER_NOT_EQUAL,
    MSG_INVITE_USER_EXISTS,
    MSG_LOGIN,
)
from projectroles.context_processors import (
    SIDEBAR_ICON_MIN_SIZE,
    SIDEBAR_ICON_MAX_SIZE,
)


app_settings = AppSettingAPI()
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
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]

# Local constants
INVITE_EMAIL = 'test@example.com'
SECRET = 'rsd886hi8276nypuvw066sbvv0rb2a6x'
TASKFLOW_SECRET_INVALID = 'Not a valid secret'
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.bihealth.org'
REMOTE_SITE_DESC = 'description'
REMOTE_SITE_SECRET = build_secret()
REMOTE_SITE_USER_DISPLAY = True
REMOTE_SITE_NEW_NAME = 'New name'
REMOTE_SITE_NEW_URL = 'https://new.url'
REMOTE_SITE_NEW_DESC = 'New description'
REMOTE_SITE_NEW_SECRET = build_secret()
EXAMPLE_APP_NAME = 'example_project_app'
INVALID_UUID = '11111111-1111-1111-1111-111111111111'
INVALID_SETTING_VALUE = 'INVALID VALUE'

HIDDEN_PROJECT_SETTINGS = [
    'settings.example_project_app.project_hidden_setting',
    'settings.example_project_app.project_hidden_json_setting',
]
UPDATED_HIDDEN_SETTING = 'Updated value'
UPDATED_HIDDEN_JSON_SETTING = {'updated': 'value'}

PROJECTROLES_APP_SETTINGS_TEST_LOCAL = {
    'test_setting': {
        'scope': APP_SETTING_SCOPE_PROJECT,  # PROJECT/USER
        'type': 'BOOLEAN',  # STRING/INTEGER/BOOLEAN
        'default': False,
        'label': 'Test setting',  # Optional, defaults to name/key
        'description': 'Test setting',  # Optional
        'user_modifiable': True,  # Optional, show/hide in forms
        'local': False,
    },
    'test_setting_local': {
        'scope': APP_SETTING_SCOPE_PROJECT,  # PROJECT/USER
        'type': 'BOOLEAN',  # STRING/INTEGER/BOOLEAN
        'default': False,
        'label': 'Test setting',  # Optional, defaults to name/key
        'description': 'Test setting',  # Optional
        'user_modifiable': True,  # Optional, show/hide in forms
        'local': True,
    },
    'project_star': {  # NOTE: We have to include this for view tests
        'scope': APP_SETTING_SCOPE_PROJECT_USER,
        'type': 'BOOLEAN',
        'default': False,
        'local': False,
    },
}

EX_PROJECT_UI_SETTINGS = [
    'project_str_setting',
    'project_int_setting',
    'project_str_setting_options',
    'project_int_setting_options',
    'project_bool_setting',
    'project_json_setting',
    'project_callable_setting',
    'project_callable_setting_options',
]


class TestViewsBase(RoleMixin, TestCase):
    """Base class for view testing"""

    def setUp(self):
        # Init roles
        self.init_roles()
        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()


# General view tests -----------------------------------------------------------


class TestHomeView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for HomeView"""

    def setUp(self):
        super().setUp()
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.url = reverse('home')

    def test_get(self):
        """Test HomeView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        custom_cols = response.context['project_custom_cols']
        self.assertEqual(len(custom_cols), 2)
        self.assertEqual(custom_cols[0]['column_id'], 'links')
        self.assertEqual(response.context['project_col_count'], 4)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_context_sidebar_icon_size(self):
        """Test GET context for sidebar icon size"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(response.context['sidebar_icon_size'], 36)

    @override_settings(PROJECTROLES_SIDEBAR_ICON_SIZE=SIDEBAR_ICON_MIN_SIZE - 2)
    def test_get_context_sidebar_icon_size_min(self):
        """Test GET context for sidebar icon size with value below minimum"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(
                response.context['sidebar_icon_size'],
                SIDEBAR_ICON_MIN_SIZE,
            )

    @override_settings(PROJECTROLES_SIDEBAR_ICON_SIZE=SIDEBAR_ICON_MAX_SIZE + 2)
    def test_get_context_sidebar_icon_size_max(self):
        """Test GET context for sidebar icon size with value over max"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(
                response.context['sidebar_icon_size'],
                SIDEBAR_ICON_MAX_SIZE,
            )

    def test_get_context_sidebar_notch_pos(self):
        """Test GET context for siderbar notch position"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(response.context['sidebar_notch_pos'], 12)

    def test_get_context_sidebar_notch_size(self):
        """Test GET context for sidebar notch size"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(response.context['sidebar_notch_size'], 12)

    @override_settings(PROJECTROLES_SIDEBAR_ICON_SIZE=SIDEBAR_ICON_MIN_SIZE)
    def test_get_context_sidebar_notch_size_min(self):
        """Test GET context for sidebar notch size with minimum icon size"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(response.context['sidebar_notch_size'], 9)

    def test_get_context_sidebar_padding(self):
        """Test GET context for sidebar padding"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(response.context['sidebar_padding'], 8)

    @override_settings(PROJECTROLES_SIDEBAR_ICON_SIZE=SIDEBAR_ICON_MAX_SIZE)
    def test_get_context_sidebar_padding_max(self):
        """Test GET context for sidebar padding with maximum icon size"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(response.context['sidebar_padding'], 10)

    @override_settings(PROJECTROLES_SIDEBAR_ICON_SIZE=SIDEBAR_ICON_MIN_SIZE)
    def test_get_context_sidebar_padding_min(self):
        """Test GET context for sidebar padding with minimum icon size"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertEqual(response.context['sidebar_padding'], 4)


class TestProjectSearchResultsView(
    ProjectMixin,
    RoleAssignmentMixin,
    TestViewsBase,
    ProjectEventMixin,
    ProjectEventStatusMixin,
):
    """Tests for ProjectSearchResultsView"""

    def setUp(self):
        super().setUp()
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.plugins = get_active_plugins(plugin_type='project_app')

    def test_get(self):
        """Test ProjectSearchResultsView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['test'])
        self.assertEqual(response.context['search_keywords'], {})
        self.assertEqual(response.context['search_type'], None)
        self.assertEqual(response.context['search_input'], 'test')
        self.assertEqual(
            len(response.context['app_results']),
            len([p for p in self.plugins if p.search_enable]),
        )

    def test_get_search_type(self):
        """Test GET with search type"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search')
                + '?'
                + urlencode({'s': 'test type:file'})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['test'])
        self.assertEqual(response.context['search_keywords'], {})
        self.assertEqual(response.context['search_type'], 'file')
        self.assertEqual(response.context['search_input'], 'test type:file')
        self.assertEqual(
            len(response.context['app_results']),
            len(
                [
                    p
                    for p in self.plugins
                    if (
                        p.search_enable
                        and response.context['search_type'] in p.search_types
                    )
                ]
            ),
        )

    def test_get_non_text_input(self):
        """Test GET with non-text input from standard search (should redirect)"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?s=+++'
            )
            self.assertRedirects(response, reverse('home'))

    def test_get_finder(self):
        """Test GET as finder"""
        user_finder = self.make_user('user_finder')
        finder_cat = self.make_project(
            'FinderCategory', PROJECT_TYPE_CATEGORY, self.category
        )
        self.make_assignment(finder_cat, self.user, self.role_owner)
        self.make_assignment(finder_cat, user_finder, self.role_finder)
        finder_project = self.make_project(
            'FinderProject', PROJECT_TYPE_PROJECT, finder_cat
        )
        self.make_assignment(finder_project, self.user, self.role_owner)
        with self.login(user_finder):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['project_results']), 1)
        self.assertEqual(response.context['project_results'][0], finder_project)

    def test_post_advanced(self):
        """Test POST from ProjectAdvancedSearchView"""
        new_project = self.make_project(
            'AnotherProject',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='xxx',
        )
        self.cat_owner_as = self.make_assignment(
            new_project, self.user, self.role_owner
        )
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:search_advanced'),
                data={'m': 'testproject\r\nxxx', 'k': ''},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['search_terms'], ['testproject', 'xxx']
        )
        self.assertEqual(response.context['search_keywords'], {})
        self.assertEqual(response.context['search_type'], None)
        self.assertEqual(len(response.context['project_results']), 2)

    def test_post_advanced_short_input(self):
        """Test POST with short term (< 3 characters)"""
        new_project = self.make_project(
            'AnotherProject',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='xxx',
        )
        self.cat_owner_as = self.make_assignment(
            new_project, self.user, self.role_owner
        )
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:search_advanced'),
                data={'m': 'testproject\r\nxx', 'k': ''},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['testproject'])
        self.assertEqual(len(response.context['project_results']), 1)

    def test_post_advanced_empty_input(self):
        """Test POST with empty term (should be ignored)"""
        new_project = self.make_project(
            'AnotherProject',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='xxx',
        )
        self.cat_owner_as = self.make_assignment(
            new_project, self.user, self.role_owner
        )
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:search_advanced'),
                data={'m': 'testproject\r\nxxx', 'k': ''},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['search_terms'], ['testproject', 'xxx']
        )
        self.assertEqual(len(response.context['project_results']), 2)

    def test_post_advanced_dupe(self):
        """Test POST with duplicate term"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:search_advanced'),
                data={'m': 'xxx\r\nxxx', 'k': ''},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_terms'], ['xxx'])

    @override_settings(PROJECTROLES_ENABLE_SEARCH=False)
    def test_get_disabled(self):
        """Test GET with disabled search"""
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
            self.assertRedirects(response, reverse('home'))

    def test_get_omit_app(self):
        """Test GET with omitted app"""
        self.event = self.make_event(
            project=self.project,
            app='projectroles',
            user=self.user,
            event_name='test_event',
            description='description',
            classified=False,
            extra_data={'test_key': 'test_val'},
        )
        self.make_event_status(
            event=self.event,
            status_type='SUBMIT',
            description='SUBMIT',
            extra_data={'test_key': 'test_val'},
        )
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['app_results']), 2)
        with override_settings(PROJECTROLES_SEARCH_OMIT_APPS=['timeline']):
            with self.login(self.user):
                response = self.client.get(
                    reverse('projectroles:search')
                    + '?'
                    + urlencode({'s': 'test'})
                )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['app_results']), 1)


class TestProjectAdvancedSearchView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for ProjectAdvancedSearchView"""

    def test_get(self):
        """Test ProjectAdvancedSearchView GET"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:search_advanced'))
        self.assertEqual(response.status_code, 200)

    @override_settings(PROJECTROLES_ENABLE_SEARCH=False)
    def test_get_disabled(self):
        """Test GET with disabled search"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:search_advanced'))
            self.assertRedirects(response, reverse('home'))


class TestProjectDetailView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for ProjectDetailView"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_get(self):
        """Test ProjectDetailView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].pk, self.project.pk)

    def test_get_not_found(self):
        """Test GET with invalid UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


class TestProjectCreateView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for ProjectCreateView"""

    def setUp(self):
        super().setUp()
        self.app_alert_model = get_backend_api('appalerts_backend').get_model()

    def test_get_top(self):
        """Test ProjectCreateView GET with top level category creation form"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:create'))
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(form.initial['type'], PROJECT_TYPE_CATEGORY)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertEqual(form.initial['owner'], self.user)

    @override_settings(PROJECTROLES_DISABLE_CATEGORIES=True)
    def test_get_top_disable_categories(self):
        """Test GET with top level and categories disabled"""
        with self.login(self.user):
            response = self.client.get(reverse('projectroles:create'))
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(form.initial['type'], PROJECT_TYPE_PROJECT)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertEqual(form.initial['owner'], self.user)

    def test_get_sub(self):
        """Test GET under category"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.user, self.role_owner)
        # Create another user to enable checking for owner selection
        self.make_user('user_new')

        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(
            form.fields['type'].choices,
            [
                (None, EMPTY_CHOICE_LABEL),
                (
                    PROJECT_TYPE_CATEGORY,
                    get_display_name(PROJECT_TYPE_CATEGORY, title=True),
                ),
                (
                    PROJECT_TYPE_PROJECT,
                    get_display_name(PROJECT_TYPE_PROJECT, title=True),
                ),
            ],
        )
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertEqual(form.initial['owner'], self.user)

    def test_get_cat_member(self):
        """Test GET under category as category non-owner"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.user, self.role_owner)
        new_user = self.make_user('user_new')
        self.make_assignment(category, new_user, self.role_contributor)

        with self.login(new_user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        # Current user should be the initial value for owner
        self.assertEqual(form.initial['owner'], new_user)

    def test_get_project(self):
        """Test GET under project (should fail)"""
        project = self.make_project('TestProject', PROJECT_TYPE_PROJECT, None)
        self.make_assignment(project, self.user, self.role_owner)
        self.make_user('user_new')
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 302)

    def test_get_not_found(self):
        """Test GET with invalid parent UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_get_parent_owner(self):
        """Test GET with parent owner as initial value"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        user_new = self.make_user('user_new')
        self.make_assignment(category, user_new, self.role_owner)
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.initial['owner'], user_new)

    def test_post_top_level_category(self):
        """Test POST for top level category"""
        self.assertEqual(Project.objects.all().count(), 0)
        values = {
            'title': 'TestCategory',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'owner': self.user.sodar_uuid,
            'description': 'description',
            'public_guest_access': False,
        }
        # Add settings values
        values.update(
            app_settings.get_defaults(APP_SETTING_SCOPE_PROJECT, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(reverse('projectroles:create'), values)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 1)
        project = Project.objects.first()
        self.assertIsNotNone(project)
        # Same user so no alerts or emails
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': project.pk,
            'title': 'TestCategory',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': 'description',
            'public_guest_access': False,
            'archive': False,
            'full_title': 'TestCategory',
            'has_public_children': False,
            'sodar_uuid': project.sodar_uuid,
        }
        model_dict = model_to_dict(project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # Assert settings comparison
        settings = AppSetting.objects.filter(project=project)
        self.assertEqual(settings.count(), 1)
        setting = settings.first()
        self.assertEqual(setting.name, 'project_category_bool_setting')

        # Assert owner role assignment
        owner_as = RoleAssignment.objects.get(
            project=project, role=self.role_owner
        )
        expected = {
            'id': owner_as.pk,
            'project': project.pk,
            'role': self.role_owner.pk,
            'user': self.user.pk,
            'sodar_uuid': owner_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(owner_as), expected)
        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                ),
            )

    def test_post_project(self):
        """Test POST for project creation"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.user, self.role_owner)

        # Create project
        values = {
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.sodar_uuid,
            'owner': self.user.sodar_uuid,
            'description': 'description',
            'public_guest_access': False,
        }
        # Add settings values
        values.update(
            app_settings.get_defaults(APP_SETTING_SCOPE_PROJECT, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 2)
        project = Project.objects.get(type=PROJECT_TYPE_PROJECT)
        # No alerts or emails should be sent as the same user triggered this
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': project.pk,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.pk,
            'description': 'description',
            'public_guest_access': False,
            'archive': False,
            'full_title': 'TestCategory / TestProject',
            'has_public_children': False,
            'sodar_uuid': project.sodar_uuid,
        }
        model_dict = model_to_dict(project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # Assert settings comparison
        project_settings = [
            'project_bool_setting',
            'project_callable_setting',
            'project_callable_setting_options',
            'project_global_setting',
            'project_hidden_json_setting',
            'project_hidden_setting',
            'project_int_setting',
            'project_int_setting_options',
            'project_json_setting',
            'project_str_setting',
            'project_str_setting_options',
            'allow_public_links',
            'ip_allowlist',
            'ip_restrict',
        ]
        settings = AppSetting.objects.filter(project=project)
        self.assertEqual(settings.count(), 14)
        for setting in settings:
            self.assertIn(setting.name, project_settings)

        # Assert owner role assignment
        owner_as = RoleAssignment.objects.get(
            project=project, role=self.role_owner
        )
        expected = {
            'id': owner_as.pk,
            'project': project.pk,
            'role': self.role_owner.pk,
            'user': self.user.pk,
            'sodar_uuid': owner_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(owner_as), expected)

    def test_post_project_cat_member(self):
        """Test POST for project as category member"""
        # Create category and add new user as member
        category = self.make_project(
            title='TestCategory', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        self.make_assignment(category, self.user, self.role_owner)
        new_user = self.make_user('user_new')
        self.make_assignment(category, new_user, self.role_contributor)

        values = {
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.sodar_uuid,
            'owner': new_user.sodar_uuid,
            'description': 'description',
            'public_guest_access': False,
        }
        values.update(
            app_settings.get_defaults(APP_SETTING_SCOPE_PROJECT, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                ),
                values,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 2)
        project = Project.objects.get(type=PROJECT_TYPE_PROJECT)
        self.assertEqual(project.get_owner().user, new_user)
        # Alert and email for parent owner should be created
        self.assertEqual(self.app_alert_model.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_project_title_delimiter(self):
        """Test POST for project with category delimiter in title (should fail)"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.user, self.role_owner)
        self.assertEqual(Project.objects.all().count(), 1)
        values = {
            'title': 'Test{}Project'.format(CAT_DELIMITER),
            'type': PROJECT_TYPE_PROJECT,
            'parent': category.sodar_uuid,
            'owner': self.user.sodar_uuid,
            'description': 'description',
            'public_guest_access': False,
        }
        values.update(
            app_settings.get_defaults(APP_SETTING_SCOPE_PROJECT, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:create',
                    kwargs={'project': category.sodar_uuid},
                ),
                values,
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.all().count(), 1)


class TestProjectUpdateView(
    ProjectMixin, RoleAssignmentMixin, RemoteTargetMixin, TestViewsBase
):
    """Tests for ProjectUpdateView"""

    @classmethod
    def _get_post_app_settings(cls, project, user):
        """Get postable app settings for project of type PROJECT"""
        if project.type != PROJECT_TYPE_PROJECT:
            raise ValueError('Can only be called for a project')
        ps = app_settings.get_all(project=project, post_safe=True)
        # Omit hidden settings for regular user
        if user and not user.is_superuser:
            ps = {k: ps[k] for k in ps if k not in HIDDEN_PROJECT_SETTINGS}
        # Edit settings to non-default values
        ps['settings.example_project_app.project_int_setting'] = 1
        ps['settings.example_project_app.project_str_setting'] = 'test'
        ps['settings.example_project_app.project_bool_setting'] = True
        ps['settings.example_project_app.project_json_setting'] = '{}'
        ps[
            'settings.example_project_app.project_callable_setting'
        ] = 'No project or user for callable'
        ps[
            'settings.example_project_app.project_callable_setting_options'
        ] = str(project.sodar_uuid)
        ps['settings.projectroles.ip_restrict'] = True
        ps['settings.projectroles.ip_allowlist'] = '["192.168.1.1"]'
        return ps

    def _assert_app_settings(self, post_settings):
        """Assert app settings values to match data after POST"""
        for k, v in post_settings.items():
            v_json = None
            try:
                v_json = json.loads(v)
            except Exception:
                pass
            s = app_settings.get(
                k.split('.')[1],
                k.split('.')[2],
                project=self.project,
                post_safe=True,
            )
            if isinstance(v_json, (dict, list)):
                self.assertEqual(json.loads(s), v_json)
            else:
                self.assertEqual(s, v)

    def setUp(self):
        super().setUp()
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.app_alert_model = get_backend_api('appalerts_backend').get_model()
        self.url = reverse(
            'projectroles:update',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:update',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_get_project(self):
        """Test GET with project"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertNotIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertIsInstance(form.fields['owner'].widget, HiddenInput)

    def test_get_no_parent_role(self):
        """Test GET for current parent selectability without parent role"""
        # Create new user and project, make new user the owner
        user_new = self.make_user('user_new')
        self.owner_as.user = user_new
        self.owner_as.save()
        # Create another category with new user as owner
        category2 = self.make_project(
            'TestCategory2', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category2, user_new, self.role_owner)

        with self.login(user_new):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        # Ensure self.category (with no user_new rights) is initial
        self.assertEqual(form.initial['parent'], self.category.sodar_uuid)
        self.assertEqual(len(form.fields['parent'].choices), 2)

    def test_post_project_superuser(self):
        """Test POST for project as superuser"""
        timeline = get_backend_api('timeline_backend')
        new_category = self.make_project('NewCat', PROJECT_TYPE_CATEGORY, None)
        self.make_assignment(new_category, self.user, self.role_owner)
        self.assertEqual(Project.objects.all().count(), 3)

        values = model_to_dict(self.project)
        values['title'] = 'updated title'
        values['description'] = 'updated description'
        values['parent'] = new_category.sodar_uuid  # NOTE: Updated parent
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
        # Add settings values
        ps = self._get_post_app_settings(self.project, self.user)
        values.update(ps)
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(Project.objects.all().count(), 3)
        self.project.refresh_from_db()
        # No alert or mail, because the owner has not changed
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': self.project.pk,
            'title': 'updated title',
            'type': PROJECT_TYPE_PROJECT,
            'parent': new_category.pk,
            'description': 'updated description',
            'public_guest_access': False,
            'archive': False,
            'full_title': new_category.title + CAT_DELIMITER + 'updated title',
            'has_public_children': False,
            'sodar_uuid': self.project.sodar_uuid,
        }
        model_dict = model_to_dict(self.project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # Assert settings
        self._assert_app_settings(ps)
        # Assert hidden settings
        hidden_val = app_settings.get(
            'example_project_app',
            'project_hidden_setting',
            project=self.project,
        )
        self.assertEqual(hidden_val, '')
        hidden_json = app_settings.get(
            'example_project_app',
            'project_hidden_json_setting',
            project=self.project,
        )
        self.assertEqual(hidden_json, {})

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )
        # Assert timeline event
        tl_event = (
            timeline.get_project_events(self.project).order_by('-pk').first()
        )
        self.assertEqual(tl_event.event_name, 'project_update')
        self.assertIn('title', tl_event.extra_data)
        self.assertIn('description', tl_event.extra_data)
        self.assertIn('parent', tl_event.extra_data)

    def test_post_project_regular_user(self):
        """Test POST as regular user"""
        # Create new user and set as self.project owner
        user_new = self.make_user('user_new')
        self.owner_as.user = user_new
        self.owner_as.save()
        # Set hidden setting values
        app_settings.set(
            'example_project_app',
            'project_hidden_setting',
            UPDATED_HIDDEN_SETTING,
            project=self.project,
        )
        app_settings.set(
            'example_project_app',
            'project_hidden_json_setting',
            UPDATED_HIDDEN_JSON_SETTING,
            project=self.project,
        )
        # Make new category
        new_category = self.make_project('NewCat', PROJECT_TYPE_CATEGORY, None)
        self.make_assignment(new_category, user_new, self.role_owner)
        self.assertEqual(Project.objects.all().count(), 3)

        values = model_to_dict(self.project)
        values['title'] = 'updated title'
        values['description'] = 'updated description'
        values['parent'] = new_category.sodar_uuid
        values['owner'] = user_new.sodar_uuid
        ps = self._get_post_app_settings(self.project, user_new)
        values.update(ps)
        with self.login(user_new):
            self.client.post(self.url, values)

        self.assertEqual(Project.objects.all().count(), 3)
        self.project.refresh_from_db()
        expected = {
            'id': self.project.pk,
            'title': 'updated title',
            'type': PROJECT_TYPE_PROJECT,
            'parent': new_category.pk,
            'description': 'updated description',
            'public_guest_access': False,
            'archive': False,
            'full_title': new_category.title + CAT_DELIMITER + 'updated title',
            'has_public_children': False,
            'sodar_uuid': self.project.sodar_uuid,
        }
        model_dict = model_to_dict(self.project)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        self._assert_app_settings(ps)
        # Hidden settings should remain as they were not changed
        hidden_val = app_settings.get(
            'example_project_app',
            'project_hidden_setting',
            project=self.project,
        )
        self.assertEqual(hidden_val, UPDATED_HIDDEN_SETTING)
        hidden_json = app_settings.get(
            'example_project_app',
            'project_hidden_json_setting',
            project=self.project,
        )
        self.assertEqual(hidden_json, UPDATED_HIDDEN_JSON_SETTING)

    def test_post_project_title_delimiter(self):
        """Test POST with category delimiter in title (should fail)"""
        # TODO: Add values getter as a helper
        values = model_to_dict(self.project)
        values['parent'] = self.category.sodar_uuid
        values['owner'] = self.user.sodar_uuid
        values['title'] = 'Project{}Title'.format(CAT_DELIMITER)
        # Add settings values
        values.update(
            app_settings.get_all(project=self.project, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'TestProject')

    def test_post_project_custom_validation(self):
        """Test POST with custom validation and invalid value (should fail)"""
        values = model_to_dict(self.project)
        values['parent'] = self.category.sodar_uuid
        values['owner'] = self.user.sodar_uuid
        values.update(
            app_settings.get_all(project=self.project, post_safe=True)
        )
        values[
            'settings.example_project_app.project_str_setting'
        ] = INVALID_SETTING_VALUE
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_FORM_INVALID,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            '',
        )

    def test_post_project_public_access(self):
        """Test POST with public guest access"""
        self.assertEqual(self.project.public_guest_access, False)
        self.assertEqual(self.category.has_public_children, False)

        values = model_to_dict(self.project)
        values['public_guest_access'] = True
        values['parent'] = self.category.sodar_uuid  # NOTE: Must add parent
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
        values.update(
            app_settings.get_all(project=self.project, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.category.refresh_from_db()
        self.assertEqual(self.project.public_guest_access, True)
        # Assert the parent category has_public_children is set true
        self.assertEqual(self.category.has_public_children, True)

    def test_get_category(self):
        """Test GET with category"""
        with self.login(self.user):
            response = self.client.get(self.url_cat)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertNotIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertIsInstance(form.fields['owner'].widget, HiddenInput)

    def test_post_category(self):
        """Test POST with category"""
        self.assertEqual(Project.objects.all().count(), 2)
        values = model_to_dict(self.category)
        values['title'] = 'updated title'
        values['description'] = 'updated description'
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
        values['parent'] = ''
        # Add settings values
        values.update(
            app_settings.get_all(project=self.category, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(self.url_cat, values)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Project.objects.all().count(), 2)
        self.category.refresh_from_db()
        self.assertIsNotNone(self.category)
        # Ensure no alert or email (owner not updated)
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        expected = {
            'id': self.category.pk,
            'title': 'updated title',
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': 'updated description',
            'public_guest_access': False,
            'archive': False,
            'full_title': 'updated title',
            'has_public_children': False,
            'sodar_uuid': self.category.sodar_uuid,
        }
        model_dict = model_to_dict(self.category)
        model_dict.pop('readme', None)
        self.assertEqual(model_dict, expected)

        # Assert settings comparison
        settings = AppSetting.objects.filter(project=self.category)
        self.assertEqual(settings.count(), 1)
        setting = settings.first()
        self.assertEqual(setting.name, 'project_category_bool_setting')
        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.category.sodar_uuid},
                ),
            )

    def test_post_category_parent(self):
        """Test POST with updated category parent"""
        new_category = self.make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(new_category, self.user, self.role_owner)
        self.assertEqual(
            self.category.full_title,
            self.category.title,
        )
        self.assertEqual(
            self.project.full_title,
            self.category.title + ' / ' + self.project.title,
        )

        values = model_to_dict(self.category)
        values['title'] = self.category.title
        values['description'] = self.category.description
        values['owner'] = self.user.sodar_uuid  # NOTE: Must add owner
        values['parent'] = new_category.sodar_uuid  # Updated category
        # Add settings values
        values.update(
            app_settings.get_all(project=self.category, post_safe=True)
        )
        with self.login(self.user):
            response = self.client.post(self.url_cat, values)

        self.assertEqual(response.status_code, 302)
        # Assert category state and project title after update
        self.category.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.category.parent, new_category)
        self.assertEqual(
            self.category.full_title,
            new_category.title + ' / ' + self.category.title,
        )
        self.assertEqual(
            self.project.full_title,
            new_category.title
            + ' / '
            + self.category.title
            + ' / '
            + self.project.title,
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_remote(self):
        """Test GET with remote project as target"""
        self.set_up_as_target(projects=[self.category, self.project])
        with self.login(self.user):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['title'].widget, HiddenInput)
        self.assertIsInstance(form.fields['type'].widget, HiddenInput)
        self.assertIsInstance(form.fields['parent'].widget, HiddenInput)
        self.assertIsInstance(form.fields['description'].widget, HiddenInput)
        self.assertIsInstance(form.fields['readme'].widget, HiddenInput)
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_str_setting'
            ].widget,
            HiddenInput,
        )
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_int_setting'
            ].widget,
            HiddenInput,
        )
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_bool_setting'
            ].widget,
            HiddenInput,
        )
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_callable_setting'
            ].widget,
            HiddenInput,
        )
        self.assertNotIsInstance(
            form.fields[
                'settings.example_project_app.project_callable_setting_options'
            ].widget,
            HiddenInput,
        )
        self.assertTrue(
            form.fields['settings.projectroles.ip_restrict'].disabled
        )
        self.assertTrue(
            form.fields['settings.projectroles.ip_allowlist'].disabled
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_post_remote(self):
        """Test POST with remote project as target"""
        self.set_up_as_target(projects=[self.category, self.project])
        values = model_to_dict(self.project)
        values['owner'] = self.user.sodar_uuid
        values['parent'] = self.category.sodar_uuid
        values['settings.example_project_app.project_int_setting'] = 0
        values['settings.example_project_app.project_int_setting_options'] = 0
        values['settings.example_project_app.project_str_setting'] = 'test'
        values[
            'settings.example_project_app.project_str_setting_options'
        ] = 'string1'
        values['settings.example_project_app.project_bool_setting'] = True
        values[
            'settings.example_project_app.project_callable_setting'
        ] = 'No project or user for callable'
        values[
            'settings.example_project_app.project_callable_setting_options'
        ] = str(self.project.sodar_uuid)
        values['settings.projectroles.ip_restrict'] = True
        values['settings.projectroles.ip_allowlist'] = '["192.168.1.1"]'
        self.assertEqual(Project.objects.all().count(), 2)
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.all().count(), 2)

    def test_get_not_found(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:update',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


class TestProjectArchiveView(
    ProjectMixin, RoleAssignmentMixin, RemoteTargetMixin, TestViewsBase
):
    """Tests for ProjectArchiveView"""

    @classmethod
    def _get_tl(cls):
        return ProjectEvent.objects.filter(event_name='project_archive')

    @classmethod
    def _get_tl_un(cls):
        return ProjectEvent.objects.filter(event_name='project_unarchive')

    def _get_alerts(self):
        return self.app_alert_model.objects.filter(alert_name='project_archive')

    def _get_alerts_un(self):
        return self.app_alert_model.objects.filter(
            alert_name='project_unarchive'
        )

    def setUp(self):
        super().setUp()
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.user_contributor = self.make_user('user_contributor')
        self.contributor_as = self.make_assignment(
            self.project, self.user_contributor, self.role_contributor
        )
        self.app_alert_model = get_backend_api('appalerts_backend').get_model()
        self.url = reverse(
            'projectroles:archive',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:archive',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectArchiveView GET with project"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_category(self):
        """Test GET with category (should fail)"""
        with self.login(self.user):
            response = self.client.get(self.url_cat)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.category.sodar_uuid},
                ),
            )

    def test_post(self):
        """Test ProjectArchiveView POST"""
        self.assertEqual(self.project.archive, False)
        self.assertEqual(self._get_tl().count(), 0)
        self.assertEqual(self._get_tl_un().count(), 0)
        self.assertEqual(self._get_alerts().count(), 0)
        self.assertEqual(self._get_alerts_un().count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        values = {'status': True}
        with self.login(self.user):
            response = self.client.post(self.url, values)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

        self.project.refresh_from_db()
        self.assertEqual(self.project.archive, True)
        self.assertEqual(self._get_tl().count(), 1)
        self.assertEqual(self._get_tl_un().count(), 0)
        # Only the contributor should receive an alert
        self.assertEqual(self._get_alerts().count(), 1)
        self.assertEqual(self._get_alerts_un().count(), 0)
        self.assertEqual(self._get_alerts().first().user, self.user_contributor)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_unarchive(self):
        """Test POST to unarchiving project"""
        self.project.set_archive()
        self.assertEqual(self._get_tl().count(), 0)
        self.assertEqual(self._get_tl_un().count(), 0)
        self.assertEqual(self._get_alerts().count(), 0)
        self.assertEqual(self._get_alerts_un().count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        values = {'status': False}
        with self.login(self.user):
            self.client.post(self.url, values)

        self.project.refresh_from_db()
        self.assertEqual(self.project.archive, False)
        self.assertEqual(self._get_tl().count(), 0)
        self.assertEqual(self._get_tl_un().count(), 1)
        self.assertEqual(self._get_alerts().count(), 0)
        self.assertEqual(self._get_alerts_un().count(), 1)
        self.assertEqual(
            self._get_alerts_un().first().user, self.user_contributor
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_post_project_archived(self):
        """Test POST with already archived project"""
        self.project.set_archive()
        self.assertEqual(self._get_tl().count(), 0)
        self.assertEqual(self._get_tl_un().count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        values = {'status': True}
        with self.login(self.user):
            self.client.post(self.url, values)
        self.project.refresh_from_db()
        self.assertEqual(self.project.archive, True)
        self.assertEqual(self._get_tl().count(), 0)
        self.assertEqual(self._get_alerts().count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_category(self):
        """Test POST with category (should fail)"""
        self.assertEqual(self.category.archive, False)
        self.assertEqual(self._get_tl().count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        values = {'status': True}
        with self.login(self.user):
            response = self.client.post(self.url_cat, values)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.category.sodar_uuid},
                ),
            )
        self.category.refresh_from_db()
        self.assertEqual(self.category.archive, False)
        self.assertEqual(self._get_tl().count(), 0)
        self.assertEqual(self._get_alerts().count(), 0)
        self.assertEqual(len(mail.outbox), 0)


class TestProjectForm(
    AppSettingMixin, TestViewsBase, ProjectMixin, RoleAssignmentMixin
):
    """Tests for ProjectForm"""

    def setUp(self):
        super().setUp()
        # Init user & role
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.url = reverse(
            'projectroles:update',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test GET for settings values"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])
        fields = response.context['form'].fields
        for s in EX_PROJECT_UI_SETTINGS:
            self.assertIsNotNone(fields['settings.example_project_app.' + s])
        field = fields['settings.example_project_app.project_str_setting']
        self.assertEqual(field.widget.attrs['placeholder'], 'Example string')
        field = fields['settings.example_project_app.project_int_setting']
        self.assertEqual(field.widget.attrs['placeholder'], 0)
        self.assertIsNotNone(fields['settings.projectroles.ip_restrict'])
        self.assertIsNotNone(fields['settings.projectroles.ip_allowlist'])

    def test_post(self):
        """Test POST to modify settings values"""
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            '',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            0,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string1',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            0,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            False,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )
        self.assertEqual(
            app_settings.get(
                'projectroles', 'ip_restrict', project=self.project
            ),
            False,
        )
        self.assertEqual(
            app_settings.get(
                'projectroles', 'ip_allowlist', project=self.project
            ),
            [],
        )

        values = {
            'settings.example_project_app.project_str_setting': 'updated',
            'settings.example_project_app.project_int_setting': 170,
            'settings.example_project_app.'
            'project_str_setting_options': 'string2',
            'settings.example_project_app.project_int_setting_options': 1,
            'settings.example_project_app.project_bool_setting': True,
            'settings.example_project_app.'
            'project_json_setting': '{"Test": "Updated"}',
            'settings.example_project_app.'
            'project_callable_setting_options': str(self.project.sodar_uuid),
            'settings.projectroles.ip_restrict': True,
            'settings.projectroles.ip_allowlist': '["192.168.1.1"]',
            'owner': self.user.sodar_uuid,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )
        # Assert settings state after update
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            'updated',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            170,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string2',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            1,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Test': 'Updated'},
        )
        self.assertEqual(
            app_settings.get(
                'projectroles', 'ip_restrict', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get(
                'projectroles', 'ip_allowlist', project=self.project
            ),
            ['192.168.1.1'],
        )


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestProjectFormTarget(
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    TestViewsBase,
    ProjectMixin,
    RoleAssignmentMixin,
):
    """Tests for project create/update form on a target site"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.url = reverse(
            'projectroles:update',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test GET for settings values"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])
        fields = response.context['form'].fields
        for s in EX_PROJECT_UI_SETTINGS:
            self.assertIsNotNone(fields['settings.example_project_app.' + s])
        self.assertIsNotNone(fields['settings.projectroles.ip_restrict'])
        self.assertTrue(fields['settings.projectroles.ip_restrict'].disabled)
        self.assertIsNotNone(fields['settings.projectroles.ip_allowlist'])
        self.assertTrue(fields['settings.projectroles.ip_allowlist'].disabled)

    def test_post(self):
        """Test POST to modify settings values as target"""
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            '',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            0,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string1',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            0,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            False,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )

        values = {
            'settings.example_project_app.project_str_setting': 'updated',
            'settings.example_project_app.project_int_setting': 170,
            'settings.example_project_app.'
            'project_str_setting_options': 'string2',
            'settings.example_project_app.project_int_setting_options': 1,
            'settings.example_project_app.project_bool_setting': True,
            'settings.example_project_app.'
            'project_json_setting': '{"Test": "Updated"}',
            'settings.example_project_app.'
            'project_callable_setting': 'No project or user for callable',
            'settings.example_project_app.'
            'project_callable_setting_options': str(self.project.sodar_uuid),
            'owner': self.user.sodar_uuid,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )
        # Assert settings state after update
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            'updated',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            170,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string2',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            1,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Test': 'Updated'},
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_callable_setting',
                project=self.project,
            ),
            'No project or user for callable',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_callable_setting_options',
                project=self.project,
            ),
            str(self.project.sodar_uuid),
        )


@override_settings(
    PROJECTROLES_SITE_MODE=SITE_MODE_TARGET,
    PROJECTROLES_APP_SETTINGS_TEST=PROJECTROLES_APP_SETTINGS_TEST_LOCAL,
)
class TestProjectFormTargetLocal(
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    TestViewsBase,
    ProjectMixin,
    RoleAssignmentMixin,
):
    """
    Tests for project create/update form on target site with local settings
    """

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.url = reverse(
            'projectroles:update',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test GET for settings values as target"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])
        fields = response.context['form'].fields
        for s in EX_PROJECT_UI_SETTINGS:
            self.assertIsNotNone(fields['settings.example_project_app.' + s])
        self.assertIsNotNone(fields['settings.projectroles.test_setting_local'])
        self.assertFalse(
            fields['settings.projectroles.test_setting_local'].disabled
        )
        self.assertIsNotNone(fields['settings.projectroles.test_setting'])
        self.assertTrue(fields['settings.projectroles.test_setting'].disabled)

    def test_post(self):
        """Test POST to modify settings values as target"""
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            '',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            0,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string1',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            0,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            False,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )
        self.assertEqual(
            app_settings.get(
                'projectroles', 'test_setting', project=self.project
            ),
            False,
        )

        values = {
            'settings.example_project_app.project_str_setting': 'updated',
            'settings.example_project_app.project_int_setting': 170,
            'settings.example_project_app.'
            'project_str_setting_options': 'string2',
            'settings.example_project_app.project_int_setting_options': 1,
            'settings.example_project_app.project_bool_setting': True,
            'settings.example_project_app.'
            'project_json_setting': '{"Test": "Updated"}',
            'settings.example_project_app.'
            'project_callable_setting': 'No project or user for callable',
            'settings.example_project_app.'
            'project_callable_setting_options': str(self.project.sodar_uuid),
            'settings.projectroles.test_setting_local': True,
            'owner': self.user.sodar_uuid,
            'title': 'TestProject',
            'type': PROJECT_TYPE_PROJECT,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:detail',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )
        # Assert settings state after update
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_str_setting', project=self.project
            ),
            'updated',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_int_setting', project=self.project
            ),
            170,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_str_setting_options',
                project=self.project,
            ),
            'string2',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_int_setting_options',
                project=self.project,
            ),
            1,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_bool_setting', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME, 'project_json_setting', project=self.project
            ),
            {'Test': 'Updated'},
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_callable_setting',
                project=self.project,
            ),
            'No project or user for callable',
        )
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_callable_setting_options',
                project=self.project,
            ),
            str(self.project.sodar_uuid),
        )
        self.assertEqual(
            app_settings.get(
                'projectroles', 'test_setting_local', project=self.project
            ),
            True,
        )
        self.assertEqual(
            app_settings.get(
                'projectroles', 'test_setting', project=self.project
            ),
            False,
        )


class TestProjectRoleView(ProjectMixin, RoleAssignmentMixin, TestViewsBase):
    """Tests for ProjectRoleView"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        # Set superuser as owner
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Set new user as delegate
        self.user_delegate = self.make_user('user_delegate')
        self.delegate_as = self.make_assignment(
            self.project, self.user_delegate, self.role_delegate
        )
        # Set another new user as guest (= one of the member roles)
        self.user_guest = self.make_user('user_guest')
        self.guest_as = self.make_assignment(
            self.project, self.user_guest, self.role_guest
        )

    def test_get(self):
        """Test ProjectRoleView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'].pk, self.project.pk)

        expected = [
            {
                'id': self.owner_as.pk,
                'project': self.project.pk,
                'role': self.role_owner.pk,
                'user': self.user.pk,
                'sodar_uuid': self.owner_as.sodar_uuid,
            },
            {
                'id': self.delegate_as.pk,
                'project': self.project.pk,
                'role': self.role_delegate.pk,
                'user': self.user_delegate.pk,
                'sodar_uuid': self.delegate_as.sodar_uuid,
            },
            {
                'id': self.guest_as.pk,
                'project': self.project.pk,
                'role': self.role_guest.pk,
                'user': self.user_guest.pk,
                'sodar_uuid': self.guest_as.sodar_uuid,
            },
        ]
        self.assertEqual(
            [model_to_dict(m) for m in response.context['roles']], expected
        )
        self.assertNotIn('remote_role_url', response.context)

    def test_get_not_found(self):
        """Test GET view with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:roles',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


class TestRoleAssignmentCreateView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignmentCreateView and related helper views"""

    def setUp(self):
        super().setUp()
        # Set up category and project
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.user_owner_cat = self.make_user('owner_cat')
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.user_owner = self.make_user('user_owner')
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.user_new = self.make_user('user_new')
        # Set up helpers
        self.app_alert_model = get_backend_api('appalerts_backend').get_model()
        self.url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:role_create',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_get(self):
        """Test RoleAssignmentCreateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['project'].widget, HiddenInput)
        self.assertEqual(form.initial['project'], self.project.sodar_uuid)
        # Assert user with previously added role in project is not selectable
        self.assertNotIn(
            [
                (
                    self.user_owner.sodar_uuid,
                    get_user_display_name(self.user_owner, True),
                )
            ],
            form.fields['user'].choices,
        )
        # Assert owner role is not selectable
        self.assertNotIn(
            get_role_option(self.project, self.role_owner),
            form.fields['role'].choices,
        )
        # Assert delegate role is selectable
        self.assertIn(
            get_role_option(self.project, self.role_delegate),
            form.fields['role'].choices,
        )
        # Assert finder role is not selectable
        self.assertNotIn(
            get_role_option(self.project, self.role_finder),
            form.fields['role'].choices,
        )

    def test_get_category(self):
        """Test GET with category"""
        with self.login(self.user):
            response = self.client.get(self.url_cat)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsInstance(form.fields['project'].widget, HiddenInput)
        self.assertEqual(form.initial['project'], self.category.sodar_uuid)
        # Assert user with previously added role in project is not selectable
        self.assertNotIn(
            [
                (
                    self.user_owner_cat.sodar_uuid,
                    get_user_display_name(self.user_owner_cat, True),
                )
            ],
            form.fields['user'].choices,
        )
        self.assertNotIn(
            get_role_option(self.category, self.role_owner),
            form.fields['role'].choices,
        )
        self.assertIn(
            get_role_option(self.category, self.role_delegate),
            form.fields['role'].choices,
        )
        # Assert finder role is selectable
        self.assertIn(
            get_role_option(self.category, self.role_finder),
            form.fields['role'].choices,
        )

    def test_get_not_found(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test RoleAssignmentCreateView POST"""
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_create'
            ).count(),
            0,
        )

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_guest.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_guest.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_create'
            ).count(),
            1,
        )
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_post_delegate(self):
        """Test POST with project delegate role"""
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)

    def test_post_delegate_limit_reached(self):
        """Test POST with reached delegate limit"""
        del_user = self.make_user('new_del_user')
        self.make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertIsNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_new
            ).first()
        )

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_post_delegate_limit_increased(self):
        """Test POST with delegate limit > 1"""
        del_user = self.make_user('new_del_user')
        self.make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        self.assertIsNotNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_new
            ).first()
        )

    def test_post_delegate_limit_inherited(self):
        """Test POST with existing delegate role for inherited owner"""
        self.make_assignment(
            self.project, self.user_owner_cat, self.role_delegate
        )
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        # NOTE: Limit should be reached, but inherited owner role is disregarded
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        self.assertIsNotNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_new
            ).first()
        )

    def test_post_autocomplete_redirect_to_invite(self):
        """Test POST for redirecting to ProjectInviteCreateView"""
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'text': 'test@example.com',
        }
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_autocomplete_user_redirect'), values
            )
        self.assertEqual(response.status_code, 200)
        with self.login(self.user):
            data = json.loads(response.content)
            self.assertEqual(data['success'], True)
            self.assertEqual(
                data['redirect_url'],
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_get_autocomplete_display_options(self):
        """Test GET for displaying options by SODARUserRedirectWidget"""
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example.com',
        }
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_autocomplete_user_redirect'), values
            )
        self.assertEqual(response.status_code, 200)
        new_option = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example.com"',
            'create_id': True,
        }
        data = json.loads(response.content)
        self.assertIn(new_option, data['results'])

    def test_get_autocomplete_display_options_invalid_email(self):
        """Test GET for displaying options with invalid email"""
        values = {
            'project': self.project.sodar_uuid,
            'role': self.role_guest.pk,
            'q': 'test@example',
        }
        with self.login(self.user):
            response = self.client.get(
                reverse('projectroles:ajax_autocomplete_user_redirect'), values
            )
        self.assertEqual(response.status_code, 200)
        new_option = {
            'id': 'test@example.com',
            'text': 'Send an invite to "test@example"',
            'create_id': True,
        }
        data = json.loads(response.content)
        self.assertNotIn(new_option, data['results'])

    def test_get_promote(self):
        """Test GET with inherited role promotion"""
        # Assign category guest user for inherit/promote tests
        guest_as_cat = self.make_assignment(
            self.category, self.user_new, self.role_guest
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create_promote',
                    kwargs={
                        'project': self.project.sodar_uuid,
                        'promote_as': guest_as_cat.sodar_uuid,
                    },
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['promote_as'], guest_as_cat)
        form = response.context['form']
        self.assertIsInstance(form.fields['project'].widget, HiddenInput)
        self.assertIsInstance(form.fields['user'].widget, HiddenInput)
        self.assertEqual(form.initial['project'], self.project.sodar_uuid)
        self.assertEqual(form.initial['user'], self.user_new)
        self.assertEqual(
            [c[0] for c in form.fields['role'].choices],
            [self.role_delegate.pk, self.role_contributor.pk],
        )

    def test_get_promote_local_role(self):
        """Test GET for promotion with local role (should fail)"""
        guest_as = self.make_assignment(
            self.project, self.user_new, self.role_guest
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create_promote',
                    kwargs={
                        'project': self.project.sodar_uuid,
                        'promote_as': guest_as.sodar_uuid,
                    },
                )
            )
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_get_promote_child_role(self):
        """Test GET for promotion with child role (should fail)"""
        # Set up sub category and project with role
        sub_category = self.make_project(
            'SubCategory', PROJECT_TYPE_CATEGORY, self.category
        )
        sub_project = self.make_project(
            'SubProject', PROJECT_TYPE_PROJECT, sub_category
        )
        sub_as = self.make_assignment(
            sub_project, self.user_new, self.role_guest
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create_promote',
                    kwargs={
                        'project': self.project.sodar_uuid,
                        'promote_as': sub_as.sodar_uuid,
                    },
                )
            )
        self.assertEqual(response.status_code, 302)

    def test_get_promote_delegate(self):
        """Test GET for promotion with delegate role (should fail)"""
        delegate_as_cat = self.make_assignment(
            self.category, self.user_new, self.role_delegate
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create_promote',
                    kwargs={
                        'project': self.project.sodar_uuid,
                        'promote_as': delegate_as_cat.sodar_uuid,
                    },
                )
            )
        self.assertEqual(response.status_code, 302)

    def test_get_promote_owner(self):
        """Test GET for promotion with ownere role (should fail)"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_create_promote',
                    kwargs={
                        'project': self.project.sodar_uuid,
                        'promote_as': self.owner_as_cat.sodar_uuid,
                    },
                )
            )
        self.assertEqual(response.status_code, 302)

    def test_post_promote(self):
        """Test POST for promoting inherited role"""
        self.make_assignment(self.category, self.user_new, self.role_guest)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_create'
            ).count(),
            0,
        )

        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_new.sodar_uuid,
            'role': self.role_contributor.pk,
            'promote': True,
        }
        with self.login(self.user):
            self.client.post(self.url, values)

        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_new
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_new.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)


class TestRoleAssignmentUpdateView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignmentUpdateView"""

    def setUp(self):
        super().setUp()
        # Set up category and project
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.user_owner_cat = self.make_user('owner_cat')
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.user_owner = self.make_user('user_owner')
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Create guest user and role
        self.user_guest = self.make_user('user_guest')
        self.role_as = self.make_assignment(
            self.project, self.user_guest, self.role_guest
        )
        # Set up helpers
        self.app_alert_model = get_backend_api('appalerts_backend').get_model()
        self.url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.role_as.sodar_uuid},
        )

    def test_get(self):
        """Test RoleAssignmentUpdateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsInstance(form.fields['project'].widget, HiddenInput)
        self.assertEqual(form.initial['project'], self.project.sodar_uuid)
        self.assertIsInstance(form.fields['user'].widget, HiddenInput)
        self.assertEqual(form.initial['user'], self.user_guest.sodar_uuid)
        # Assert owner role is not selectable
        self.assertNotIn(
            get_role_option(self.project, self.role_owner),
            form.fields['role'].choices,
        )
        # Assert delegate role is selectable
        self.assertIn(
            get_role_option(self.project, self.role_delegate),
            form.fields['role'].choices,
        )
        # Assert finder role is not selectable
        self.assertNotIn(
            get_role_option(self.project, self.role_finder),
            form.fields['role'].choices,
        )

    def test_get_category(self):
        """Test GET for category"""
        user_new = self.make_user('user_new')
        new_as = self.make_assignment(self.category, user_new, self.role_guest)
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': new_as.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertIsInstance(form.fields['project'].widget, HiddenInput)
        self.assertEqual(form.initial['project'], self.category.sodar_uuid)
        self.assertIsInstance(form.fields['user'].widget, HiddenInput)
        self.assertEqual(form.initial['user'], user_new.sodar_uuid)
        self.assertNotIn(
            get_role_option(self.category, self.role_owner),
            form.fields['role'].choices,
        )
        self.assertIn(
            get_role_option(self.category, self.role_delegate),
            form.fields['role'].choices,
        )
        # Assert finder role is selectable
        self.assertIn(
            get_role_option(self.category, self.role_finder),
            form.fields['role'].choices,
        )

    def test_get_not_found(self):
        """Test GET with invalid assignment UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_update',
                    kwargs={'roleassignment': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test RoleAssignmentUpdateView POST"""
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_update'
            ).count(),
            0,
        )

        values = {
            'project': self.role_as.project.sodar_uuid,
            'user': self.user_guest.sodar_uuid,
            'role': self.role_contributor.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_guest
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_guest.pk,
            'role': self.role_contributor.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_update'
            ).count(),
            1,
        )
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    def test_post_delegate(self):
        """Test POST to update RoleAssignment to delegate"""
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        values = {
            'project': self.role_as.project.sodar_uuid,
            'user': self.user_guest.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=self.user_guest
        )
        expected = {
            'id': role_as.pk,
            'project': self.project.pk,
            'user': self.user_guest.pk,
            'role': self.role_delegate.pk,
            'sodar_uuid': role_as.sodar_uuid,
        }
        self.assertEqual(model_to_dict(role_as), expected)

    def test_post_delegate_limit_reached(self):
        """Test POST with reached delegate limit"""
        del_user = self.make_user('new_del_user')
        self.make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_guest.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_guest
            )
            .first()
            .role,
            self.role_guest,
        )

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_post_delegate_limit_increased(self):
        """Test POST with delegate limit > 1"""
        del_user = self.make_user('new_del_user')
        self.make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            1,
        )
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_guest.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            2,
        )

    def test_post_delegate_limit_inherited(self):
        """Test POST with existing delegate role for inherited owner"""
        self.make_assignment(
            self.project, self.user_owner_cat, self.role_delegate
        )
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            1,
        )
        values = {
            'project': self.project.sodar_uuid,
            'user': self.user_guest.sodar_uuid,
            'role': self.role_delegate.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        # NOTE: Limit should be reached, but inherited owner role is disregarded
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, role=self.role_delegate
            ).count(),
            2,
        )

    def test_get_inactive_local_role(self):
        """Test GET with inherited role overriding local inactive role"""
        # Set user as category contributor
        self.make_assignment(
            self.category, self.user_guest, self.role_contributor
        )
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        # Assert only delegate role is selectable
        self.assertEqual(len(form.fields['role'].choices), 1)
        self.assertEqual(
            form.fields['role'].choices[0],
            get_role_option(self.project, self.role_delegate),
        )


class TestRoleAssignmentDeleteView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignmentDeleteView"""

    def setUp(self):
        super().setUp()
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Create guest user and role
        self.user_contrib = self.make_user('user_contrib')
        self.contrib_as = self.make_assignment(
            self.project, self.user_contrib, self.role_contributor
        )
        self.user_new = self.make_user('user_new')
        # Set up helpers
        self.app_alerts = get_backend_api('appalerts_backend')
        self.app_alert_model = self.app_alerts.get_model()
        self.url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contrib_as.sodar_uuid},
        )

    def test_get(self):
        """Test RoleAssignmentDeleteView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['inherited_as'])
        self.assertEqual(response.context['inherited_children'], [])

    def test_get_inherit(self):
        """Test GET for user with inherited role"""
        inh_as = self.make_assignment(
            self.category, self.user_contrib, self.role_guest
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': self.contrib_as.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['inherited_as'], inh_as)
        self.assertIsNone(response.context['inherited_children'])

    def test_get_children(self):
        """Test GET for user with inherited child roles to be removed"""
        inh_as = self.make_assignment(
            self.category, self.user_new, self.role_guest
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': inh_as.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['inherited_as'])
        self.assertEqual(response.context['inherited_children'], [self.project])

    def test_get_children_finder(self):
        """Test GET for finder user with inherited child roles"""
        inh_as = self.make_assignment(
            self.category, self.user_new, self.role_finder
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': inh_as.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['inherited_as'])
        self.assertIsNone(response.context['inherited_children'])

    def test_get_not_found(self):
        """Test GET with invalid assignment UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test RoleAssignmentDeleteView POST"""
        alert = self.app_alerts.add_alert(
            'projectroles',
            'test_alert',
            self.user_contrib,
            'test',
            project=self.project,
        )
        self.assertEqual(alert.active, True)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_delete'
            ).count(),
            0,
        )
        self.assertEqual(len(mail.outbox), 0)
        with self.login(self.user):
            response = self.client.post(self.url)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:roles',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_delete'
            ).count(),
            1,
        )
        alert.refresh_from_db()
        self.assertEqual(alert.active, False)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_owner(self):
        """Test POST for RoleAssignment owner deletion (should fail)"""
        user_owner = self.make_user('user_owner')
        self.owner_as.user = user_owner  # Not a superuser
        self.owner_as.save()
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(len(mail.outbox), 0)
        with self.login(user_owner):
            response = self.client.post(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': self.owner_as.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_contributor(self):
        """Test POST as contributor (should fail)"""
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        with self.login(self.user_contrib):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)

    def test_post_inherit(self):
        """Test POST with existing inherited role"""
        self.make_assignment(self.category, self.user_contrib, self.role_guest)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        alert = self.app_alerts.add_alert(
            'projectroles',
            'test_alert',
            self.user_contrib,
            'test',
            project=self.project,
        )
        self.assertEqual(alert.active, True)
        with self.login(self.user):
            self.client.post(self.url)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_update'
            ).count(),
            1,
        )
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_delete'
            ).count(),
            0,
        )
        alert.refresh_from_db()
        self.assertEqual(alert.active, True)

    def test_post_children(self):
        """Test POST with child categories or projects"""
        new_as = self.make_assignment(
            self.category, self.user_new, self.role_guest
        )
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        alert = self.app_alerts.add_alert(
            'projectroles',
            'test_alert',
            self.user_new,
            'test',
            project=self.project,  # NOTE: Setting for child project
        )
        self.assertEqual(alert.active, True)
        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': new_as.sodar_uuid},
                )
            )
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_update'
            ).count(),
            0,
        )
        self.assertEqual(
            self.app_alert_model.objects.filter(
                alert_name='role_delete'
            ).count(),
            1,
        )
        alert.refresh_from_db()
        self.assertEqual(alert.active, False)

    def test_post_app_settings_contributor(self):
        """Test post with PROJECT_USER app settings after contributor deletion"""
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        app_settings.set(
            app_name=EXAMPLE_APP_NAME,
            setting_name='project_user_bool_setting',
            project=self.project,
            user=self.user,
            value=True,
        )
        self.assertIsNotNone(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_user_bool_setting',
                self.project,
                self.user_contrib,
            )
        )
        with self.login(self.user):
            self.client.post(self.url)
        self.assertEqual(RoleAssignment.objects.all().count(), 2)
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_user_bool_setting',
                self.project,
                self.user_contrib,
            ),
            False,
        )

    def test_post_app_settings_inherit(self):
        """Test POST with PROJECT_USER app setting with inherited role"""
        self.make_assignment(self.category, self.user_contrib, self.role_guest)
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        app_settings.set(
            app_name=EXAMPLE_APP_NAME,
            setting_name='project_user_bool_setting',
            project=self.project,
            user=self.user,
            value=True,
        )
        self.assertIsNotNone(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_user_bool_setting',
                self.project,
                self.user_contrib,
            )
        )
        with self.login(self.user):
            self.client.post(self.url)
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_user_bool_setting',
                self.project,
                self.user_contrib,
            ),
            False,
        )

    def test_post_app_settings_children(self):
        """Test POST with PROJECT_USER app setting with child categories or projects"""
        new_as = self.make_assignment(
            self.category, self.user_new, self.role_guest
        )
        self.assertEqual(RoleAssignment.objects.all().count(), 4)
        app_settings.set(
            app_name=EXAMPLE_APP_NAME,
            setting_name='project_user_bool_setting',
            project=self.project,
            user=self.user,
            value=True,
        )
        self.assertIsNotNone(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_user_bool_setting',
                self.project,
                self.user_new,
            )
        )
        with self.login(self.user):
            self.client.post(
                reverse(
                    'projectroles:role_delete',
                    kwargs={'roleassignment': new_as.sodar_uuid},
                )
            )
        self.assertEqual(RoleAssignment.objects.all().count(), 3)
        self.assertEqual(
            app_settings.get(
                EXAMPLE_APP_NAME,
                'project_user_bool_setting',
                self.project,
                self.user_new,
            ),
            False,
        )


class TestRoleAssignmentOwnerTransferView(
    ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for RoleAssignmentOwnerTransferView"""

    def setUp(self):
        super().setUp()
        # Set up category and project
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.user_owner = self.make_user('user_owner')
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Create guest user and role
        self.user_guest = self.make_user('user_guest')
        self.role_as = self.make_assignment(
            self.project, self.user_guest, self.role_guest
        )
        # User without roles
        self.user_new = self.make_user('user_new')
        # Set up helpers
        self.app_alert_model = get_backend_api('appalerts_backend').get_model()
        self.url = reverse(
            'projectroles:role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test RoleAssignmentOwnerTransferView GET"""
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form.fields.get('old_owner_role'))
        self.assertEqual(len(form.fields['old_owner_role'].choices), 3)
        # Assert finder role is not selectable
        self.assertNotIn(
            self.role_finder.pk,
            [c[0] for c in form.fields['old_owner_role'].choices],
        )

    def test_get_old_inherited_member(self):
        """Test GET with inherited non-owner role for old owner"""
        self.make_assignment(
            self.category, self.user_owner, self.role_contributor
        )
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        # Only delegate and contributor roles allowed
        self.assertEqual(
            [c[0] for c in form.fields['old_owner_role'].choices],
            [self.role_delegate.pk, self.role_contributor.pk],
        )
        self.assertEqual(form.fields['old_owner_role'].disabled, False)

    def test_get_old_inherited_owner(self):
        """Test GET with inherited owner role for old owner"""
        self.owner_as_cat.user = self.user_owner
        self.owner_as_cat.save()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        # Only owner role included
        self.assertEqual(len(form.fields['old_owner_role'].choices), 1)
        self.assertEqual(
            form.fields['old_owner_role'].choices[0][0], self.role_owner.pk
        )
        self.assertEqual(form.fields['old_owner_role'].disabled, True)

    def test_get_category(self):
        """Test GET for category"""
        self.make_assignment(self.category, self.user_new, self.role_guest)
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:role_owner_transfer',
                    kwargs={'project': self.category.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form.fields.get('old_owner_role'))
        self.assertEqual(len(form.fields['old_owner_role'].choices), 4)
        # Assert finder role is selectable
        self.assertIn(
            self.role_finder.pk,
            [c[0] for c in form.fields['old_owner_role'].choices],
        )

    def test_post(self):
        """Test RoleAssignmentOwnerTransferView POST"""
        self.assertEqual(self.app_alert_model.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        with self.login(self.user):
            response = self.client.post(
                self.url,
                data={
                    'project': self.project.sodar_uuid,
                    'new_owner': self.user_guest.sodar_uuid,
                    'old_owner_role': self.role_guest.pk,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_guest)
        self.assertEqual(
            RoleAssignment.objects.get(
                project=self.project, user=self.user_owner
            ).role,
            self.role_guest,
        )
        self.assertEqual(self.app_alert_model.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_post_as_old_owner(self):
        """Test POST as old owner"""
        with self.login(self.user_owner):
            response = self.client.post(
                self.url,
                data={
                    'project': self.project.sodar_uuid,
                    'new_owner': self.user_guest.sodar_uuid,
                    'old_owner_role': self.role_guest.pk,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_guest)
        self.assertEqual(
            RoleAssignment.objects.get(
                project=self.project, user=self.user_owner
            ).role,
            self.role_guest,
        )
        # Should only create one alert/mail for new owner
        self.assertEqual(self.app_alert_model.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_old_inherited_member(self):
        """Test POST to transfer from old owner with inherited non-owner role"""
        self.make_assignment(
            self.category, self.user_owner, self.role_contributor
        )
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        with self.login(self.user):
            response = self.client.post(
                self.url,
                data={
                    'project': self.project.sodar_uuid,
                    'new_owner': self.user_guest.sodar_uuid,
                    'old_owner_role': self.role_contributor.pk,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_guest)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        self.assertEqual(self.owner_as.role, self.role_contributor)
        self.assertEqual(self.app_alert_model.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_post_old_inherited_owner(self):
        """Test POST to transfer from old owner with inherited owner role"""
        self.owner_as_cat.user = self.user_owner
        self.owner_as_cat.save()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        with self.login(self.user):
            response = self.client.post(
                self.url,
                data={
                    'project': self.project.sodar_uuid,
                    'new_owner': self.user_guest.sodar_uuid,
                    'old_owner_role': self.role_owner.pk,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_guest)
        self.assertIsNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_owner
            ).first()
        )
        self.assertEqual(
            self.project.get_role(self.user_owner), self.owner_as_cat
        )
        self.assertEqual(self.owner_as.role, self.role_owner)
        # No alert or message for old owner as they are still owner
        self.assertEqual(self.app_alert_model.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_new_inherited_member(self):
        """Test POST to transfer to new owner with inherited non-owner role"""
        self.make_assignment(
            self.category, self.user_new, self.role_contributor
        )
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        with self.login(self.user):
            response = self.client.post(
                self.url,
                data={
                    'project': self.project.sodar_uuid,
                    'new_owner': self.user_new.sodar_uuid,
                    'old_owner_role': self.role_contributor.pk,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        self.assertEqual(self.owner_as.role, self.role_contributor)
        self.assertEqual(self.app_alert_model.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_post_new_inherited_owner(self):
        """Test POST to transfer to new owner with inherited owner role"""
        self.assertEqual(
            self.project.get_role(self.user_owner_cat), self.owner_as_cat
        )
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        with self.login(self.user):
            response = self.client.post(
                self.url,
                data={
                    'project': self.project.sodar_uuid,
                    'new_owner': self.user_owner_cat.sodar_uuid,
                    'old_owner_role': self.role_contributor.pk,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_owner_cat)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        self.assertEqual(self.owner_as.role, self.role_contributor)
        self.assertEqual(
            self.project.get_role(self.user_owner_cat),
            RoleAssignment.objects.get(
                project=self.project,
                user=self.user_owner_cat,
                role=self.role_owner,
            ),
        )
        self.assertEqual(self.app_alert_model.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_new_local_role(self):
        """Test POST to transfer to new owner with overridden local role"""
        new_as = self.make_assignment(
            self.project, self.user_new, self.role_contributor
        )
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        with self.login(self.user):
            response = self.client.post(
                self.url,
                data={
                    'project': self.project.sodar_uuid,
                    'new_owner': self.user_new.sodar_uuid,
                    'old_owner_role': self.role_contributor.pk,
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.assertEqual(self.project.get_owner(), new_as)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        self.assertEqual(self.owner_as.role, self.role_contributor)
        self.assertEqual(self.app_alert_model.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)


class TestProjectInviteCreateView(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestViewsBase
):
    """Tests for ProjectInviteCreateView"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.user_new = self.make_user('user_new')
        self.url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectInviteCreateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        # Assert owner role is not selectable
        self.assertNotIn(
            get_role_option(self.project, self.role_owner),
            form.fields['role'].choices,
        )

    def test_get_from_roleassignment(self):
        """Test GET with forwarded values from RoleAssignment Form"""
        values = {
            'e': 'test@example.com',
            'r': self.role_contributor.pk,
        }
        with self.login(self.user):
            response = self.client.get(self.url, values)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        # Assert owner role is not selectable
        self.assertNotIn(
            get_role_option(self.project, self.role_owner),
            form.fields['role'].choices,
        )
        # Assert forwarded mail address and role have been set in the form
        self.assertEqual(
            form.fields['role'].initial, str(self.role_contributor.pk)
        )
        self.assertEqual(form.fields['email'].initial, 'test@example.com')

    def test_get_not_found(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test ProjectInviteCreateView POST"""
        self.assertEqual(ProjectInvite.objects.all().count(), 0)
        values = {
            'email': INVITE_EMAIL,
            'project': self.project.pk,
            'role': self.role_contributor.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(ProjectInvite.objects.all().count(), 1)
        invite = ProjectInvite.objects.get(
            project=self.project, email=INVITE_EMAIL, active=True
        )
        self.assertIsNotNone(invite)
        expected = {
            'id': invite.pk,
            'project': self.project.pk,
            'email': INVITE_EMAIL,
            'role': self.role_contributor.pk,
            'issuer': self.user.pk,
            'message': '',
            'date_expire': invite.date_expire,
            'secret': invite.secret,
            'active': True,
            'sodar_uuid': invite.sodar_uuid,
        }
        self.assertEqual(model_to_dict(invite), expected)
        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:invites',
                    kwargs={'project': self.project.sodar_uuid},
                ),
            )

    @override_settings(
        PROJECTROLES_ALLOW_LOCAL_USERS=False,
        ENABLE_SAML=False,
    )
    def test_post_local_users_not_allowed(self):
        """Test POST for local user with local users not allowed"""
        values = {
            'email': INVITE_EMAIL,
            'project': self.project.pk,
            'role': self.role_contributor.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProjectInvite.objects.all().count(), 0)

    @override_settings(
        PROJECTROLES_ALLOW_LOCAL_USERS=True,
        ENABLE_SAML=False,
    )
    def test_post_local_users_allowed(self):
        """Test POST for local user with local users allowed"""
        values = {
            'email': INVITE_EMAIL,
            'project': self.project.pk,
            'role': self.role_contributor.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 302)
        invite = ProjectInvite.objects.get(
            project=self.project, email=INVITE_EMAIL, active=True
        )
        self.assertIsNotNone(invite)

    @override_settings(
        PROJECTROLES_ALLOW_LOCAL_USERS=False,
        ENABLE_SAML=False,
        ENABLE_LDAP=True,
        AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE',
    )
    def test_post_local_users_email_domain(self):
        """Test POST for local user with email domain in AUTH_LDAP_USERNAME_DOMAIN"""
        values = {
            'email': INVITE_EMAIL,
            'project': self.project.pk,
            'role': self.role_contributor.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 302)
        invite = ProjectInvite.objects.get(
            project=self.project, email=INVITE_EMAIL, active=True
        )
        self.assertIsNotNone(invite)

    @override_settings(
        PROJECTROLES_ALLOW_LOCAL_USERS=False,
        ENABLE_SAML=False,
        ENABLE_LDAP=True,
        LDAP_ALT_DOMAINS=['example.com'],
    )
    def test_post_local_users_email_domain_ldap(self):
        """Test POST for local user with email domain in LDAP_ALT_DOMAINS"""
        values = {
            'email': INVITE_EMAIL,
            'project': self.project.pk,
            'role': self.role_contributor.pk,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 302)
        invite = ProjectInvite.objects.get(
            project=self.project, email=INVITE_EMAIL, active=True
        )
        self.assertIsNotNone(invite)


class TestProjectInviteAcceptView(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestViewsBase
):
    """Tests for ProjectInviteAcceptView and related helper views"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.user_new = self.make_user('user_new')
        self.project_url = reverse(
            'projectroles:detail',
            kwargs={'project': self.project.sodar_uuid},
        )

    @override_settings(ENABLE_LDAP=True, AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
    def test_get_ldap(self):
        """Test ProjectInviteAcceptView GET with LDAP invite"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

        with self.login(self.user_new):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:invite_process_ldap',
                        kwargs={'secret': invite.secret},
                    ),
                    302,
                ),
                (self.project_url, 302),
            ],
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_PROJECT_WELCOME.format(
                project_type='project',
                project_title='TestProject',
                role='project contributor',
            ),
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            1,
        )

    @override_settings(
        AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE',
        ENABLE_LDAP=True,
        LDAP_ALT_DOMAINS=['alt.org'],
        PROJECTROLES_ALLOW_LOCAL_USERS=False,
    )
    def test_get_ldap_alt_domain(self):
        """Test GET with LDAP invite and email in LDAP_ALT_DOMAINS"""
        alt_email = 'user@alt.org'
        invite = self.make_invite(
            email=alt_email,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

        with self.login(self.user_new):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:invite_process_ldap',
                        kwargs={'secret': invite.secret},
                    ),
                    302,
                ),
                (self.project_url, 302),
            ],
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            1,
        )

    @override_settings(
        AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE',
        ENABLE_LDAP=True,
        LDAP_ALT_DOMAINS=[],
        PROJECTROLES_ALLOW_LOCAL_USERS=False,
    )
    def test_get_ldap_email_not_listed(self):
        """Test GET with LDAP invite and email not in LDAP_ALT_DOMAINS"""
        alt_email = 'user@alt.org'
        invite = self.make_invite(
            email=alt_email,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

        with self.login(self.user_new):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertListEqual(response.redirect_chain, [(reverse('home'), 302)])
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

    @override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE', ENABLE_LDAP=True)
    def test_get_ldap_expired(self):
        """Test GET with expired LDAP invite"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
            date_expire=timezone.now(),
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

        with self.login(self.user_new):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:invite_process_ldap',
                        kwargs={'secret': invite.secret},
                    ),
                    302,
                ),
                (reverse('home'), 302),
            ],
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_local(self):
        """Test GET with local invite and nonexistent user with no user logged in"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)

        response = self.client.get(
            reverse(
                'projectroles:invite_accept',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
        )

        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
        )
        email = response.context['form']['email'].value()
        username = response.context['form']['username'].value()
        self.assertEqual(email, invite.email)
        self.assertEqual(username, invite.email.split('@')[0])
        self.assertEqual(User.objects.count(), 2)

        # NOTE: We must face HTTP_REFERER here for it to be included
        response = self.client.post(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            data={
                'first_name': 'First',
                'last_name': 'Last',
                'username': username,
                'email': email,
                'password': 'asd',
                'password_confirm': 'asd',
            },
            follow=True,
            HTTP_REFERER=reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
        )
        self.assertListEqual(
            response.redirect_chain,
            [
                (self.project_url, 302),
                (reverse('login') + '?next=' + self.project_url, 302),
            ],
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[1].message, MSG_LOGIN
        )
        user = User.objects.get(username=username)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=user,
                role=self.role_contributor,
            ).count(),
            1,
        )
        with self.login(user, password='asd'):
            response = self.client.get(self.project_url)
        self.assertEqual(response.status_code, 200)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_expired_local(self):
        """Test GET with expired local invite"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
            date_expire=timezone.now(),
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

        response = self.client.get(
            reverse(
                'projectroles:invite_accept',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertListEqual(
            response.redirect_chain,
            [
                (
                    reverse(
                        'projectroles:invite_process_local',
                        kwargs={'secret': invite.secret},
                    ),
                    302,
                ),
                (reverse('home'), 302),
                (reverse('login') + '?next=/', 302),
            ],
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project,
                user=self.user_new,
                role=self.role_contributor,
            ).count(),
            0,
        )

    @override_settings(
        ENABLE_LDAP=True,
        PROJECTROLES_ALLOW_LOCAL_USERS=True,
        AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE',
        AUTH_LDAP_DOMAIN_PRINTABLE='EXAMPLE',
    )
    def test_get_process_ldap_wrong_type_local(self):
        """Test ProjectInviteProcessLDAPView GET with local invite"""
        invite = self.make_invite(
            email='test@different.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        response = self.client.get(
            reverse(
                'projectroles:invite_process_ldap',
                kwargs={'secret': invite.secret},
            ),
        )
        # LDAP expects user to be logged in
        self.assertRedirects(
            response,
            reverse('login')
            + '?next='
            + reverse(
                'projectroles:invite_process_ldap',
                kwargs={'secret': invite.secret},
            ),
        )

    @override_settings(
        ENABLE_LDAP=True,
        PROJECTROLES_ALLOW_LOCAL_USERS=True,
        AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE',
        AUTH_LDAP_DOMAIN_PRINTABLE='EXAMPLE',
    )
    def test_get_process_local_wrong_type_ldap(self):
        """Test ProjectInviteProcessLocalView GET with LDAP invite"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse('home')
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_LDAP_LOCAL_VIEW,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_get_local_user_disabled(self):
        """Test GET with local users disabled"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        response = self.client.get(
            reverse(
                'projectroles:invite_accept',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertListEqual(
            response.redirect_chain,
            [(reverse('home'), 302), (reverse('login') + '?next=/', 302)],
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=False)
    def test_get_process_local_disabled(self):
        """Test ProjectInviteProcessLocalView GET with local users disabled"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response, reverse('login') + '?next=' + reverse('home')
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_LOCAL_NOT_ALLOWED,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_process_local_no_user_different_user_logged(self):
        """Test ProjectInviteProcessLocalView GET with nonexistent user and different user logged in"""
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_process_local',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_LOGGED_IN_ACCEPT,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_process_local_user_exists_different_user_logged(self):
        """Test ProjectInviteProcessLocalView GET with existing user and different user logged in"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_process_local',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_USER_NOT_EQUAL,
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_process_local_user_exists_is_logged(self):
        """Test ProjectInviteProcessLocalView GET with with existing and logged in user"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        with self.login(invited_user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_process_local',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(response, self.project_url)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_PROJECT_WELCOME.format(
                project_type='project',
                project_title='TestProject',
                role='project contributor',
            ),
        )

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_process_local_user_exists_not_logged(self):
        """Test ProjectInviteProcessLocalView GET with existing user and no user logged in"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        response = self.client.get(
            reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'login',
            )
            + '?next='
            + reverse(
                'projectroles:invite_process_local',
                kwargs={'secret': invite.secret},
            ),
        )
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_INVITE_USER_EXISTS,
        )

    def test_get_role_exists(self):
        """Test GET for user with roles in project"""
        invited_user = self.make_user(INVITE_EMAIL.split('@')[0])
        invited_user.email = INVITE_EMAIL
        invited_user.save()
        invite = self.make_invite(
            email=INVITE_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.make_assignment(self.project, invited_user, self.role_guest)
        self.assertTrue(invite.active)
        self.assertIsNone(
            ProjectEvent.objects.filter(event_name='invite_accept').first()
        )

        with self.login(invited_user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_accept',
                    kwargs={'secret': invite.secret},
                ),
                follow=True,
            )
        self.assertRedirects(response, self.project_url)
        invite.refresh_from_db()
        self.assertFalse(invite.active)
        # No timeline event should be created
        self.assertIsNone(
            ProjectEvent.objects.filter(event_name='invite_accept').first()
        )


class TestProjectInviteListView(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestViewsBase
):
    """Tests for ProjectInviteListView"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )

    def test_get(self):
        """Test ProjectInviteListView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invites',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

    def test_get_not_found(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invites',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)


class TestProjectInviteRevokeView(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestViewsBase
):
    """Tests for ProjectInviteRevokeView"""

    def setUp(self):
        super().setUp()
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        self.invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message='',
        )
        self.url = reverse(
            'projectroles:invite_revoke',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectInviteRevokeView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_not_found(self):
        """Test GET with invalid invite UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:invite_revoke',
                    kwargs={'projectinvite': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post_invite(self):
        """Test ProjectInviteRevokeView POST"""
        self.assertEqual(ProjectInvite.objects.all().count(), 1)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        with self.login(self.user):
            self.client.post(self.url)
        self.assertEqual(ProjectInvite.objects.all().count(), 1)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)

    def test_post_delegate(self):
        """Test POST with delegate role"""
        self.invite.role = self.role_delegate
        self.invite.save()
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        with self.login(self.user):
            self.client.post(self.url)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 0)

    def test_post_delegate_no_perms(self):
        """Test POST with delegate role and insufficient perms (should fail)"""
        self.invite.role = self.role_delegate
        self.invite.save()
        user_delegate = self.make_user('user_delegate')
        self.make_assignment(self.project, user_delegate, self.role_delegate)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)
        with self.login(user_delegate):
            self.client.post(self.url)
        self.assertEqual(ProjectInvite.objects.filter(active=True).count(), 1)


# Remote view tests ------------------------------------------------------------


class TestRemoteSiteListView(RemoteSiteMixin, TestViewsBase):
    """Tests for RemoteSiteListView"""

    def setUp(self):
        super().setUp()
        # Create target site
        self.target_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.url = reverse('projectroles:remote_sites')

    def test_get_source(self):
        """Test RemoteSiteListView GET as source"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sites'].count(), 1)  # 1 target site

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_target(self):
        """Test GET as target"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sites'].count(), 0)

    # TODO: Remove this once #76 is done
    @override_settings(PROJECTROLES_DISABLE_CATEGORIES=True)
    def test_get_disable_categories(self):
        """Test GET with categories disabled"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertRedirects(response, reverse('home'))


class TestRemoteSiteCreateView(RemoteSiteMixin, TestViewsBase):
    """Tests for RemoteSiteCreateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:remote_site_create')

    def test_get_source(self):
        """Test RemoteSiteCreateView GET as source"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsNotNone(form.fields['secret'].initial)
        self.assertEqual(form.fields['secret'].widget.attrs['readonly'], True)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_target(self):
        """Test GET as target"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertIsNone(form.fields['secret'].initial)
        self.assertNotIn('readonly', form.fields['secret'].widget.attrs)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_target_existing(self):
        """Test GET as target with existing source (should fail)"""
        # Create source site
        self.source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    def test_post_source(self):
        """Test RemoteSiteCreateView POST as source site"""
        self.assertEqual(
            0,
            ProjectEvent.objects.filter(
                event_name='target_site_create'
            ).count(),
        )
        self.assertEqual(RemoteSite.objects.all().count(), 0)
        values = {
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(RemoteSite.objects.all().count(), 1)
        site = RemoteSite.objects.first()
        expected = {
            'id': site.pk,
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SITE_MODE_TARGET,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        model_dict = model_to_dict(site)
        self.assertEqual(model_dict, expected)

        tl_event = ProjectEvent.objects.filter(
            event_name='target_site_create'
        ).first()
        self.assertEqual(tl_event.event_name, 'target_site_create')
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_post_target(self):
        """Test POST as target"""
        self.assertEqual(
            0,
            ProjectEvent.objects.filter(event_name='source_site_set').count(),
        )
        self.assertEqual(RemoteSite.objects.all().count(), 0)
        values = {
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

        self.assertEqual(RemoteSite.objects.all().count(), 1)
        site = RemoteSite.objects.first()
        expected = {
            'id': site.pk,
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SITE_MODE_SOURCE,
            'description': REMOTE_SITE_DESC,
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        model_dict = model_to_dict(site)
        self.assertEqual(model_dict, expected)

        tl_event = ProjectEvent.objects.filter(
            event_name='source_site_set'
        ).first()
        self.assertEqual(tl_event.event_name, 'source_site_set')

    def test_post_source_existing_name(self):
        """Test POST with an existing name"""
        self.target_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.assertEqual(RemoteSite.objects.all().count(), 1)

        values = {
            'name': REMOTE_SITE_NAME,  # Old name
            'url': REMOTE_SITE_NEW_URL,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': build_secret(),
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RemoteSite.objects.all().count(), 1)


class TestRemoteSiteUpdateView(RemoteSiteMixin, TestViewsBase):
    """Tests for RemoteSiteUpdateView"""

    def setUp(self):
        super().setUp()
        # Set up target site
        self.target_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.url = reverse(
            'projectroles:remote_site_update',
            kwargs={'remotesite': self.target_site.sodar_uuid},
        )

    def test_get(self):
        """Test RemoteSiteUpdateView GET as source"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNotNone(form)
        self.assertEqual(form['name'].initial, REMOTE_SITE_NAME)
        self.assertEqual(form['url'].initial, REMOTE_SITE_URL)
        self.assertEqual(form['description'].initial, REMOTE_SITE_DESC)
        self.assertEqual(form['secret'].initial, REMOTE_SITE_SECRET)
        self.assertEqual(form.fields['secret'].widget.attrs['readonly'], True)
        self.assertEqual(form['user_display'].initial, REMOTE_SITE_USER_DISPLAY)

    def test_get_not_found(self):
        """Test GET with invalid site UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:remote_site_update',
                    kwargs={'remotesite': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test RemoteSiteUpdateView POST as source"""
        self.assertEqual(
            0,
            ProjectEvent.objects.filter(
                event_name='target_site_update'
            ).count(),
        )
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        values = {
            'name': REMOTE_SITE_NEW_NAME,
            'url': REMOTE_SITE_NEW_URL,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(RemoteSite.objects.all().count(), 1)
        site = RemoteSite.objects.first()
        expected = {
            'id': site.pk,
            'name': REMOTE_SITE_NEW_NAME,
            'url': REMOTE_SITE_NEW_URL,
            'mode': SITE_MODE_TARGET,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': site.sodar_uuid,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        model_dict = model_to_dict(site)
        self.assertEqual(model_dict, expected)

        tl_event = ProjectEvent.objects.filter(
            event_name='target_site_update'
        ).first()
        self.assertEqual(tl_event.event_name, 'target_site_update')
        with self.login(self.user):
            self.assertRedirects(response, reverse('projectroles:remote_sites'))

    def test_post_existing_name(self):
        """Test POST with existing name (should fail)"""
        new_target_site = self.make_site(
            name=REMOTE_SITE_NEW_NAME,
            url=REMOTE_SITE_NEW_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_NEW_DESC,
            secret=REMOTE_SITE_NEW_SECRET,
        )
        self.assertEqual(RemoteSite.objects.all().count(), 2)
        values = {
            'name': REMOTE_SITE_NAME,  # Old name
            'url': REMOTE_SITE_NEW_URL,
            'description': REMOTE_SITE_NEW_DESC,
            'secret': REMOTE_SITE_SECRET,
            'user_display': REMOTE_SITE_USER_DISPLAY,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse(
                    'projectroles:remote_site_update',
                    kwargs={'remotesite': new_target_site.sodar_uuid},
                ),
                values,
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RemoteSite.objects.all().count(), 2)


class TestRemoteSiteDeleteView(RemoteSiteMixin, TestViewsBase):
    """Tests for RemoteSiteDeleteView"""

    def setUp(self):
        super().setUp()
        # Set up target site
        self.target_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.url = reverse(
            'projectroles:remote_site_delete',
            kwargs={'remotesite': self.target_site.sodar_uuid},
        )

    def test_get(self):
        """Test RemoteSiteDeleteView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_render_not_found(self):
        """Test GET with invalid site UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'projectroles:remote_site_delete',
                    kwargs={'remotesite': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test RemoteSiteDeleteView POST"""
        self.assertEqual(
            0,
            ProjectEvent.objects.filter(
                event_name='target_site_delete'
            ).count(),
        )
        self.assertEqual(RemoteSite.objects.all().count(), 1)
        with self.login(self.user):
            response = self.client.post(self.url)
            self.assertRedirects(response, reverse('projectroles:remote_sites'))
        tl_event = ProjectEvent.objects.filter(
            event_name='target_site_delete'
        ).first()
        self.assertEqual(tl_event.event_name, 'target_site_delete')
        self.assertEqual(RemoteSite.objects.all().count(), 0)


class TestRemoteProjectBatchUpdateView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    TestViewsBase,
):
    """Tests for RemoteProjectBatchUpdateView"""

    def setUp(self):
        super().setUp()
        # Set up project
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Set up target site
        self.target_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.url = reverse(
            'projectroles:remote_projects_update',
            kwargs={'remotesite': self.target_site.sodar_uuid},
        )

    def test_post_confirm(self):
        """Test RemoteProjectBatchUpdateView POST in confirm mode"""
        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {access_field: SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']}
        with self.login(self.user):
            response = self.client.post(self.url, values)
        self.assertEqual(
            0,
            ProjectEvent.objects.filter(
                event_name='remote_access_update'
            ).count(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['site'], self.target_site)
        self.assertIsNotNone(response.context['modifying_access'])

    def test_post_confirm_no_change(self):
        """Test POST without changes (should redirect)"""
        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {access_field: SODAR_CONSTANTS['REMOTE_LEVEL_NONE']}
        with self.login(self.user):
            response = self.client.post(self.url, values)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

        self.assertEqual(
            0,
            ProjectEvent.objects.filter(
                event_name='remote_access_update'
            ).count(),
        )

    def test_post_create(self):
        """Test POST to create new RemoteProject"""
        self.assertEqual(
            0,
            ProjectEvent.objects.filter(
                event_name='remote_batch_update'
            ).count(),
        )
        self.assertEqual(RemoteProject.objects.all().count(), 0)
        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {
            access_field: SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
            'update-confirmed': 1,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

        self.assertEqual(RemoteProject.objects.all().count(), 1)
        rp = RemoteProject.objects.first()
        self.assertEqual(rp.project_uuid, self.project.sodar_uuid)
        self.assertEqual(rp.level, SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'])

        tl_event = ProjectEvent.objects.filter(
            event_name='remote_batch_update'
        ).first()
        self.assertEqual(tl_event.event_name, 'remote_batch_update')

    def test_post_update(self):
        """Test POST to update existing RemoteProject"""
        self.assertEqual(
            0,
            ProjectEvent.objects.filter(
                event_name='remote_batch_update'
            ).count(),
        )
        rp = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.target_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL'],
        )
        self.assertEqual(RemoteProject.objects.all().count(), 1)

        access_field = 'remote_access_{}'.format(self.project.sodar_uuid)
        values = {
            access_field: SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
            'update-confirmed': 1,
        }
        with self.login(self.user):
            response = self.client.post(self.url, values)
            self.assertRedirects(
                response,
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': self.target_site.sodar_uuid},
                ),
            )

        self.assertEqual(RemoteProject.objects.all().count(), 1)
        rp.refresh_from_db()
        self.assertEqual(rp.project_uuid, self.project.sodar_uuid)
        self.assertEqual(rp.level, SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'])

        tl_event = ProjectEvent.objects.filter(
            event_name='remote_batch_update'
        ).first()
        self.assertEqual(tl_event.event_name, 'remote_batch_update')


# SODAR User view tests --------------------------------------------------------


class TestUserUpdateView(TestCase):
    """Tests for UserUpdateView"""

    def setUp(self):
        self.user_local = self.make_user('local_user')
        self.user_ldap = self.make_user('ldap_user@EXAMPLE')
        self.url = reverse('projectroles:user_update')

    def test_get_local_user(self):
        """Test TestUserUpdateView GET with local user"""
        with self.login(self.user_local):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_ldap_user(self):
        """Test GET with LDAP user"""
        with self.login(self.user_ldap):
            response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_USER_PROFILE_LDAP,
        )

    def test_post_local_user(self):
        """Test POST with local user"""
        self.assertEqual(User.objects.count(), 2)
        user = User.objects.get(pk=self.user_local.pk)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        with self.login(self.user_local):
            response = self.client.post(
                self.url,
                {
                    'first_name': 'Local',
                    'last_name': 'User',
                    'username': self.user_local.username,
                    'email': self.user_local.email,
                    'password': 'fjf',
                    'password_confirm': 'fjf',
                },
                follow=True,
            )
        self.assertListEqual(
            response.redirect_chain,
            [
                (reverse('home'), 302),
                (
                    reverse('login') + '?next=' + reverse('home'),
                    302,
                ),
            ],
        )
        self.assertEqual(User.objects.count(), 2)
        user = User.objects.get(pk=self.user_local.pk)
        self.assertEqual(user.first_name, 'Local')
        self.assertEqual(user.last_name, 'User')
