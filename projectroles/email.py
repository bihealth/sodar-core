"""Email creation and sending for the projectroles app"""

import logging
import re

from typing import Optional

from django.conf import settings
from django.contrib import auth, messages
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.urls import reverse
from django.utils.timezone import localtime

from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    Role,
    ProjectInvite,
    SODARUser,
    SODARUserAdditionalEmail,
    SODAR_CONSTANTS,
    ROLE_RANKING,
)
from projectroles.plugins import PluginAPI
from projectroles.utils import get_display_name


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
plugin_api = PluginAPI()
User = auth.get_user_model()


# Settings
SUBJECT_PREFIX = settings.EMAIL_SUBJECT_PREFIX.strip() + ' '
EMAIL_SENDER = settings.EMAIL_SENDER
DEBUG = settings.DEBUG
SITE_TITLE = settings.SITE_INSTANCE_TITLE

# SODAR constants
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']

# Local constants
APP_NAME = 'projectroles'
EMAIL_RE = re.compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')


# Generic Elements -------------------------------------------------------------


MESSAGE_HEADER = r'''
Dear {recipient},

This email has been automatically sent to you by {site_title}.

'''.lstrip()

MESSAGE_HEADER_NO_RECIPIENT = r'''
This email has been automatically sent to you by {site_title}.
'''.lstrip()

NO_REPLY_NOTE = r'''
Please do not reply to this email.
'''

MESSAGE_FOOTER = r'''

For support and reporting issues regarding {site_title},
contact {admin_name} ({admin_email}).
'''

SETTINGS_LINK = r'''
You can manage receiving of automated emails in your user settings:
{url}
'''


# Role Change Template ---------------------------------------------------------


SUBJECT_ROLE_CREATE = 'Membership granted for {project_label} "{project}"'
SUBJECT_ROLE_UPDATE = 'Membership changed in {project_label} "{project}"'
SUBJECT_ROLE_DELETE = 'Membership removed from {project_label} "{project}"'
SUBJECT_ROLE_LEAVE = 'Member {user_name} left {project_label} "{project}"'

MESSAGE_ROLE_CREATE = r'''
{issuer} has granted you the membership
in {project_label} "{project}" with the role of "{role}".

To access the {project_label} in {site_title}, please click on
the following link:
{project_url}
'''.lstrip()

MESSAGE_ROLE_UPDATE = r'''
{issuer} has changed your membership
role in {project_label} "{project}" into "{role}".

To access the {project_label} in {site_title}, please click on
the following link:
{project_url}
'''.lstrip()

MESSAGE_ROLE_DELETE = r'''
{issuer} has removed your membership from {project_label} "{project}".
'''.lstrip()

MESSAGE_ROLE_LEAVE = r'''
Member {user_name} has left the {project_label} "{project}".
For them to regain access, it has to be granted again by {project_label}
owner or delegate.
'''.lstrip()


# Invite Template --------------------------------------------------------------


SUBJECT_INVITE = 'Invitation for {project_label} "{project}"'

MESSAGE_INVITE_BODY = r'''
You have been invited by {issuer}
to share data in the {project_label} "{project}" with the
role of "{role}".

To accept the invitation and access the {project_label} in {site_title},
please click on the following link:
{invite_url}

Please note that the link is only to be used once. After successfully
accepting the invitation, please access the project with its URL or
through the project list on the site's "Home" page.

This invitation will expire on {date_expire}.
'''

MESSAGE_INVITE_ISSUER = r'''
Message from the sender of this invitation:
----------------------------------------
{}
----------------------------------------
'''


# Invite Acceptance Notification Template --------------------------------------


SUBJECT_ACCEPT = 'Invitation accepted by {user} for {project_label} "{project}"'

MESSAGE_ACCEPT_BODY = r'''
Invitation sent by you for role of "{role}" in {project_label} "{project}"
has been accepted by {user}.
They have been granted access in the {project_label} accordingly.
'''.lstrip()


# Invite Expiry Notification Template ------------------------------------------


SUBJECT_EXPIRY = 'Expired invitation used by {user_name} in "{project}"'

MESSAGE_EXPIRY_BODY = r'''
Invitation sent by you for role of "{role}" in {project_label} "{project}"
was attempted to be used by {user_name} ({user_email}).

This invitation has expired on {date_expire}. Because of this,
access was not granted to the user.

Please add the role manually with "Add Member", if you still wish
to grant the user access to the {project_label}.
'''.lstrip()


# Project/Category Creation Notification Template ------------------------------


