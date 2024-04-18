"""REST API view permission tests for the timeline app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions_api import ProjectAPIPermissionTestBase

from timeline.tests.test_models import TimelineEventMixin
from timeline.tests.test_views_api import (
    EVENT_NAME,
    EVENT_DESC,
    EXTRA_DATA,
)
from timeline.views_api import (
    TIMELINE_API_MEDIA_TYPE,
    TIMELINE_API_DEFAULT_VERSION,
)


class TimelineAPIPermissionTestBase(ProjectAPIPermissionTestBase):
    """Base class for timeline REST API view permission tests"""

    media_type = TIMELINE_API_MEDIA_TYPE
    api_version = TIMELINE_API_DEFAULT_VERSION


class TestProjectTimelineEventListAPIView(TimelineAPIPermissionTestBase):
    """Tests for ProjectTimelineEventListAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'timeline:api_list_project',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectTimelineEventListAPIView GET"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response_api(self.url, self.anonymous, 200)

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
        bad_users = [self.user_finder_cat, self.user_no_roles]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)


class TestSiteTimelineEventListAPIView(TimelineAPIPermissionTestBase):
    """Tests for SiteTimelineEventListAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('timeline:api_list_site')

    def test_get(self):
        """Test SiteTimelineEventListAPIView GET"""
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
            self.user_finder_cat,
            self.user_no_roles,
        ]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response_api(self.url, self.anonymous, 401)


class TestTimelineEventRetrieveAPIView(
    TimelineEventMixin, TimelineAPIPermissionTestBase
):
    """Tests for TimelineEventRetrieveAPIView"""

    def setUp(self):
        super().setUp()
        self.event = self.make_event(
            project=self.project,
            app='projectroles',
            user=self.user_owner,
            event_name=EVENT_NAME,
            description=EVENT_DESC,
            classified=False,
            extra_data=EXTRA_DATA,
        )
        self.url = reverse(
            'timeline:api_retrieve',
            kwargs={'timelineevent': self.event.sodar_uuid},
        )

    def test_get_project_event(self):
        """Test TimelineEventRetrieveAPIView GET with project event"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_project_event_anon(self):
        """Test GET with project event and anonymous access"""
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_project_event_classified(self):
        """Test GET with classified project event"""
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
        ]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)

    def test_get_site_event(self):
        """Test GET with site-wide event"""
        self.event.project = None
        self.event.save()
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
            self.user_finder_cat,
            self.user_no_roles,
        ]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_site_event_anon(self):
        """Test GET with site event and anonymous access"""
        self.event.project = None
        self.event.save()
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_site_event_classified(self):
        """Test GET with classified site event"""
        self.event.project = None
        self.event.classified = True
        self.event.save()
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
        ]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
