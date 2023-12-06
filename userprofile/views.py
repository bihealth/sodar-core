"""UI views for the userprofile app"""

from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins
from projectroles.views import (
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    InvalidFormMixin,
)

from userprofile.forms import UserSettingsForm


User = auth.get_user_model()
app_settings = AppSettingAPI()


# SODAR Constants
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local Constants
SETTING_UPDATE_MSG = 'User settings updated.'


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
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER, plugin=plugin, user_modifiable=True
                )
            else:
                name = 'projectroles'
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER, app_name=name, user_modifiable=True
                )
            for k, v in p_settings.items():
                yield {
                    'label': v.get('label') or '{}.{}'.format(name, k),
                    'value': app_settings.get(name, k, user=self.request.user),
                    'description': v.get('description'),
                }

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        result['user_settings'] = list(self._get_user_settings())
        result['local_user'] = self.request.user.is_local()
        return result


class UserSettingsView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    InvalidFormMixin,
    FormView,
):
    """User settings update view"""

    form_class = UserSettingsForm
    permission_required = 'userprofile.view_detail'
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
                _, app_name, setting_name = k.split('.', 3)
                # TODO: Omit global USER settings (#1329)
                app_settings.set(
                    app_name, setting_name, v, user=self.request.user
                )
        messages.success(self.request, SETTING_UPDATE_MSG)
        return result
