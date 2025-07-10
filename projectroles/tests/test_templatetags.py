"""Tests for template tags in the projectroles app"""

import mistune
import uuid

from importlib import import_module

from django.conf import settings
from django.test import override_settings, RequestFactory
from django.urls import reverse, resolve

from test_plus.test import TestCase

import projectroles
from projectroles.app_settings import AppSettingAPI
from projectroles.models import AppSetting, SODAR_CONSTANTS
from projectroles.plugins import PluginAPI
from projectroles.templatetags import (
    projectroles_common_tags as c_tags,
    projectroles_role_tags as r_tags,
    projectroles_tags as tags,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
)


app_settings = AppSettingAPI()
plugin_api = PluginAPI()
site = import_module(settings.SITE_PACKAGE)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']

# Local constants
APP_NAME_EX = 'example_project_app'
APP_NAME_FF = 'filesfolders'
NON_EXISTING_UUID = uuid.uuid4()
STATIC_FILE_PATH = 'images/logo_navbar.png'
TEMPLATE_PATH = 'projectroles/home.html'


class TemplateTagTestBase(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, ProjectInviteMixin, TestCase
):
    """Base class for testing template tags"""

    def setUp(self):
        # Init roles
        self.init_roles()
        # Init users
        self.user = self.make_user('user_owner')
        self.superuser = self.make_user('user_superuser')
        self.superuser.is_superuser = True
        self.superuser.save()
        # Init category
        self.category = self.make_project(
            title='TestCategoryTop', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        # Init project under category
        self.project = self.make_project(
            title='TestProjectSub',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
        )
        # Init role assignments
        self.owner_as_cat = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Init app_settings
        app_settings.set(
            APP_NAME_FF, 'allow_public_links', True, project=self.project
        )
        app_settings.set(
            'projectroles', 'ip_restrict', True, project=self.project
        )
        self.setting_filesfolders = AppSetting.objects.get(
            project=self.project,
            app_plugin__name=APP_NAME_FF,
            name='allow_public_links',
        )
        # Init request factory
        self.req_factory = RequestFactory()


class TestProjectrolesCommonTags(TemplateTagTestBase):
    """Test for template tags in projectroles_common_tags"""

    def test_site_version(self):
        """Test site_version()"""
        self.assertEqual(c_tags.site_version(), site.__version__)

    def test_core_version(self):
        """Test core_version()"""
        self.assertEqual(c_tags.core_version(), projectroles.__version__)

    def test_check_backend(self):
        """Test check_backend()"""
        self.assertEqual(c_tags.check_backend('timeline_backend'), True)
        self.assertEqual(c_tags.check_backend('example_backend_app'), True)
        self.assertEqual(c_tags.check_backend('sodar_cache'), True)
        self.assertEqual(c_tags.check_backend('NON_EXISTING_PLUGIN'), False)

    def test_get_project_by_uuid(self):
        """Test get_project_by_uuid()"""
        self.assertEqual(
            c_tags.get_project_by_uuid(self.project.sodar_uuid), self.project
        )
        self.assertEqual(c_tags.get_project_by_uuid(NON_EXISTING_UUID), None)

    def test_get_user_by_uuid(self):
        """Test get_user_by_uuid()"""
        self.assertEqual(
            c_tags.get_user_by_uuid(self.user.sodar_uuid), self.user
        )
        self.assertEqual(c_tags.get_user_by_uuid(NON_EXISTING_UUID), None)

    def test_get_user_by_username(self):
        """Test get_user_by_username()"""
        self.assertEqual(
            c_tags.get_user_by_username(self.user.username), self.user
        )
        self.assertEqual(c_tags.get_user_by_username('NON_EXISTING_USER'), None)

    def test_get_django_setting(self):
        """Test get_django_setting()"""
        ret = c_tags.get_django_setting('PROJECTROLES_BROWSER_WARNING')
        self.assertEqual(ret, True)
        self.assertIsInstance(ret, bool)
        ret = c_tags.get_django_setting('PROJECTROLES_BROWSER_WARNING', js=True)
        self.assertEqual(ret, 1)
        self.assertIsInstance(ret, int)
        self.assertEqual(
            c_tags.get_django_setting('NON_EXISTING_SETTING'), None
        )
        self.assertEqual(
            c_tags.get_django_setting(
                'NON_EXISTING_SETTING', default='default'
            ),
            'default',
        )

    def test_get_app_setting(self):
        """Test get_app_setting()"""
        self.assertEqual(
            c_tags.get_app_setting(
                APP_NAME_EX, 'project_bool_setting', project=self.project
            ),
            False,
        )
        self.assertEqual(
            c_tags.get_app_setting(
                APP_NAME_EX, 'user_bool_setting', user=self.user
            ),
            False,
        )

    def test_static_file_exists(self):
        """Test static_file_exists()"""
        self.assertEqual(c_tags.static_file_exists(STATIC_FILE_PATH), True)
        self.assertEqual(
            c_tags.static_file_exists('NON_EXISTING_PATH/FILE.txt'), False
        )

    def test_template_exists(self):
        """Test template_exists()"""
        self.assertEqual(c_tags.template_exists(TEMPLATE_PATH), True)
        self.assertEqual(
            c_tags.template_exists('projectroles/NON_EXISTING_FILE.html'), False
        )

    def test_get_full_url(self):
        """Test get_full_url()"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )

        with self.login(self.user):
            request = self.req_factory.get(url)
            self.assertEqual(
                c_tags.get_full_url(request, url),
                f'http://testserver/project/{self.project.sodar_uuid}',
            )

    def test_get_display_name(self):
        """Test get_display_name()"""
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=False, count=1), 'project'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=True, count=1), 'Project'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=False, count=2), 'projects'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=True, count=2), 'Projects'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=False, plural=True),
            'projects',
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=True, plural=True),
            'Projects',
        )

    def test_get_project_title_html(self):
        """Test get_project_title_html()"""
        self.assertEqual(
            c_tags.get_project_title_html(self.project),
            'TestCategoryTop / TestProjectSub',
        )

    def test_get_project_link(self):
        """Test get_project_link()"""
        self.assertEqual(
            c_tags.get_project_link(self.project, full_title=False),
            f'<a href="/project/{self.project.sodar_uuid}" '
            f'title="{self.project.description}" data-toggle="tooltip" '
            f'data-placement="top">{self.project.title}</a>',
        )
        self.assertEqual(
            c_tags.get_project_link(self.project, full_title=True),
            f'<a href="/project/{self.project.sodar_uuid}" '
            f'title="{self.project.description}" data-toggle="tooltip" '
            f'data-placement="top">{self.project.full_title}</a>',
        )
        # TODO: Also test remote project link display (with icon)

    def test_get_user_superuser_icon(self):
        """Test get_user_superuser_icon()"""
        expected = (
            '<span title="Superuser" data-toggle="tooltip">'
            '<i class="iconify text-info ml-1" '
            'data-icon="mdi:shield-account"></i>'
            '</span>'
        )
        self.assertEqual(c_tags.get_user_superuser_icon(), expected)

    def test_get_user_superuser_icon_tooltip_false(self):
        """Test get_user_superuser_icon() with tooltip=False"""
        expected = (
            '<i class="iconify text-info ml-1" '
            'data-icon="mdi:shield-account"></i>'
        )
        self.assertEqual(c_tags.get_user_superuser_icon(False), expected)

    def test_get_user_inactive_icon(self):
        """Test get_user_inactive_icon()"""
        expected = (
            '<span title="Inactive" data-toggle="tooltip">'
            '<i class="iconify text-secondary ml-1" '
            'data-icon="mdi:account-off"></i>'
            '</span>'
        )
        self.assertEqual(c_tags.get_user_inactive_icon(), expected)

    def test_get_user_inactive_icon_tooltip_false(self):
        """Test get_user_inactive_icon() with tooltip=False"""
        expected = (
            '<i class="iconify text-secondary ml-1" '
            'data-icon="mdi:account-off"></i>'
        )
        self.assertEqual(c_tags.get_user_inactive_icon(False), expected)

    def test_get_user_html(self):
        """Test get_user_html()"""
        self.assertEqual(
            c_tags.get_user_html(self.user),
            f'<span class="sodar-user-html" data-toggle="tooltip" '
            f'data-placement="top" title="{self.user.get_full_name()}">'
            f'<a href="mailto:{self.user.email}">{self.user.username}</a>'
            f'</span>',
        )

    def test_get_user_html_superuser(self):
        """Test get_user_html() with superuser"""
        self.user.is_superuser = True
        self.assertEqual(
            c_tags.get_user_html(self.user),
            '<span class="sodar-user-html" data-toggle="tooltip" '
            'data-placement="top" title="{}"><a href="mailto:{}">'
            '{}</a><i class="iconify text-info ml-1" '
            'data-icon="mdi:shield-account"></i></span>'.format(
                self.user.get_full_name() + ' (superuser)',
                self.user.email,
                self.user.username,
            ),
        )

    def test_get_user_html_inactive(self):
        """Test get_user_html() with inactive user"""
        self.user.is_active = False
        self.assertEqual(
            c_tags.get_user_html(self.user),
            '<span class="sodar-user-html text-secondary" '
            'data-toggle="tooltip" data-placement="top" title="{}">{}'
            '<i class="iconify text-secondary ml-1" '
            'data-icon="mdi:account-off"></i></span>'.format(
                self.user.get_full_name() + ' (inactive)', self.user.username
            ),
        )

    def test_get_user_html_superuser_inactive(self):
        """Test get_user_html() with inactive superuser"""
        self.user.is_superuser = True
        self.user.is_active = False
        self.assertEqual(
            c_tags.get_user_html(self.user),
            '<span class="sodar-user-html text-secondary" '
            'data-toggle="tooltip" data-placement="top" title="{}">{}'
            '<i class="iconify text-info ml-1" '
            'data-icon="mdi:shield-account"></i>'
            '<i class="iconify text-secondary ml-1" '
            'data-icon="mdi:account-off"></i></span>'.format(
                self.user.get_full_name() + ' (inactive)', self.user.username
            ),
        )

    def test_get_user_html_no_email(self):
        """Test get_user_html() with no email on user"""
        self.user.email = ''
        self.assertEqual(
            c_tags.get_user_html(self.user),
            f'<span class="sodar-user-html" data-toggle="tooltip" '
            f'data-placement="top" title="{self.user.get_full_name()}">'
            f'{self.user.username}</span>',
        )

    def test_get_user_badge(self):
        """Test get_user_badge()"""
        expected = (
            f'<span class="badge badge-primary sodar-obj-badge '
            f'sodar-user-badge sodar-user-badge-active" '
            f'title="{self.user.get_full_name()}" '
            f'data-toggle="tooltip" '
            f'data-uuid="{self.user.sodar_uuid}">'
            f'<i class="iconify" data-icon="mdi:account"></i> '
            f'<a class="text-white" href="mailto:{self.user.email}">'
            f'{self.user.username}</a></span>'
        )
        self.assertEqual(c_tags.get_user_badge(self.user), expected)

    def test_get_user_badge_no_email(self):
        """Test get_user_badge() with no email"""
        self.user.email = None
        expected = (
            f'<span class="badge badge-primary sodar-obj-badge '
            f'sodar-user-badge sodar-user-badge-active" '
            f'title="{self.user.get_full_name()}" '
            f'data-toggle="tooltip" '
            f'data-uuid="{self.user.sodar_uuid}">'
            f'<i class="iconify" data-icon="mdi:account"></i> '
            f'{self.user.username}</span>'
        )
        self.assertEqual(c_tags.get_user_badge(self.user), expected)

    def test_get_user_badge_superuser(self):
        """Test get_user_badge() with superuser"""
        expected = (
            f'<span class="badge badge-info sodar-obj-badge '
            f'sodar-user-badge sodar-user-badge-superuser" '
            f'title="{self.superuser.get_full_name()}" '
            f'data-toggle="tooltip" '
            f'data-uuid="{self.superuser.sodar_uuid}">'
            f'<i class="iconify" data-icon="mdi:shield-account"></i> '
            f'<a class="text-white" href="mailto:{self.superuser.email}">'
            f'{self.superuser.username}</a></span>'
        )
        self.assertEqual(c_tags.get_user_badge(self.superuser), expected)

    def test_get_user_badge_inactive(self):
        """Test get_user_badge() with inactive user"""
        self.user.is_active = False
        expected = (
            f'<span class="badge badge-secondary sodar-obj-badge '
            f'sodar-user-badge sodar-user-badge-inactive" '
            f'title="{self.user.get_full_name()}" '
            f'data-toggle="tooltip" '
            f'data-uuid="{self.user.sodar_uuid}">'
            f'<i class="iconify" data-icon="mdi:account-off"></i> '
            f'{self.user.username}</span>'
        )
        self.assertEqual(c_tags.get_user_badge(self.user), expected)

    def test_get_user_badge_extra_class(self):
        """Test get_user_badge() with extra_class"""
        expected = (
            f'<span class="badge badge-primary sodar-obj-badge '
            f'sodar-user-badge sodar-user-badge-active mr-1" '
            f'title="{self.user.get_full_name()}" '
            f'data-toggle="tooltip" '
            f'data-uuid="{self.user.sodar_uuid}">'
            f'<i class="iconify" data-icon="mdi:account"></i> '
            f'<a class="text-white" href="mailto:{self.user.email}">'
            f'{self.user.username}</a></span>'
        )
        self.assertEqual(
            c_tags.get_user_badge(self.user, extra_class='mr-1'), expected
        )

    def test_get_project_badge(self):
        """Test get_project_badge()"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected = (
            f'<span class="badge badge-info sodar-obj-badge '
            f'sodar-project-badge" title="{self.project.full_title}" '
            f'data-toggle="tooltip">'
            f'<i class="iconify" data-icon="mdi:cube"></i> '
            f'<a href="{url}">{self.project.title}</a>'
            f'</span>'
        )
        self.assertEqual(c_tags.get_project_badge(self.project), expected)

    def test_get_project_badge_category(self):
        """Test get_project_badge() with category"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )
        expected = (
            f'<span class="badge badge-info sodar-obj-badge '
            f'sodar-project-badge" title="{self.category.full_title}" '
            f'data-toggle="tooltip">'
            f'<i class="iconify" data-icon="mdi:rhombus-split"></i> '
            f'<a href="{url}">{self.category.title}</a>'
            f'</span>'
        )
        self.assertEqual(c_tags.get_project_badge(self.category), expected)

    def test_get_project_badge_can_view_false(self):
        """Test get_project_badge() with can_view=False"""
        expected = (
            f'<span class="badge badge-secondary sodar-obj-badge '
            f'sodar-project-badge" title="{self.project.full_title}" '
            f'data-toggle="tooltip">'
            f'<i class="iconify" data-icon="mdi:cube"></i> {self.project.title}'
            f'</span>'
        )
        self.assertEqual(
            c_tags.get_project_badge(self.project, can_view=False), expected
        )

    def test_get_project_badge_variant(self):
        """Test get_project_badge() with specified variant"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected = (
            f'<span class="badge badge-danger sodar-obj-badge '
            f'sodar-project-badge" title="{self.project.full_title}" '
            f'data-toggle="tooltip">'
            f'<i class="iconify" data-icon="mdi:cube"></i> '
            f'<a href="{url}">{self.project.title}</a>'
            f'</span>'
        )
        self.assertEqual(
            c_tags.get_project_badge(self.project, variant='danger'), expected
        )

    def test_get_project_badge_variant_uppercase(self):
        """Test get_project_badge() with variant in uppercase"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected = (
            f'<span class="badge badge-danger sodar-obj-badge '
            f'sodar-project-badge" title="{self.project.full_title}" '
            f'data-toggle="tooltip">'
            f'<i class="iconify" data-icon="mdi:cube"></i> '
            f'<a href="{url}">{self.project.title}</a>'
            f'</span>'
        )
        self.assertEqual(
            c_tags.get_project_badge(self.project, variant='DANGER'), expected
        )

    def test_get_project_badge_extra_class(self):
        """Test get_project_badge() with extra_class set"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected = (
            f'<span class="badge badge-info sodar-obj-badge '
            f'sodar-project-badge mr-1" title="{self.project.full_title}" '
            f'data-toggle="tooltip">'
            f'<i class="iconify" data-icon="mdi:cube"></i> '
            f'<a href="{url}">{self.project.title}</a>'
            f'</span>'
        )
        self.assertEqual(
            c_tags.get_project_badge(self.project, extra_class='mr-1'), expected
        )

    def test_get_history_dropdown(self):
        """Test get_history_dropdown()"""
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.user.__class__.__name__,
                'object_uuid': self.user.sodar_uuid,
            },
        )
        self.assertEqual(
            c_tags.get_history_dropdown(self.user, self.project),
            '<a class="dropdown-item sodar-pr-role-link-history" href="{}">\n'
            '<i class="iconify" data-icon="mdi:clock-time-eight-outline"></i> '
            'History</a>\n'.format(url),
        )

    def test_highlight_search_term(self):
        """Test highlight_search_term()"""
        item = 'Some Highlighted Text'
        term = 'highlight'
        self.assertEqual(
            c_tags.highlight_search_term(item, term),
            'Some <span class="sodar-search-highlight">Highlight</span>ed Text',
        )
        self.assertEqual(c_tags.highlight_search_term(item, ''), item)

    def test_get_info_link(self):
        """Test get_info_link()"""
        self.assertEqual(
            c_tags.get_info_link('content'),
            '<a class="sodar-info-link" tabindex="0" data-toggle="popover" '
            'data-trigger="focus" data-placement="top" data-content="content" >'
            '<i class="iconify text-info" data-icon="mdi:information"></i></a>',
        )
        self.assertEqual(
            c_tags.get_info_link('content', html=True),
            '<a class="sodar-info-link" tabindex="0" data-toggle="popover" '
            'data-trigger="focus" data-placement="top" data-content="content" '
            'data-html="true">'
            '<i class="iconify text-info" data-icon="mdi:information"></i></a>',
        )

    # TODO: Test get_remote_icon() (need to set up remote projects)

    def test_render_markdown(self):
        """Test render_markdown()"""
        raw_md = '**Some markdown**'
        self.assertEqual(
            c_tags.render_markdown(raw_md), mistune.markdown(raw_md)
        )

    def test_force_wrap(self):
        """Test force_wrap()"""
        s = 'sometext'
        s_space = 'some text'
        s_hyphen = 'some-text'
        self.assertEqual(c_tags.force_wrap(s, 4), 'some<wbr />text')
        self.assertEqual(c_tags.force_wrap(s_space, 4), s_space)
        self.assertEqual(c_tags.force_wrap(s_hyphen, 4), s_hyphen)

    def test_get_class(self):
        """Test get_class()"""
        self.assertEqual(c_tags.get_class(self.project), 'Project')
        self.assertEqual(c_tags.get_class(self.project, lower=True), 'project')

    def test_include_invalid_plugin(self):
        """Test get_backend_include() plugin checks"""
        self.assertEqual(
            c_tags.get_backend_include('NON_EXISTING_PLUGIN', 'js'), ''
        )
        # Testing a plugin which is not backend
        self.assertEqual(c_tags.get_backend_include(APP_NAME_FF, 'js'), '')

    def test_include_none_value(self):
        """Test get_backend_include() none attribute check"""
        # TODO: Replace with get_app_plugin once implemented for backend plugins
        backend_plugin = plugin_api.get_active_plugins('backend')[0]
        type(backend_plugin).javascript_url = None
        type(backend_plugin).css_url = None

        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'js'), ''
        )
        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'css'), ''
        )

    def test_include_invalid_url(self):
        """Test get_backend_include() file existence check"""
        # TODO: Replace with get_app_plugin once implemented for backend plugins
        backend_plugin = plugin_api.get_active_plugins('backend')[0]

        type(backend_plugin).javascript_url = (
            'example_backend_app/js/NOT_EXISTING_JS.js'
        )
        type(backend_plugin).css_url = (
            'example_backend_app/css/NOT_EXISTING_CSS.css'
        )

        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'js'), ''
        )
        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'css'), ''
        )

    def test_get_backend_include(self):
        """Test get_backend_include()"""
        # TODO: Replace with get_app_plugin once implemented for backend plugins
        backend_plugin = plugin_api.get_active_plugins('backend')[0]

        type(backend_plugin).javascript_url = (
            'example_backend_app/js/greeting.js'
        )
        type(backend_plugin).css_url = 'example_backend_app/css/greeting.css'

        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'js'),
            '<script type="text/javascript" '
            'src="/static/example_backend_app/js/greeting.js"></script>',
        )
        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'css'),
            '<link rel="stylesheet" type="text/css" '
            'href="/static/example_backend_app/css/greeting.css"/>',
        )

    def test_split(self):
        """Test split()"""
        s = 'xyz'
        self.assertEqual(c_tags.split(s, 'y'), ['x', 'z'])