SUBJECT_PROJECT_CREATE = '{project_type} "{project}" created by {user}'

MESSAGE_PROJECT_CREATE_BODY = r'''
{user} has created a new {project_type}
under "{category}".
You are receiving this email because you are the owner of the parent category.
You have automatically inherited owner rights to the created {project_type}.

Title: {project}
Owner: {owner}

You can access the project at the following link:
{project_url}
'''.lstrip()


# Project/Category Moving Notification Template ------------------------------


SUBJECT_PROJECT_MOVE = '{project_type} "{project}" moved by {user}'

MESSAGE_PROJECT_MOVE_BODY = r'''
{user} has moved the {project_type} "{project}"
under "{category}".
You are receiving this email because you are the owner of the parent category.
You have automatically inherited owner rights to the created {project_type}.

Title: {project}
Owner: {owner}

You can access the project at the following link:
{project_url}
'''.lstrip()


# Project Archiving Template ---------------------------------------------------


SUBJECT_PROJECT_ARCHIVE = '{project_label_title} "{project}" archived by {user}'

MESSAGE_PROJECT_ARCHIVE = r'''
{user} has archived "{project}".
The {project_label} is now read-only. Modifying data in
{project_label} apps has been disabled. Existing project data
can still be accessed and user roles can be modified.

You can access the archived {project_label} at the following link:
{project_url}
'''.lstrip()


# Project Unarchiving Template -------------------------------------------------


SUBJECT_PROJECT_UNARCHIVE = (
    '{project_label_title} "{project}" unarchived by {user}'
)

MESSAGE_PROJECT_UNARCHIVE = r'''
{user} has unarchived "{project}".
{project_label_title} data can now be modified and write
access for users has been restored.

You can access the {project_label} at the following link:
{project_url}
'''.lstrip()


# Project Deletion Template ----------------------------------------------------

SUBJECT_PROJECT_DELETE = '{project_label_title} "{project}" deleted by {user}'

MESSAGE_PROJECT_DELETE = r'''
{user} has deleted "{project}".
The {project_label} has been removed from the site and can no
longer be accessed.
'''.lstrip()


# Email composing helpers ------------------------------------------------------


def get_email_user(user: SODARUser) -> str:
    """
    Return a string representation of a user object for emails.

    :param user: SODARUser object
    :return: string
    """
    ret = user.get_full_name()
    if user.email:
        ret += f' ({user.email})'
    return ret


def get_invite_body(
    project: Project,
    issuer: SODARUser,
    role_name: str,
    invite_url: str,
    date_expire_str: str,
) -> str:
    """
    Return the invite content header.

    :param project: Project object
    :param issuer: User object
    :param role_name: Display name of the Role object
    :param invite_url: Generated URL for the invite
    :param date_expire_str: Expiry date as a pre-formatted string
    :return: string
    """
    body = MESSAGE_HEADER_NO_RECIPIENT.format(site_title=SITE_TITLE)
    body += MESSAGE_INVITE_BODY.format(
        issuer=get_email_user(issuer),
        project=project.title,
        role=role_name,
        invite_url=invite_url,
        date_expire=date_expire_str,
        site_title=SITE_TITLE,
        project_label=get_display_name(project.type),
    )
    if not issuer.email and not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        body += NO_REPLY_NOTE
    return body


def get_invite_message(message: Optional[str] = None) -> str:
    """
    Return the message from invite issuer, of empty string if not set.

    :param message: Optional user message as string
    :return: string
    """
    if message and len(message) > 0:
        return MESSAGE_INVITE_ISSUER.format(message)
    return ''


def get_email_header(header: str) -> str:
    """
    Return the email header.

    :param header: Header string
    :return: string
    """
    return getattr(settings, 'PROJECTROLES_EMAIL_HEADER', None) or header


def get_email_footer(request: HttpRequest, settings_link: bool = True) -> str:
    """
    Return the email footer.

    :param request: HttpRequest object
    :param settings_link: Include link to user settings if True (optional)
    :return: string
    """
    footer = ''
    custom_footer = getattr(settings, 'PROJECTROLES_EMAIL_FOOTER', None)
    support_contact = getattr(settings, 'PROJECTROLES_SUPPORT_CONTACT', None)
    admin_recipient = settings.ADMINS[0] if settings.ADMINS else None
    if custom_footer:
        footer += '\n' + custom_footer
    elif support_contact and ':' in support_contact:
        footer += MESSAGE_FOOTER.format(
            site_title=SITE_TITLE,
            admin_name=support_contact.split(':')[0],
            admin_email=support_contact.split(':')[1],
        )
    elif admin_recipient:
        footer += MESSAGE_FOOTER.format(
            site_title=SITE_TITLE,
            admin_name=admin_recipient[0],
            admin_email=admin_recipient[1],
        )
    # Add user settings link if enabled and userprofile app is active
    if request and settings_link and plugin_api.get_app_plugin('userprofile'):
        footer += SETTINGS_LINK.format(
            url=request.build_absolute_uri(
                reverse('userprofile:settings_update')
            )
        )
    return footer


