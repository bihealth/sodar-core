"""Tests for Ajax view permissions in the timeline app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import ProjectPermissionTestBase

from timeline.tests.test_models import (
    TimelineEventMixin,
    TimelineEventStatusMixin,
)


# Local constants
APP_NAME_PR = 'projectroles'


class TestProjectEventDetailAjaxView(
    TimelineEventMixin, TimelineEventStatusMixin, ProjectPermissionTestBase
):
    """Tests for ProjectEventDetailAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, APP_NAME_PR, self.user_owner, 'project_create'
        )
        self.make_event_status(self.event, 'OK')
        self.url = reverse(
            'timeline:ajax_detail_project',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        self.bad_users = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test ProjectEventDetailAjaxView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 403)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)

    def test_get_classified(self):
        """Test GET with classified event"""
        self.event.classified = True
        self.event.save()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.anonymous, 403)


class TestSiteEventDetailAjaxView(
    TimelineEventMixin, TimelineEventStatusMixin, ProjectPermissionTestBase
):
    """Tests for SiteEventDetailAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            None, APP_NAME_PR, self.user_owner, 'test_event'
        )
        self.make_event_status(self.event, 'OK')
        self.regular_user = self.make_user('regular_user')
        self.url = reverse(
            'timeline:ajax_detail_site',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )

    def test_get(self):
        """Test SiteEventDetailAjaxView GET"""
        good_users = [self.superuser, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        good_users = [self.superuser, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_classified(self):
        """Test GET with classified event"""
        self.event.classified = True
        self.event.save()
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, bad_users, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.assert_response(self.url, self.no_role_users, 403)


class TestProjectEventExtraAjaxView(
    TimelineEventMixin, TimelineEventStatusMixin, ProjectPermissionTestBase
):
    """Tests for ProjectEventExtraAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, APP_NAME_PR, self.user_owner, 'project_create'
        )
        self.make_event_status(self.event, 'OK')
        self.url = reverse(
            'timeline:ajax_extra_project',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test ProjectEventExtraAjaxView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test SiteEventDetailAjaxView permissions with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 403)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)

    def test_get_classified(self):
        """Test GET with classified event"""
        self.event.classified = True
        self.event.save()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)


class TestSiteEventExtraAjaxView(
    TimelineEventMixin, TimelineEventStatusMixin, ProjectPermissionTestBase
):
    """Tests for SiteEventExtraAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            None,
            APP_NAME_PR,
            self.user_owner,
            'test_event',
            extra_data={'example_data': 'example_extra_data'},
        )
        self.event_status = self.make_event_status(self.event, 'OK')
        self.regular_user = self.make_user('regular_user')
        self.url = reverse(
            'timeline:ajax_extra_site',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )

    def test_get(self):
        """Test SiteEventExtraAjaxView GET"""
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_classified(self):
        """Test GET with classified event"""
        self.event.classified = True
        self.event.save()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 403)


class TestEventStatusExtraAjaxViewProject(
    TimelineEventMixin, TimelineEventStatusMixin, ProjectPermissionTestBase
):
    """Tests for EventStatusExtraAjaxView permissions with a project event"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, APP_NAME_PR, self.user_owner, 'project_create'
        )
        self.event_status = self.make_event_status(
            self.event, 'OK', extra_data={'example_data': 'example_extra_data'}
        )
        self.url = reverse(
            'timeline:ajax_extra_status',
            kwargs={'eventstatus': self.event_status.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test EventStatusExtraAjaxView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)

    def test_get_classified(self):
        """Test GET with classified event"""
        self.event.classified = True
        self.event.save()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.no_role_users, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.project.set_public_access(self.role_guest)
        self.assert_response(self.url, self.anonymous, 403)


class TestEventStatusExtraAjaxViewSite(
    TimelineEventMixin, TimelineEventStatusMixin, ProjectPermissionTestBase
):
    """Tests for EventStatusExtraAjaxView permissions with a site event"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            None, APP_NAME_PR, self.user_owner, 'test_event'
        )
        self.event_status = self.make_event_status(
            self.event,
            'OK',
            extra_data={'example_data': 'example_extra_data'},
        )
        self.regular_user = self.make_user('regular_user')
        self.url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.event_status.sodar_uuid,
            },
        )

    def test_get(self):
        """Test SiteEventExtraAjaxView GET"""
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_classified(self):
        """Test GET with classified event"""
        self.event.classified = True
        self.event.save()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.assert_response(self.url, self.anonymous, 403)