class TestProjectrolesRoleTags(TemplateTagTestBase):
    """Test for template tags in projectroles_role_tags"""

    def test_get_role_icon(self):
        """Test get_role_icon()"""
        self.assertEqual(r_tags.get_role_icon(self.role_owner), 'mdi:star')
        self.assertEqual(
            r_tags.get_role_icon(self.role_delegate), 'mdi:star-half-full'
        )
        self.assertEqual(
            r_tags.get_role_icon(self.role_contributor), 'mdi:account'
        )
        self.assertEqual(r_tags.get_role_icon(self.role_guest), 'mdi:account')

    def test_get_role_class(self):
        """Test get_role_class()"""
        self.assertEqual(r_tags.get_role_class(self.user), '')

    def test_get_role_class_inactive(self):
        """Test get_role_class() with inactive user"""
        self.user.is_active = False
        self.assertEqual(r_tags.get_role_class(self.user), 'text-secondary')

    def test_get_role_perms(self):
        """Test get_role_perms()"""
        self.assertEqual(
            r_tags.get_role_perms(self.project, self.user),
            {
                'can_update_owner': True,
                'can_update_delegate': True,
                'can_update_members': True,
                'can_invite': True,
            },
        )
        # Guest
        user_guest = self.make_user('user_new')
        self.make_assignment(self.project, user_guest, self.role_guest)
        self.assertEqual(
            r_tags.get_role_perms(self.project, user_guest),
            {
                'can_update_owner': False,
                'can_update_delegate': False,
                'can_update_members': False,
                'can_invite': False,
            },
        )
        # Inherited delegate
        user_delegate_cat = self.make_user('user_delegate_cat')
        self.make_assignment(
            self.category, user_delegate_cat, self.role_delegate
        )
        self.assertEqual(
            r_tags.get_role_perms(self.project, user_delegate_cat),
            {
                'can_update_owner': False,
                'can_update_delegate': False,
                'can_update_members': True,
                'can_invite': True,
            },
        )

    def test_display_role_buttons(self):
        """Test display_role_buttons()"""
        self.assertTrue(
            r_tags.display_role_buttons(
                self.project,
                self.owner_as,
                r_tags.get_role_perms(self.project, self.user),
            ),
        )
        # Guest
        user_guest = self.make_user('user_new')
        guest_as = self.make_assignment(
            self.project, user_guest, self.role_guest
        )
        self.assertFalse(
            r_tags.display_role_buttons(
                self.project,
                guest_as,
                r_tags.get_role_perms(self.project, guest_as.user),
            ),
        )

    def test_get_inactive_role(self):
        """Test get_inactive_role()"""
        inh_user = self.make_user('inh_user')
        self.owner_as_cat.user = inh_user
        self.owner_as_cat.save()
        self.assertEqual(
            r_tags.get_inactive_role(self.project, self.owner_as_cat), None
        )
        inactive_as = self.make_assignment(
            self.project, inh_user, self.role_contributor
        )
        self.assertEqual(
            r_tags.get_inactive_role(self.project, self.owner_as_cat),
            inactive_as,
        )