def get_invite_subject(project: Project) -> str:
    """
    Return invite email subject.

    :param project: Project object
    :return: string
    """
    return SUBJECT_PREFIX + SUBJECT_INVITE.format(
        project=project.title, project_label=get_display_name(project.type)
    )


def get_role_change_subject(change_type: str, project: Project) -> str:
    """
    Return role change email subject.

    :param change_type: Change type ('create', 'update', 'delete')
    :param project: Project object
    :return: String
    """
    subject = SUBJECT_PREFIX
    subject_kwargs = {
        'project': project.title,
        'project_label': get_display_name(project.type),
    }
    if change_type == 'create':
        subject += SUBJECT_ROLE_CREATE.format(**subject_kwargs)
    elif change_type == 'update':
        subject += SUBJECT_ROLE_UPDATE.format(**subject_kwargs)
    elif change_type == 'delete':
        subject += SUBJECT_ROLE_DELETE.format(**subject_kwargs)
    return subject


def get_role_change_body(
    change_type: str,
    project: Project,
    user_name: str,
    role_name: str,
    issuer: SODARUser,
    request: HttpRequest,
) -> str:
    """
    Return role change email body.

    :param change_type: Change type ('create', 'update', 'delete')
    :param project: Project object
    :param user_name: Name of target user
    :param role_name: Name of role as string
    :param issuer: User object for issuing user
    :param request: HttpRequest object
    :return: String
    """
    project_url = request.build_absolute_uri(
        reverse('projectroles:detail', kwargs={'project': project.sodar_uuid})
    )
    body = get_email_header(
        MESSAGE_HEADER.format(recipient=user_name, site_title=SITE_TITLE)
    )
    if change_type == 'create':
        body += MESSAGE_ROLE_CREATE.format(
            issuer=get_email_user(issuer),
            role=role_name,
            project=project.title,
            project_url=project_url,
            site_title=SITE_TITLE,
            project_label=get_display_name(project.type),
        )

    elif change_type == 'update':
        body += MESSAGE_ROLE_UPDATE.format(
            issuer=get_email_user(issuer),
            role=role_name,
            project=project.title,
            project_url=project_url,
            site_title=SITE_TITLE,
            project_label=get_display_name(project.type),
        )

    elif change_type == 'delete':
        body += MESSAGE_ROLE_DELETE.format(
            issuer=get_email_user(issuer),
            project=project.title,
            project_label=get_display_name(project.type),
        )
    if not issuer.email and not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        body += NO_REPLY_NOTE
    body += get_email_footer(request)
    return body


def get_user_addr(user: SODARUser) -> list[str]:
    """
    Return all the email addresses for a user as a list. Verified emails set as
    SODARUserAdditionalEmail objects are included. If a user has no main email
    set but additional emails exist, the latter are returned.

    :param user: User object
    :return: list
    """
    ret = []
    if user.email:
        ret.append(user.email)
    for e in SODARUserAdditionalEmail.objects.filter(
        user=user, verified=True
    ).order_by('email'):
        ret.append(e.email)
    return ret


def get_project_modify_recipients(
    recipients: list[SODARUser],
) -> list[SODARUser]:
    """
    Filter recipient list for project modify emails. Excludes users with
    notify_email_project set False.

    :param recipients: List of SODARUser objects
    :return: List of SODARUser objects
    """
    return [
        u
        for u in recipients
        if app_settings.get(APP_NAME, 'notify_email_project', user=u)
    ]


