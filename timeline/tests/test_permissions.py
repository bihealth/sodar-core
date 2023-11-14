"""Tests for UI view permissions in the timeline app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestProjectPermissionBase


class TestProjectTimelineView(TestProjectPermissionBase):
    """Tests for ProjectTimelineView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'timeline:list_project', kwargs={'project': self.project.sodar_uuid}
        )

    def test_get(self):
        """Test ProjectTimelineView GET"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonynomus access"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)


class TestSiteTimelineView(TestProjectPermissionBase):
    """Tests for SiteTimelineView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('timeline:list_site')

    def test_get(self):
        """Test SiteTimelineView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonynomus access"""
        self.assert_response(self.url, self.anonymous, 302)


class TestAdminTimelineView(TestProjectPermissionBase):
    """Tests for AdminTimelineView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('timeline:list_admin')

    def test_get(self):
        """Test AdminTimelineView GET"""
        good_users = [self.superuser]
        bad_users = [
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 302)


class TestProjectObjectTimelineView(TestProjectPermissionBase):
    """Tests for ProjectObjectTimelineView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': 'User',
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )

    def test_get(self):
        """Test ProjectObjectTimelineView GET"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_event_object_list_anon(self):
        """Test GET with anonynomus access"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)


class TestSiteObjectTimelineView(TestProjectPermissionBase):
    """Tests for SiteObjectTimelineView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'timeline:list_object_site',
            kwargs={
                'object_model': 'User',
                'object_uuid': self.user_owner.sodar_uuid,
            },
        )

    def test_get(self):
        """Test SiteObjectTimelineView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, self.anonymous, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)
