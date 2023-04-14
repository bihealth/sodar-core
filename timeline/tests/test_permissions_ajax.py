"""Ajax API view permission tests for the timeline app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestProjectPermissionBase

from timeline.tests.test_models import (
    ProjectEventMixin,
    ProjectEventStatusMixin,
)


class TestTimelineAjaxPermissions(
    ProjectEventMixin, ProjectEventStatusMixin, TestProjectPermissionBase
):
    """Tests for timeline Ajax API view permissions"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            self.project, 'projectroles', self.user_owner, 'project_create'
        )
        self.event_status = self.make_event_status(
            self.event, 'OK', extra_data={'example_data': 'example_extra_data'}
        )
        self.site_event = self.make_event(
            None, 'projectroles', self.user_owner, 'test_event'
        )
        self.site_event_status = self.make_event_status(
            self.site_event,
            'OK',
            extra_data={'example_data': 'example_extra_data'},
        )
        self.regular_user = self.make_user('regular_user')

    def test_detail_project(self):
        """Test ProjectEventDetailAjaxView permissions"""
        url = reverse(
            'timeline:ajax_detail_project',
            kwargs={
                'projectevent': self.event.sodar_uuid,
            },
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_detail_project_anon(self):
        """Test ProjectEventDetailAjaxView permissions with anonymous access"""
        url = reverse(
            'timeline:ajax_detail_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 200)

    def test_detail_project_classified(self):
        """Test ProjectEventDetailAjaxView permissions with classified event"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_detail_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_detail_project_classified_anon(self):
        """Test ProjectEventDetailAjaxView with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_detail_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    def test_detail_site(self):
        """Test SiteEventDetailAjaxView permissions"""
        url = reverse(
            'timeline:ajax_detail_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.regular_user,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_detail_site_anon(self):
        """Test SiteEventDetailAjaxView permissions with anonymous access"""
        url = reverse(
            'timeline:ajax_detail_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403)

    def test_detail_site_classified(self):
        """Test SiteEventDetailAjaxView permissions with classified event"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_detail_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.regular_user,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_detail_site_classified_anon(self):
        """Test SiteEventDetailAjaxView permissions with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_detail_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403)

    def test_extra_data_project(self):
        """Test ProjectEventExtraDataAjaxView permissions"""
        url = reverse(
            'timeline:ajax_extra_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_extra_data_project_anon(self):
        """Test SiteEventDetailAjaxView permissions with anonymous access"""
        url = reverse(
            'timeline:ajax_extra_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403)

    def test_extra_data_project_classified(self):
        """Test ProjectEventExtraDataAjaxView with classified event"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_extra_data_project_classified_anon(self):
        """Test ProjectEventExtraDataAjaxView with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_project',
            kwargs={'projectevent': self.event.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    def test_extra_data_site(self):
        """Test SiteEventExtraDataAjaxView permissions"""
        url = reverse(
            'timeline:ajax_extra_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_extra_data_site_anon(self):
        """Test SiteEventDetailAjaxView permissions with anonymous access"""
        url = reverse(
            'timeline:ajax_extra_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 403)

    def test_extra_data_site_classified(self):
        """Test SiteEventExtraDataAjaxView permissions with classified event"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_extra_data_site_classified_anon(self):
        """Test SiteEventExtraDataAjaxView with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_site',
            kwargs={'projectevent': self.site_event.sodar_uuid},
        )
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, self.anonymous, 403)

    def test_status_extra_data_project(self):
        """Test ProjectEventExtraDataAjaxView permissions"""
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.event_status.sodar_uuid,
            },
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_status_extra_data_project_anon(self):
        """Test SiteEventDetailAjaxView permissions with anonymous access"""
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.site_event_status.sodar_uuid,
            },
        )
        self.assert_response(url, self.anonymous, 403)

    def test_status_extra_data_project_classified(self):
        """Test ProjectEventExtraDataAjaxView with classified event"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.event_status.sodar_uuid,
            },
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_status_extra_data_project_classified_anon(self):
        """Test ProjectEventExtraDataAjaxView with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.event_status.sodar_uuid,
            },
        )
        self.assert_response(url, self.anonymous, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    def test_status_extra_data_site(self):
        """Test SiteEventExtraDataAjaxView permissions"""
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.site_event_status.sodar_uuid,
            },
        )
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_status_extra_data_site_anon(self):
        """Test SiteEventDetailAjaxView permissions with anonymous access"""
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.site_event_status.sodar_uuid,
            },
        )
        self.assert_response(url, self.anonymous, 403)

    def test_status_extra_data_site_classified(self):
        """Test SiteEventExtraDataAjaxView permissions with classified event"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.site_event_status.sodar_uuid,
            },
        )
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_status_extra_data_site_classified_anon(self):
        """Test SiteEventExtraDataAjaxView with classified event and anonymous access"""
        self.event.classified = True
        self.event.save()
        url = reverse(
            'timeline:ajax_extra_status',
            kwargs={
                'eventstatus': self.site_event_status.sodar_uuid,
            },
        )
        self.assert_response(url, self.anonymous, 403)