def send_mail(
    subject: str,
    message: str,
    recipient_list: list,
    request: Optional[HttpRequest] = None,
    reply_to: Optional[list] = None,
    cc: Optional[list] = None,
    bcc: Optional[list] = None,
) -> int:
    """
    Wrapper for send_mail() with logging and error messaging.

    :param subject: Message subject (string)
    :param message: Message body (string)
    :param recipient_list: Recipients of email (list)
    :param request: HttpRequest object (optional)
    :param reply_to: List of emails for the "reply-to" header (optional)
    :param cc: List of emails for "cc" field (optional)
    :param bcc: List of emails for "bcc" field (optional)
    :return: Amount of sent email (int)
    """
    try:
        e = EmailMessage(
            subject=subject,
            body=message,
            from_email=EMAIL_SENDER,
            to=recipient_list,
            reply_to=reply_to if isinstance(reply_to, list) else [],
            cc=cc if isinstance(cc, list) else [],
            bcc=bcc if isinstance(bcc, list) else [],
        )
        ret = e.send(fail_silently=False)
        logger.debug(
            '{} email{} sent to {}'.format(
                ret, 's' if ret != 1 else '', ', '.join(recipient_list)
            )
        )
        return ret
    except Exception as ex:
        error_msg = f'Error sending email: {str(ex)}'
        logger.error(error_msg)
        if DEBUG:
            raise ex
        if request:
            messages.error(request, error_msg)
        return 0


# Sending functions ------------------------------------------------------------


def send_role_change_mail(
    change_type: str,
    project: Project,
    user: SODARUser,
    role: Role,
    request: HttpRequest,
) -> int:
    """
    Send email to user when their role in a project has been changed.

    :param change_type: Change type ('create', 'update', 'delete')
    :param project: Project object
    :param user: User object
    :param role: Role object (can be None for deletion)
    :param request: HttpRequest object
    :return: Amount of sent email (int)
    """
    subject = get_role_change_subject(change_type, project)
    message = get_role_change_body(
        change_type=change_type,
        project=project,
        user_name=user.get_full_name(),
        role_name=role.name if role else '',
        issuer=request.user,
        request=request,
    )
    issuer_emails = get_user_addr(request.user)
    return send_mail(
        subject, message, get_user_addr(user), request, issuer_emails
    )


def send_project_leave_mail(
    project: Project, user: SODARUser, request: Optional[HttpRequest] = None
) -> int:
    """
    Send email to project owners and delegates when a user leaves a project.

    :param project: Project object
    :param user: User object
    :param request: HttpRequest object or None
    :return: Amount of sent email (int)
    """
    p_label = get_display_name(project.type)
    subject = SUBJECT_PREFIX + SUBJECT_ROLE_LEAVE.format(
        user_name=user.username, project_label=p_label, project=project.title
    )
    message = MESSAGE_ROLE_LEAVE.format(
        user_name=user.username, project_label=p_label, project=project.title
    )
    mail_count = 0
    recipients = [
        a.user
        for a in project.get_roles(max_rank=ROLE_RANKING[PROJECT_ROLE_DELEGATE])
        if a.user != user
        and a.user.is_active
        and app_settings.get(APP_NAME, 'notify_email_role', user=a.user)
    ]
    for r in recipients:
        mail_count += send_mail(subject, message, get_user_addr(r), request)
    return mail_count


def send_invite_mail(invite: ProjectInvite, request: HttpRequest) -> int:
    """
    Send an email invitation to user not yet registered in the system.

    :param invite: ProjectInvite object
    :param request: HttpRequest object
    :return: Amount of sent email (int)
    """
    message = get_invite_body(
        project=invite.project,
        issuer=invite.issuer,
        role_name=invite.role.name,
        invite_url=invite.get_url(request),
        date_expire_str=localtime(invite.date_expire).strftime(
            '%Y-%m-%d %H:%M'
        ),
    )
    message += get_invite_message(invite.message)
    message += get_email_footer(request, settings_link=False)
    subject = get_invite_subject(invite.project)
    issuer_emails = get_user_addr(invite.issuer)
    return send_mail(subject, message, [invite.email], request, issuer_emails)


def send_invite_accept_mail(
    invite: ProjectInvite, request: HttpRequest, user: SODARUser
) -> int:
    """
    Send a notification email to the issuer of an invitation when a user
    accepts the invitation.

    :param invite: ProjectInvite object
    :param request: HttpRequest object
    :param user: User invited
    :return: Amount of sent email (int)
    """
    subject = SUBJECT_PREFIX + SUBJECT_ACCEPT.format(
        user=get_email_user(user),
        project_label=get_display_name(invite.project.type),
        project=invite.project.title,
    )
    message = get_email_header(
        MESSAGE_HEADER.format(
            recipient=invite.issuer.get_full_name(), site_title=SITE_TITLE
        )
    )
    message += MESSAGE_ACCEPT_BODY.format(
        role=invite.role.name,
        project=invite.project.title,
        user=get_email_user(user),
        site_title=SITE_TITLE,
        project_label=get_display_name(invite.project.type),
    )

    if not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        message += NO_REPLY_NOTE
    message += get_email_footer(request)
    return send_mail(subject, message, get_user_addr(invite.issuer), request)


