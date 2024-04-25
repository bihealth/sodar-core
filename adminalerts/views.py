"""UI views for the adminalerts app"""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import (
    DetailView,
    UpdateView,
    CreateView,
    DeleteView,
    ListView,
)
from django.views.generic.edit import ModelFormMixin

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.email import get_email_user, get_user_addr, send_generic_mail
from projectroles.views import (
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
)

from adminalerts.forms import AdminAlertForm
from adminalerts.models import AdminAlert


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
User = get_user_model()


# Local constants
APP_NAME = 'adminalerts'
DEFAULT_PAGINATION = 15
EMAIL_SUBJECT = '{state} admin alert: {message}'
EMAIL_BODY = r'''
An admin alert has been {action}d by {issuer}:

{message}
'''.lstrip()
EMAIL_BODY_DESCRIPTION = r'''
Additional details:
----------------------------------------
{description}
----------------------------------------
'''


# Listing/details views --------------------------------------------------------


class AdminAlertListView(LoggedInPermissionMixin, ListView):
    """Alert list view"""

    permission_required = 'adminalerts.create_alert'
    template_name = 'adminalerts/alert_list.html'
    model = AdminAlert
    paginate_by = getattr(
        settings, 'ADMINALERTS_PAGINATION', DEFAULT_PAGINATION
    )
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'

    def get_queryset(self):
        return AdminAlert.objects.all().order_by('-pk')


class AdminAlertDetailView(
    LoggedInPermissionMixin, HTTPRefererMixin, DetailView
):
    """Alert detail view"""

    permission_required = 'adminalerts.view_alert'
    template_name = 'adminalerts/alert_detail.html'
    model = AdminAlert
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'


# Modification views -----------------------------------------------------------


class AdminAlertModifyMixin(ModelFormMixin):
    """Common modification methods for AdminAlert create/update views"""

    @classmethod
    def _get_email_recipients(cls, alert):
        """
        Return list of email addresses for alert email recipients, excluding the
        alert issuer.
        """
        ret = []
        users = User.objects.exclude(sodar_uuid=alert.user.sodar_uuid).order_by(
            'email'
        )
        for u in users:
            if not app_settings.get(APP_NAME, 'notify_email_alert', user=u):
                continue
            if not u.email:
                logger.warning('No email set for user: {}'.format(u.username))
                continue
            user_emails = get_user_addr(u)
            ret += [e for e in user_emails if e not in ret]
        return ret

    def _send_email(self, alert, action):
        """
        Send email alerts to all users except for the alert issuer.

        :param alert: AdminAlert object
        :param action: "create" or "update" (string)
        """
        subject = EMAIL_SUBJECT.format(
            state='New' if action == 'create' else 'Updated',
            message=alert.message,
        )
        body = EMAIL_BODY.format(
            action=action,
            issuer=get_email_user(alert.user),
            message=alert.message,
        )
        if alert.description:
            body += EMAIL_BODY_DESCRIPTION.format(
                description=alert.description.raw
            )
        recipients = self._get_email_recipients(alert)
        # NOTE: Recipients go under bcc
        # NOTE: If we have no recipients in bcc we cancel sending
        if len(recipients) == 0:
            return 0
        return send_generic_mail(
            subject,
            body,
            [settings.EMAIL_SENDER],
            self.request,
            reply_to=None,
            bcc=recipients,
        )

    def form_valid(self, form):
        form_action = 'update' if self.object else 'create'
        self.object = form.save()
        email_count = 0
        email_msg_suffix = ''
        if (
            form.cleaned_data['send_email']
            and self.object.active
            and settings.PROJECTROLES_SEND_EMAIL
        ):
            email_count = self._send_email(form.instance, form_action)
        if email_count > 0:
            email_msg_suffix = ', {} email{} sent'.format(
                email_count, 's' if email_count != 1 else ''
            )
        messages.success(
            self.request, 'Alert {}d{}.'.format(form_action, email_msg_suffix)
        )
        return redirect(reverse('adminalerts:list'))


class AdminAlertCreateView(
    LoggedInPermissionMixin,
    AdminAlertModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    CreateView,
):
    """AdminAlert creation view"""

    model = AdminAlert
    form_class = AdminAlertForm
    permission_required = 'adminalerts.create_alert'


class AdminAlertUpdateView(
    LoggedInPermissionMixin,
    AdminAlertModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    UpdateView,
):
    """AdminAlert updating view"""

    model = AdminAlert
    form_class = AdminAlertForm
    permission_required = 'adminalerts.update_alert'
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'


class AdminAlertDeleteView(
    LoggedInPermissionMixin, HTTPRefererMixin, DeleteView
):
    """AdminAlert deletion view"""

    model = AdminAlert
    permission_required = 'adminalerts.update_alert'
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'

    def get_success_url(self):
        """Override for redirecting alert list view with message"""
        messages.success(self.request, 'Alert deleted.')
        return reverse('adminalerts:list')
