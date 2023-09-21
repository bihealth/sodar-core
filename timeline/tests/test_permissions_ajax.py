"""Tests for Ajax view permissions in the timeline app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestProjectPermissionBase

from timeline.tests.test_models import (
    ProjectEventMixin,
    ProjectEventStatusMixin,
)


class TestProjectEventDetailAjaxView(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectPermissionBase
):
    """Tests for ProjectEventDetailAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, 'projectroles', self.user_owner, 'project_create'
        )
        self.make_event_status(self.event, 'OK')
        self.url = reverse(
            'timeline:ajax_detail_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectEventDetailAjaxView GET"""
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)


class TestSiteEventDetailAjaxView(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectPermissionBase
):
    """Tests for SiteEventDetailAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            None, 'projectroles', self.user_owner, 'test_event'
        )
        self.make_event_status(self.event, 'OK')
        self.regular_user = self.make_user('regular_user')
        self.url = reverse(
            'timeline:ajax_detail_site',
            kwargs={'projectevent': self.event.sodar_uuid},
        )

    def test_get(self):
        """Test SiteEventDetailAjaxView GET"""
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
        self.assert_response(self.url, self.anonymous, 403)


class TestProjectEventExtraAjaxView(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectPermissionBase
):
    """Tests for ProjectEventExtraAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, 'projectroles', self.user_owner, 'project_create'
        )
        self.make_event_status(self.event, 'OK')
        self.url = reverse(
            'timeline:ajax_extra_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectEventExtraAjaxView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test SiteEventDetailAjaxView permissions with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)


class TestSiteEventExtraAjaxView(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectPermissionBase
):
    """Tests for SiteEventExtraAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            None,
            'projectroles',
            self.user_owner,
            'test_event',
            extra_data={'example_data': 'example_extra_data'},
        )
        self.event_status = self.make_event_status(self.event, 'OK')
        self.regular_user = self.make_user('regular_user')
        self.url = reverse(
            'timeline:ajax_extra_site',
            kwargs={'projectevent': self.event.sodar_uuid},
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
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectPermissionBase
):
    """Tests for EventStatusExtraAjaxView permissions with a project event"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, 'projectroles', self.user_owner, 'project_create'
        )
        self.event_status = self.make_event_status(
            self.event, 'OK', extra_data={'example_data': 'example_extra_data'}
        )
        self.url = reverse(
            'timeline:ajax_extra_status',
            kwargs={'eventstatus': self.event_status.sodar_uuid},
        )

    def test_get(self):
        """Test EventStatusExtraAjaxView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_classified_anon(self):
        """Test GET with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 403)


class TestEventStatusExtraAjaxViewSite(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectPermissionBase
):
    """Tests for EventStatusExtraAjaxView permissions with a site event"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            None, 'projectroles', self.user_owner, 'test_event'
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