def send_invite_expiry_mail(
    invite: ProjectInvite, request: HttpRequest, user_name: str
) -> int:
    """
    Send a notification email to the issuer of an invitation when a user
    attempts to accept an expired invitation.

    :param invite: ProjectInvite object
    :param request: HttpRequest object
    :param user_name: User name of invited user
    :return: Amount of sent email (int)
    """
    subject = SUBJECT_PREFIX + SUBJECT_EXPIRY.format(
        user_name=user_name, project=invite.project.title
    )
    message = get_email_header(
        MESSAGE_HEADER.format(
            recipient=invite.issuer.get_full_name(), site_title=SITE_TITLE
        )
    )
    message += MESSAGE_EXPIRY_BODY.format(
        role=invite.role.name,
        project=invite.project.title,
        user_name=user_name,
        user_email=invite.email,
        date_expire=localtime(invite.date_expire).strftime('%Y-%m-%d %H:%M'),
        site_title=SITE_TITLE,
        project_label=get_display_name(invite.project.type),
    )

    if not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        message += NO_REPLY_NOTE
    message += get_email_footer(request)
    return send_mail(subject, message, get_user_addr(invite.issuer), request)


def send_project_create_mail(
    project: Project, recipients: list[SODARUser], request: HttpRequest
) -> int:
    """
    Send email about project creation to owners and delegates of the parent
    category, excluding the project creator. Also excludes users who have set
    notify_email_role to False.

    Received recipient list must be filtered for email preferences.

    :param project: Project object
    :param recipients: List of SODARUser objects
    :param request: HttpRequest object
    :return: Amount of sent email (int)
    """
    parent = project.parent
    if not parent:
        return 0
    recipients = get_project_modify_recipients(recipients)
    if not recipients:
        return 0
    owner = project.get_owner().user

    subject = SUBJECT_PREFIX + SUBJECT_PROJECT_CREATE.format(
        project_type=get_display_name(project.type, title=True),
        project=project.title,
        user=get_email_user(request.user),
    )
    mail_count = 0
    for r in recipients:
        message = get_email_header(
            MESSAGE_HEADER.format(
                recipient=r.get_full_name(), site_title=SITE_TITLE
            )
        )
        message += MESSAGE_PROJECT_CREATE_BODY.format(
            user=get_email_user(request.user),
            project_type=get_display_name(project.type),
            category=parent.title,
            project=project.title,
            owner=get_email_user(owner),
            project_url=request.build_absolute_uri(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                )
            ),
        )
        message += get_email_footer(request)
        mail_count += send_mail(
            subject,
            message,
            get_user_addr(r),
            request,
            reply_to=get_user_addr(request.user),
        )
    return mail_count


def send_project_move_mail(
    project: Project, recipients: list[SODARUser], request: HttpRequest
) -> int:
    """
    Send email about project being moved to the owners and delegates of the
    parent category, excluding the project creator. Also excludes users who have
    set notify_email_role to False.

    Received recipient list must be filtered for email preferences.

    :param project: Project object
    :param recipients: List of SODARUser objects
    :param request: HttpRequest object
    :return: Amount of sent email (int)
    """
    parent = project.parent
    if not parent:
        return 0
    recipients = get_project_modify_recipients(recipients)
    if not recipients:
        return 0
    owner = project.get_owner().user

    subject = SUBJECT_PREFIX + SUBJECT_PROJECT_MOVE.format(
        project_type=get_display_name(project.type, title=True),
        project=project.title,
        user=get_email_user(request.user),
    )
    mail_count = 0
    for r in recipients:
        message = get_email_header(
            MESSAGE_HEADER.format(
                recipient=r.get_full_name(), site_title=SITE_TITLE
            )
        )
        message += MESSAGE_PROJECT_MOVE_BODY.format(
            user=get_email_user(request.user),
            project_type=get_display_name(project.type),
            category=parent.title,
            project=project.title,
            owner=get_email_user(owner),
            project_url=request.build_absolute_uri(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                )
            ),
        )
        message += get_email_footer(request)
        mail_count += send_mail(
            subject,
            message,
            get_user_addr(r),
            request,
            reply_to=get_user_addr(request.user),
        )
    return mail_count


