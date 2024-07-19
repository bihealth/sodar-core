"""Tests for email sending in the projectroles Django app"""

from django.conf import settings
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from test_plus.test import TestCase, RequestFactory

from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.email import (
    send_role_change_mail,
    send_generic_mail,
    send_project_create_mail,
    get_email_user,
    get_user_addr,
    get_email_footer,
    SETTINGS_LINK,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    SODARUserAdditionalEmailMixin,
)


app_settings = AppSettingAPI()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
SUBJECT_BODY = 'Test subject'
MESSAGE_BODY = 'Test message'
INVALID_EMAIL = 'ahch0La8lo0eeT8u'
CUSTOM_HEADER = 'Custom header'
CUSTOM_FOOTER = 'Custom footer'

USER_ADD_EMAIL = 'user1@example.com'
USER_ADD_EMAIL2 = 'user2@example.com'


class TestEmailSending(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    SODARUserAdditionalEmailMixin,
    TestCase,
):
    """Tests for email sending"""

    def _get_settings_link(self):
        """Return message footer settings link"""
        return SETTINGS_LINK.format(
            url=self.request.build_absolute_uri(
                reverse('userprofile:settings_update')
            )
        )

    def setUp(self):
        # Init roles
        self.init_roles()
        # Init users
        self.user_owner = self.make_user('owner')
        self.user_owner.email = 'owner_user@example.com'
        self.user_owner.save()
        self.user = self.make_user('user')
        self.user.email = 'user@example.com'
        self.user.save()

        # Init projects
        self.category = self.make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )

        self.project = self.make_project(
            'sub_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.user_as = self.make_assignment(
            self.project, self.user, self.role_contributor
        )
        # Set up request factory and default request
        self.factory = RequestFactory()
        self.request = self.factory.get(reverse('home'))
        self.request.user = self.user_owner

    def test_role_create_mail(self):
        """Test role creation mail sending"""
        email_sent = send_role_change_mail(
            change_type='create',
            project=self.project,
            user=self.user,
            role=self.user_as.role,
            request=self.request,
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user.email)
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_role_create_mail_additional(self):
        """Test role creation with additional sender emails"""
        self.make_email(self.user, USER_ADD_EMAIL)
        self.make_email(self.user, USER_ADD_EMAIL2)
        email_sent = send_role_change_mail(
            change_type='create',
            project=self.project,
            user=self.user,
            role=self.user_as.role,
            request=self.request,
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 3)
        self.assertEqual(
            mail.outbox[0].to,
            [self.user.email, USER_ADD_EMAIL, USER_ADD_EMAIL2],
        )
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_role_create_mail_additional_no_default(self):
        """Test role creation with additional sender emails but no default email"""
        self.make_email(self.user, USER_ADD_EMAIL)
        self.make_email(self.user, USER_ADD_EMAIL2)
        self.user.email = ''
        self.user.save()
        email_sent = send_role_change_mail(
            change_type='create',
            project=self.project,
            user=self.user,
            role=self.user_as.role,
            request=self.request,
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 2)
        self.assertEqual(
            mail.outbox[0].to,
            [USER_ADD_EMAIL, USER_ADD_EMAIL2],
        )
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_role_create_mail_additional_reply(self):
        """Test role creation with additional reply-to emails"""
        self.make_email(self.user_owner, USER_ADD_EMAIL)
        self.make_email(self.user_owner, USER_ADD_EMAIL2)
        email_sent = send_role_change_mail(
            change_type='create',
            project=self.project,
            user=self.user,
            role=self.user_as.role,
            request=self.request,
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(
            mail.outbox[0].to,
            [self.user.email],
        )
        self.assertEqual(len(mail.outbox[0].reply_to), 3)
        self.assertEqual(
            mail.outbox[0].reply_to,
            [self.user_owner.email, USER_ADD_EMAIL, USER_ADD_EMAIL2],
        )

    def test_role_update_mail(self):
        """Test role updating mail sending"""
        email_sent = send_role_change_mail(
            change_type='update',
            project=self.project,
            user=self.user,
            role=self.user_as.role,
            request=self.request,
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user.email)
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_role_delete_mail(self):
        """Test role deletion mail sending"""
        email_sent = send_role_change_mail(
            change_type='delete',
            project=self.project,
            user=self.user,
            role=None,
            request=self.request,
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user.email)
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_project_create_mail(self):
        """Test project creation mail sending"""
        new_project = self.make_project(
            'New Project', PROJECT_TYPE_PROJECT, self.category
        )
        self.make_assignment(new_project, self.user, self.role_owner)
        self.request.user = self.user
        email_sent = send_project_create_mail(
            project=new_project,
            request=self.request,
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user_owner.email)
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user.email)

    def test_generic_mail_user(self):
        """Test send_generic_mail() with a User recipient"""
        email_sent = send_generic_mail(
            subject_body=SUBJECT_BODY,
            message_body=MESSAGE_BODY,
            recipient_list=[self.user],
            request=self.request,
            reply_to=[self.user_owner.email],
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user.email)
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_generic_mail_user_additional(self):
        """Test send_generic_mail() with a User and additional emails"""
        self.make_email(self.user, USER_ADD_EMAIL)
        self.make_email(self.user, USER_ADD_EMAIL2)
        email_sent = send_generic_mail(
            subject_body=SUBJECT_BODY,
            message_body=MESSAGE_BODY,
            recipient_list=[self.user],
            request=self.request,
            reply_to=[self.user_owner.email],
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 3)
        self.assertEqual(
            mail.outbox[0].to,
            [self.user.email, USER_ADD_EMAIL, USER_ADD_EMAIL2],
        )
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_generic_mail_str(self):
        """Test send_generic_mail() with an email string recipient"""
        email_sent = send_generic_mail(
            subject_body=SUBJECT_BODY,
            message_body=MESSAGE_BODY,
            recipient_list=[self.user.email],
            request=self.request,
            reply_to=[self.user_owner.email],
        )
        self.assertEqual(email_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user.email)
        self.assertEqual(len(mail.outbox[0].reply_to), 1)
        self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_generic_mail_multiple(self):
        """Test send_generic_mail() with multiple recipients"""
        user_new = self.make_user('newuser')
        email_sent = send_generic_mail(
            subject_body=SUBJECT_BODY,
            message_body=MESSAGE_BODY,
            recipient_list=[self.user_owner, user_new],
            request=self.request,
        )
        self.assertEqual(email_sent, 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_get_email_footer(self):
        """Test get_email_footer() with default admin"""
        footer = get_email_footer(self.request)
        self.assertIn(settings.ADMINS[0][0], footer)
        self.assertIn(settings.ADMINS[0][1], footer)
        self.assertIn(self._get_settings_link(), footer)

    @override_settings(ADMINS=[])
    def test_get_email_footer_no_admin(self):
        """Test get_email_footer() with empty admin list"""
        self.assertEqual(
            get_email_footer(self.request), self._get_settings_link()
        )

    def test_get_email_footer_no_settings(self):
        """Test get_email_footer() with no settings link"""
        footer = get_email_footer(self.request, settings_link=False)
        self.assertIn(settings.ADMINS[0][0], footer)
        self.assertIn(settings.ADMINS[0][1], footer)
        self.assertNotIn(self._get_settings_link(), footer)

    @override_settings(PROJECTROLES_EMAIL_HEADER=CUSTOM_HEADER)
    def test_custom_header(self):
        """Test send_generic_mail() with custom header"""
        send_generic_mail(
            subject_body=SUBJECT_BODY,
            message_body=MESSAGE_BODY,
            recipient_list=[self.user_owner.email],
            request=self.request,
            reply_to=[self.user_owner.email],
        )
        self.assertIn(CUSTOM_HEADER, mail.outbox[0].body)
        self.assertNotIn(CUSTOM_FOOTER, mail.outbox[0].body)

    @override_settings(PROJECTROLES_EMAIL_FOOTER=CUSTOM_FOOTER)
    def test_custom_footer(self):
        """Test send_generic_mail() with custom footer"""
        send_generic_mail(
            subject_body=SUBJECT_BODY,
            message_body=MESSAGE_BODY,
            recipient_list=[self.user_owner.email],
            request=self.request,
            reply_to=[self.user_owner.email],
        )
        self.assertNotIn(CUSTOM_HEADER, mail.outbox[0].body)
        self.assertIn(CUSTOM_FOOTER, mail.outbox[0].body)

    def test_get_email_user(self):
        """Test get_email_user()"""
        self.assertEqual(
            get_email_user(self.user_owner), 'owner (owner_user@example.com)'
        )

    def test_get_email_user_no_email(self):
        """Test get_email_user() without email"""
        self.user_owner.email = ''
        self.assertEqual(get_email_user(self.user_owner), 'owner')

    def test_get_email_user_name(self):
        """Test get_email_user() with name"""
        self.user_owner.name = 'Owner User'
        self.assertEqual(
            get_email_user(self.user_owner),
            'Owner User (owner_user@example.com)',
        )

    def test_get_email_user_first_last_name(self):
        """Test get_email_user() with first and last name"""
        self.user_owner.first_name = 'Owner'
        self.user_owner.last_name = 'User'
        self.assertEqual(
            get_email_user(self.user_owner),
            'Owner User (owner_user@example.com)',
        )

    def test_get_user_addr(self):
        """Test get_user_addr() with standard user email"""
        self.assertEqual(get_user_addr(self.user), [self.user.email])

    def test_get_user_addr_additional(self):
        """Test get_user_addr() with additional user emails"""
        self.make_email(self.user, USER_ADD_EMAIL)
        self.make_email(self.user, USER_ADD_EMAIL2)
        self.assertEqual(
            get_user_addr(self.user),
            [self.user.email, USER_ADD_EMAIL, USER_ADD_EMAIL2],
        )

    def test_get_user_addr_additional_unverified(self):
        """Test get_user_addr() with additional and unverified user emails"""
        self.make_email(self.user, USER_ADD_EMAIL)
        self.make_email(self.user, USER_ADD_EMAIL2, verified=False)
        self.assertEqual(
            get_user_addr(self.user), [self.user.email, USER_ADD_EMAIL]
        )

    def test_get_user_addr_additional_no_default(self):
        """Test get_user_addr() with additional user emails and no default"""
        self.make_email(self.user, USER_ADD_EMAIL)
        self.make_email(self.user, USER_ADD_EMAIL2)
        self.user.email = ''
        self.assertEqual(
            get_user_addr(self.user), [USER_ADD_EMAIL, USER_ADD_EMAIL2]
        )
