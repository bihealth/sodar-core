"""Forms for the userprofile app"""

from typing import Optional

from django import forms

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import (
    SODARForm,
    SODARModelForm,
    SODARAppSettingFormMixin,
)
from projectroles.models import (
    SODARUser,
    SODARUserAdditionalEmail,
    SODAR_CONSTANTS,
    ADD_EMAIL_ALREADY_SET_MSG,
)
from projectroles.plugins import PluginAPI
from projectroles.utils import build_secret


app_settings = AppSettingAPI()
plugin_api = PluginAPI()


# SODAR Constants
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']


class UserAppSettingsForm(SODARAppSettingFormMixin, SODARForm):
    """Form for configuring user settings"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)
        # Init app settings fields
        project_plugins = plugin_api.get_active_plugins(
            plugin_type='project_app'
        )
        site_plugins = plugin_api.get_active_plugins(plugin_type='site_app')
        self.app_plugins = project_plugins + site_plugins
        user_mod = False if self.user.is_superuser else True
        self.init_app_settings(
            self.app_plugins, APP_SETTING_SCOPE_USER, user_mod
        )

    def clean(self):
        cleaned_data, errors = self.clean_app_settings(
            self.cleaned_data,
            self.app_plugins,
            APP_SETTING_SCOPE_USER,
            False if self.user.is_superuser else True,
            user=self.user,
        )
        self.cleaned_data = cleaned_data
        for field, error in errors:
            self.add_error(field, error)
        return self.cleaned_data


class UserEmailForm(SODARModelForm):
    """Form for creating additional email addresses for user"""

    class Meta:
        model = SODARUserAdditionalEmail
        fields = ['email', 'user', 'secret']

    def __init__(
        self, current_user: Optional[SODARUser] = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        if current_user:
            self.current_user = current_user
        self.fields['user'].widget = forms.HiddenInput()
        self.initial['user'] = current_user
        self.fields['secret'].widget = forms.HiddenInput()
        self.initial['secret'] = build_secret(32)

    def clean(self):
        if self.cleaned_data['email'] == self.current_user.email:
            self.add_error(
                'email', ADD_EMAIL_ALREADY_SET_MSG.format(email_type='primary')
            )
            return self.cleaned_data
        if (
            SODARUserAdditionalEmail.objects.filter(
                user=self.current_user, email=self.cleaned_data['email']
            ).count()
            > 0
        ):
            self.add_error(
                'email',
                ADD_EMAIL_ALREADY_SET_MSG.format(email_type='additional'),
            )
        return self.cleaned_data
