"""UI views for the userprofile app"""

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    TemplateView,
    FormView,
    CreateView,
    DeleteView,
    View,
)

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.email import send_generic_mail, get_email_user
from projectroles.models import SODARUserAdditionalEmail, SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins, get_backend_api
from projectroles.views import (
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    InvalidFormMixin,
    CurrentUserFormMixin,
)

from userprofile.forms import UserAppSettingsForm, UserEmailForm


User = auth.get_user_model()
app_settings = AppSettingAPI()


# SODAR Constants
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local Constants
APP_NAME = 'userprofile'
SETTING_UPDATE_MSG = 'User settings updated.'
VERIFY_EMAIL_SUBJECT = 'Verify your additional email address for {site}'
VERIFY_EMAIL_BODY = r'''
{user} has added this address to their
additional emails on {site}.

Once verified, the site may use this email to send automated email for
notifications as configured in user settings.

Please verify this email address by following this URL:
{url}

If this was not requested by you, this message can be ignored.
'''.lstrip()
EMAIL_NOT_FOUND_MSG = 'No email found.'
EMAIL_ALREADY_VERIFIED_MSG = 'Email already verified.'
EMAIL_VERIFIED_MSG = 'Email "{email}" verified.'
EMAIL_VERIFY_RESEND_MSG = 'Verification message to "{email}" resent.'


class UserDetailView(LoginRequiredMixin, LoggedInPermissionMixin, TemplateView):
    """Display the user profile view including the user settings"""

    template_name = 'userprofile/detail.html'
    permission_required = 'userprofile.view_detail'

    def _get_user_settings(self):
        plugins = get_active_plugins(
            plugin_type='project_app'
        ) + get_active_plugins(plugin_type='site_app')
        for plugin in plugins + [None]:
            if plugin:
                name = plugin.name
                s_defs = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER, plugin=plugin, user_modifiable=True
                )
            else:
                name = 'projectroles'
                s_defs = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER,
                    plugin_name=name,
                    user_modifiable=True,
                )
            for s_def in s_defs.values():
                yield {
                    'label': s_def.label or '{}.{}'.format(name, s_def.name),
                    'value': app_settings.get(
                        name, s_def.name, user=self.request.user
                    ),
                    'description': s_def.description,
                }

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['user_settings'] = list(self._get_user_settings())
        result['add_emails'] = SODARUserAdditionalEmail.objects.filter(
            user=self.request.user
        ).order_by('email')
        return result


class UserAppSettingsView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    InvalidFormMixin,
    FormView,
):
    """User app settings form view"""

    form_class = UserAppSettingsForm
    permission_required = 'userprofile.update_settings'
    template_name = 'userprofile/settings_form.html'
    success_url = reverse_lazy('userprofile:detail')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        result = super().form_valid(form)
        for k, v in form.cleaned_data.items():
            if k.startswith('settings.'):
                _, plugin_name, setting_name = k.split('.', 3)
                # TODO: Omit global USER settings (#1329)
                app_settings.set(
                    plugin_name, setting_name, v, user=self.request.user
                )
        messages.success(self.request, SETTING_UPDATE_MSG)
        return result


class UserEmailMixin:
    """Mixin for user email helpers"""

    def send_verify_email(self, email, resend=False):
        """
        Send verification message to additional email address.

        :param email: SODARUserAdditionalEmail object
        """
        subject = VERIFY_EMAIL_SUBJECT.format(site=settings.SITE_INSTANCE_TITLE)
        body = VERIFY_EMAIL_BODY.format(
            user=get_email_user(email.user),
            site=settings.SITE_INSTANCE_TITLE,
            url=self.request.build_absolute_uri(
                reverse(
                    'userprofile:email_verify', kwargs={'secret': email.secret}
                )
            ),
        )
        try:
            send_generic_mail(subject, body, [email.email], self.request)
            if resend:
                messages.success(
                    self.request,
                    EMAIL_VERIFY_RESEND_MSG.format(email=email.email),
                )
            else:
                messages.success(
                    self.request,
                    'Email added. A verification message has been sent to the '
                    'address. Follow the received verification link to '
                    'activate the address.',
                )
        except Exception as ex:
            messages.error(
                self.request, 'Failed to send verification mail: {}'.format(ex)
            )


class UserEmailCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    CurrentUserFormMixin,
    UserEmailMixin,
    CreateView,
):
    """User additional email creation view"""

    form_class = UserEmailForm
    permission_required = 'userprofile.create_email'
    template_name = 'userprofile/email_form.html'

    def get_success_url(self):
        timeline = get_backend_api('timeline_backend')
        self.send_verify_email(self.object)
        if timeline:
            timeline.add_event(
                project=None,
                app_name=APP_NAME,
                user=self.request.user,
                event_name='email_create',
                description='create additional email "{}"'.format(
                    self.object.email
                ),
                classified=True,
                status_type=timeline.TL_STATUS_OK,
            )
        return reverse('userprofile:detail')

    def get(self, *args, **kwargs):
        if not settings.PROJECTROLES_SEND_EMAIL:
            messages.warning(
                self.request,
                'Email sending disabled, adding email addresses is not '
                'allowed.',
            )
            return redirect(reverse('userprofile:detail'))
        return super().get(*args, **kwargs)


class UserEmailVerifyView(LoginRequiredMixin, LoggedInPermissionMixin, View):
    """View for verifying a created additional email address"""

    http_method_names = ['get']
    permission_required = 'userprofile.create_email'

    def get(self, request, *args, **kwargs):
        secret = self.kwargs.get('secret')
        email = SODARUserAdditionalEmail.objects.filter(
            user=request.user, secret=secret
        ).first()
        if not email:
            messages.error(request, EMAIL_NOT_FOUND_MSG)
        elif email.verified:
            messages.info(request, EMAIL_ALREADY_VERIFIED_MSG)
        else:
            email.verified = True
            email.save()
            messages.success(
                request, EMAIL_VERIFIED_MSG.format(email=email.email)
            )
        return redirect(reverse('userprofile:detail'))


class UserEmailVerifyResendView(
    LoginRequiredMixin, LoggedInPermissionMixin, UserEmailMixin, View
):
    """View for resending additional email verification message"""

    http_method_names = ['get']
    permission_required = 'userprofile.create_email'

    def get(self, request, *args, **kwargs):
        email_uuid = self.kwargs.get('sodaruseradditionalemail')
        email = SODARUserAdditionalEmail.objects.filter(
            user=request.user, sodar_uuid=email_uuid
        ).first()
        if not email:
            messages.error(request, EMAIL_NOT_FOUND_MSG)
        elif email.verified:
            messages.info(request, EMAIL_ALREADY_VERIFIED_MSG)
        else:
            self.send_verify_email(email, resend=True)
        return redirect(reverse('userprofile:detail'))


class UserEmailDeleteView(
    LoginRequiredMixin, LoggedInPermissionMixin, DeleteView
):
    """View for deleting additional email"""

    model = SODARUserAdditionalEmail
    permission_required = 'userprofile.delete_email'
    slug_url_kwarg = 'sodaruseradditionalemail'
    slug_field = 'sodar_uuid'
    template_name = 'userprofile/email_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, 'Email address deleted.')
        return reverse('userprofile:detail')