class TestProjectrolesTags(TemplateTagTestBase):
    """Test for template tags in projectroles_tags"""

    def test_sodar_constant(self):
        """Test sodar_constant()"""
        self.assertEqual(tags.sodar_constant('PROJECT_TYPE_PROJECT'), 'PROJECT')
        self.assertEqual(tags.sodar_constant('NON_EXISTING_CONSTANT'), None)

    def test_get_backend_plugins(self):
        """Test get_backend_plugins()"""
        self.assertEqual(
            len(tags.get_backend_plugins()),
            len(settings.ENABLED_BACKEND_PLUGINS),
        )

    # TODO: Test get_site_app_messages() (set up admin alert)

    def test_allow_project_creation(self):
        """Test allow_project_creation()"""
        self.assertEqual(tags.allow_project_creation(), True)

    @override_settings(
        PROJECTROLES_SITE_MODE='TARGET', PROJECTROLES_TARGET_CREATE=False
    )
    def test_allow_project_creation_target(self):
        """Test allow_project_creation() in target mode"""
        self.assertEqual(tags.allow_project_creation(), False)

    def test_is_app_visible(self):
        """Test is_app_visible()"""
        app_plugin = plugin_api.get_app_plugin(APP_NAME_FF)
        self.assertEqual(
            tags.is_app_visible(app_plugin, self.project, self.user), True
        )

    def test_is_app_visible_category(self):
        """Test is_app_visible() with a category"""
        app_plugin = plugin_api.get_app_plugin(APP_NAME_FF)
        self.assertEqual(
            tags.is_app_visible(app_plugin, self.category, self.user),
            False,
        )

    def test_is_app_visible_category_enabled(self):
        """Test is_app_visible() with category_enable=True"""
        app_plugin = plugin_api.get_app_plugin('timeline')
        self.assertEqual(
            tags.is_app_visible(app_plugin, self.category, self.user), True
        )

    @override_settings(PROJECTROLES_HIDE_PROJECT_APPS=[APP_NAME_FF])
    def test_is_app_visible_hide(self):
        """Test is_app_visible() with a hidden app and normal/superuser"""
        app_plugin = plugin_api.get_app_plugin(APP_NAME_FF)
        superuser = self.make_user('superuser')
        superuser.is_superuser = True
        superuser.save()
        self.assertEqual(
            tags.is_app_visible(app_plugin, self.project, self.user), False
        )
        self.assertEqual(
            tags.is_app_visible(app_plugin, self.project, superuser), False
        )

    def test_get_app_link_state(self):
        """Test get_app_link_state()"""
        app_plugin = plugin_api.get_app_plugin(APP_NAME_FF)
        # TODO: Why does this also require app_name?
        self.assertEqual(
            tags.get_app_link_state(app_plugin, APP_NAME_FF, 'list'),
            'active',
        )
        self.assertEqual(
            tags.get_app_link_state(
                app_plugin, APP_NAME_FF, 'NON_EXISTING_URL_NAME'
            ),
            '',
        )

    # TODO: Test get_pr_link_state()

    def test_get_help_highlight(self):
        """Test get_help_highlight()"""
        self.assertEqual(
            tags.get_help_highlight(self.user), 'font-weight-bold text-warning'
        )

    # TODO: Test get_role_import_action() (Set up remote projects)
    # TODO: Test get_target_project_select() (Set up remote projects)

    def test_get_remote_access_legend(self):
        """Test get_remote_access_legend()"""
        self.assertEqual(tags.get_remote_access_legend('NONE'), 'No access')
        self.assertEqual(
            tags.get_remote_access_legend('NON_EXISTING_LEVEL'), 'N/A'
        )

    def test_get_sidebar_app_legend(self):
        """Test get_sidebar_app_legend()"""
        self.assertEqual(
            tags.get_sidebar_app_legend('Update Project'), 'Update<br />Project'
        )

    def test_get_sidebar_links_home(self):
        """Test get_sidebar_links() on the home view"""
        url = reverse('home')
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.user
        self.assertEqual(
            tags.get_project_app_links(request),
            [],
        )

    def test_get_sidebar_links_project_detail_view(self):
        """Test get_sidebar_links() on project detail view"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.user
        self.assertEqual(
            tags.get_project_app_links(request, self.project),
            [
                {
                    'name': 'project-detail',
                    'url': f'/project/{self.project.sodar_uuid}',
                    'label': 'Project Overview',
                    'icon': 'mdi:cube',
                    'active': True,
                },
                {
                    'name': 'app-plugin-filesfolders',
                    'url': f'/files/{self.project.sodar_uuid}',
                    'label': 'Files',
                    'icon': 'mdi:file',
                    'active': False,
                },
                {
                    'name': 'app-plugin-timeline',
                    'url': f'/timeline/{self.project.sodar_uuid}',
                    'label': 'Timeline',
                    'icon': 'mdi:clock-time-eight',
                    'active': False,
                },
                {
                    'name': 'app-plugin-bgjobs',
                    'url': f'/bgjobs/list/{self.project.sodar_uuid}',
                    'label': 'Background Jobs',
                    'icon': 'mdi:server',
                    'active': False,
                },
                {
                    'name': 'app-plugin-example_project_app',
                    'url': f'/examples/project/{self.project.sodar_uuid}',
                    'label': 'Example Project App',
                    'icon': 'mdi:rocket-launch',
                    'active': False,
                },
                {
                    'name': 'project-roles',
                    'url': f'/project/members/{self.project.sodar_uuid}',
                    'label': 'Members',
                    'icon': 'mdi:account-multiple',
                    'active': False,
                },
                {
                    'name': 'project-update',
                    'url': f'/project/update/{self.project.sodar_uuid}',
                    'label': 'Update Project',
                    'icon': 'mdi:lead-pencil',
                    'active': False,
                },
            ],
        )

    def test_get_sidebar_links_role_view(self):
        """Test get_sidebar_links() on the role view"""
        url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.user
        for app in tags.get_project_app_links(request, self.project):
            if app['name'] == 'project-roles':
                self.assertEqual(app['active'], True)
            else:
                self.assertEqual(app['active'], False)

    def test_get_sidebar_links_timeline_view(self):
        """Test get_sidebar_links() on the timeline view"""
        url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.user
        for app in tags.get_project_app_links(request, self.project):
            if app['name'] == 'app-plugin-timeline':
                self.assertEqual(app['active'], True)
            else:
                self.assertEqual(app['active'], False)

    def test_get_user_links_home(self):
        """Test get_user_links() on the home view"""
        url = reverse('home')
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.user
        self.assertEqual(
            tags.get_user_links(request),
            [
                {
                    'name': 'appalerts',
                    'url': '/alerts/app/list',
                    'label': 'App Alerts',
                    'icon': 'mdi:alert-octagram',
                    'active': False,
                },
                {
                    'name': 'example_site_app',
                    'url': '/examples/site/example',
                    'label': 'Example Site App',
                    'icon': 'mdi:rocket-launch-outline',
                    'active': False,
                },
                {
                    'name': 'timeline_site',
                    'url': '/timeline/site',
                    'label': 'Site-Wide Events',
                    'icon': 'mdi:clock-time-eight-outline',
                    'active': False,
                },
                {
                    'name': 'tokens',
                    'url': '/tokens/',
                    'label': 'API Tokens',
                    'icon': 'mdi:key-chain-variant',
                    'active': False,
                },
                {
                    'name': 'userprofile',
                    'url': '/user/profile',
                    'label': 'User Profile',
                    'icon': 'mdi:account-details',
                    'active': False,
                },
                {
                    'name': 'sign-out',
                    'url': '/logout/',
                    'label': 'Logout',
                    'icon': 'mdi:logout-variant',
                    'active': False,
                },
            ],
        )

    def test_get_user_links_home_superuser(self):
        """Test get_user_links() on the home view as superuser"""
        url = reverse('home')
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.superuser
        self.assertEqual(
            tags.get_user_links(request),
            [
                {
                    'name': 'adminalerts',
                    'url': '/alerts/adm/list',
                    'label': 'Admin Alerts',
                    'icon': 'mdi:alert',
                    'active': False,
                },
                {
                    'name': 'appalerts',
                    'url': '/alerts/app/list',
                    'label': 'App Alerts',
                    'icon': 'mdi:alert-octagram',
                    'active': False,
                },
                {
                    'name': 'bgjobs_site',
                    'url': '/bgjobs/list',
                    'label': 'Site Background Jobs',
                    'icon': 'mdi:server',
                    'active': False,
                },
                {
                    'name': 'example_site_app',
                    'url': '/examples/site/example',
                    'label': 'Example Site App',
                    'icon': 'mdi:rocket-launch-outline',
                    'active': False,
                },
                {
                    'name': 'remotesites',
                    'url': '/project/remote/sites',
                    'label': 'Remote Site Access',
                    'icon': 'mdi:cloud-sync',
                    'active': False,
                },
                {
                    'name': 'siteappsettings',
                    'url': '/project/site-app-settings',
                    'label': 'Site App Settings',
                    'icon': 'mdi:cog-outline',
                    'active': False,
                },
                {
                    'name': 'siteinfo',
                    'url': '/siteinfo/info',
                    'label': 'Site Info',
                    'icon': 'mdi:bar-chart',
                    'active': False,
                },
                {
                    'name': 'timeline_site',
                    'url': '/timeline/site',
                    'label': 'Site-Wide Events',
                    'icon': 'mdi:clock-time-eight-outline',
                    'active': False,
                },
                {
                    'name': 'timeline_site_admin',
                    'url': '/timeline/site/all',
                    'label': 'All Timeline Events',
                    'icon': 'mdi:web-clock',
                    'active': False,
                },
                {
                    'name': 'tokens',
                    'url': '/tokens/',
                    'label': 'API Tokens',
                    'icon': 'mdi:key-chain-variant',
                    'active': False,
                },
                {
                    'name': 'userprofile',
                    'url': '/user/profile',
                    'label': 'User Profile',
                    'icon': 'mdi:account-details',
                    'active': False,
                },
                {
                    'name': 'admin',
                    'url': None,  # No URL for Django admin, opens warning modal
                    'label': 'Django Admin',
                    'icon': 'mdi:cogs',
                    'active': False,
                },
                {
                    'name': 'sign-out',
                    'url': '/logout/',
                    'label': 'Logout',
                    'icon': 'mdi:logout-variant',
                    'active': False,
                },
            ],
        )

    def test_get_user_links_userprofile(self):
        """Test get_user_links() on the user profile view"""
        url = reverse('userprofile:detail')
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.user
        for app in tags.get_user_links(request):
            if app['name'] == 'userprofile':
                self.assertEqual(app['active'], True)
            else:
                self.assertEqual(app['active'], False)

    def test_get_user_links_remote_site(self):
        """Test get_user_links() on the remote site view"""
        url = reverse('projectroles:remote_site_create')
        request = self.req_factory.get(url)
        request.resolver_match = resolve(url)
        request.user = self.user
        for app in tags.get_user_links(request):
            if app['name'] == 'remote_site_app':
                self.assertEqual(app['active'], True)
            else:
                self.assertEqual(app['active'], False)