def send_project_archive_mail(
    project: Project, action: str, request: HttpRequest
) -> int:
    """
    Send a notification email on project archiving or unarchiving.

    :param project: Project object
    :param action: String ("archive" or "unarchive")
    :param request: HttpRequest object
    :return: Amount of sent email (int)
    """
    recipients = [
        a.user
        for a in project.get_roles()
        if a.user != request.user
        and a.user.is_active
        and app_settings.get(APP_NAME, 'notify_email_project', user=a.user)
    ]
    if not recipients:
        return 0
    mail_count = 0

    if action == 'archive':
        subject = SUBJECT_PROJECT_ARCHIVE
        body = MESSAGE_PROJECT_ARCHIVE
    else:
        subject = SUBJECT_PROJECT_UNARCHIVE
        body = MESSAGE_PROJECT_UNARCHIVE
    subject = SUBJECT_PREFIX + subject.format(
        project_label_title=get_display_name(project.type, title=True),
        project=project.title,
        user=request.user.get_full_name(),
    )
    body_final = body.format(
        project_label_title=get_display_name(project.type, title=True),
        project_label=get_display_name(project.type),
        project=project.title,
        user=request.user.get_full_name(),
        project_url=request.build_absolute_uri(
            reverse(
                'projectroles:detail', kwargs={'project': project.sodar_uuid}
            )
        ),
    )

    for r in recipients:
        message = get_email_header(
            MESSAGE_HEADER.format(
                recipient=r.get_full_name(), site_title=SITE_TITLE
            )
        )
        message += body_final
        if not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
            message += NO_REPLY_NOTE
        message += get_email_footer(request)
        mail_count += send_mail(subject, message, get_user_addr(r), request)
    return mail_count


def send_project_delete_mail(
    project: Project, recipients: list[SODARUser], request: HttpRequest
) -> int:
    """
    Send a notification email on project deletion.

    Received recipient list must be filtered for email preferences.

    :param project: Project object
    :param recipients: List of SODARUser objects
    :param request: HttpRequest object
    :return: Amount of sent email (int)
    """
    user = request.user
    recipients = [
        u
        for u in recipients
        if app_settings.get(APP_NAME, 'notify_email_project', user=u)
    ]
    if not recipients:
        return 0

    mail_count = 0
    subject = SUBJECT_PROJECT_DELETE
    body = MESSAGE_PROJECT_DELETE
    subject = SUBJECT_PREFIX + subject.format(
        project_label_title=get_display_name(project.type, title=True),
        project=project.title,
        user=user.get_full_name(),
    )
    body_final = body.format(
        project_label=get_display_name(project.type),
        project=project.title,
        user=user.get_full_name(),
    )

    for r in recipients:
        message = get_email_header(
            MESSAGE_HEADER.format(
                recipient=r.get_full_name(), site_title=SITE_TITLE
            )
        )
        message += body_final
        if not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
            message += NO_REPLY_NOTE
        message += get_email_footer(request)
        mail_count += send_mail(subject, message, get_user_addr(r), request)
    return mail_count


def send_generic_mail(
    subject_body: str,
    message_body: str,
    recipient_list: list,
    request: Optional[HttpRequest] = None,
    reply_to: Optional[list] = None,
    cc: Optional[list] = None,
    bcc: Optional[list] = None,
    settings_link: bool = True,
) -> int:
    """
    Send a generic mail with standard header and footer and no-reply
    notifications.

    :param subject_body: Subject body without prefix (string)
    :param message_body: Message body before header or footer (string)
    :param recipient_list: Recipients (list of User objects or email strings)
    :param request: HttpRequest object (optional)
    :param reply_to: List of emails for the "reply-to" header (optional)
    :param cc: List of emails for "cc" field (optional)
    :param bcc: List of emails for "bcc" field (optional)
    :param settings_link: Include link to user settings if True (optional)
    :return: Amount of mail sent (int)
    """
    subject = SUBJECT_PREFIX + subject_body
    ret = 0
    for recipient in recipient_list:
        if isinstance(recipient, User):
            recp_name = recipient.get_full_name()
            recp_addr = get_user_addr(recipient)
        else:
            recp_name = 'recipient'
            recp_addr = [recipient]
        message = get_email_header(
            MESSAGE_HEADER.format(recipient=recp_name, site_title=SITE_TITLE)
        )
        message += message_body
        if not reply_to and not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
            message += NO_REPLY_NOTE
        message += get_email_footer(request, settings_link)
        ret += send_mail(
            subject, message, recp_addr, request, reply_to, cc, bcc
        )
    return ret
