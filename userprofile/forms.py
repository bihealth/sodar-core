import json

from django import forms
from django.conf import settings

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import (
    SODARForm,
    SODARModelForm,
    SETTING_CUSTOM_VALIDATE_MSG,
    SETTING_DISABLE_LABEL,
    SETTING_SOURCE_ONLY_MSG,
)
from projectroles.models import (
    SODARUserAdditionalEmail,
    SODAR_CONSTANTS,
    ADD_EMAIL_ALREADY_SET_MSG,
)
from projectroles.plugins import get_active_plugins
from projectroles.utils import build_secret


app_settings = AppSettingAPI()


# SODAR Constants
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']


class UserSettingsForm(SODARForm):
    """Form for configuring user settings"""

    def _set_app_setting_field(self, plugin_name, s_field, s_key, s_val):
        """
        Set user app setting field, widget and value.

        :param plugin_name: App plugin name
        :param s_field: Form field name
        :param s_key: Setting key
        :param s_val: Setting value
        """
        s_widget_attrs = s_val.get('widget_attrs') or {}
        if 'placeholder' in s_val:
            s_widget_attrs['placeholder'] = s_val.get('placeholder')
        setting_kwargs = {
            'required': False,
            'label': s_val.get('label') or '{}.{}'.format(plugin_name, s_key),
            'help_text': s_val.get('description'),
        }
        # Disable global user settings if on target site
        if (
            app_settings.get_global_value(s_val)
            and settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
        ):
            setting_kwargs['label'] += ' ' + SETTING_DISABLE_LABEL
            setting_kwargs['help_text'] += ' ' + SETTING_SOURCE_ONLY_MSG
            setting_kwargs['disabled'] = True

        if s_val.get('options') and callable(s_val['options']):
            self.fields[s_field] = forms.ChoiceField(
                choices=[
                    (
                        (str(value[0]), str(value[1]))
                        if isinstance(value, tuple)
                        else (str(value), str(value))
                    )
                    for value in s_val['options'](user=self.user)
                ],
                **setting_kwargs,
            )
        elif s_val.get('options'):
            self.fields[s_field] = forms.ChoiceField(
                choices=[
                    (
                        (int(option), int(option))
                        if s_val['type'] == 'INTEGER'
                        else (option, option)
                    )
                    for option in s_val['options']
                ],
                **setting_kwargs,
            )
        elif s_val['type'] == 'STRING':
            self.fields[s_field] = forms.CharField(
                widget=forms.TextInput(attrs=s_widget_attrs),
                **setting_kwargs,
            )
        elif s_val['type'] == 'INTEGER':
            self.fields[s_field] = forms.IntegerField(
                widget=forms.NumberInput(attrs=s_widget_attrs),
                **setting_kwargs,
            )
        elif s_val['type'] == 'BOOLEAN':
            self.fields[s_field] = forms.BooleanField(**setting_kwargs)
        elif s_val['type'] == 'JSON':
            # NOTE: Attrs MUST be supplied here (#404)
            if 'class' in s_widget_attrs:
                s_widget_attrs['class'] += ' sodar-json-input'
            else:
                s_widget_attrs['class'] = 'sodar-json-input'
            self.fields[s_field] = forms.CharField(
                widget=forms.Textarea(attrs=s_widget_attrs),
                **setting_kwargs,
            )

        # Modify initial value and attributes
        self.fields[s_field].widget.attrs.update(s_widget_attrs)
        value = app_settings.get(
            plugin_name=plugin_name, setting_name=s_key, user=self.user
        )
        if s_val['type'] == 'JSON':
            value = json.dumps(value)
        self.initial[s_field] = value

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)
        # Add settings fields
        self.app_plugins = get_active_plugins(plugin_type='project_app')
        self.user_plugins = get_active_plugins(plugin_type='site_app')
        self.app_plugins = self.app_plugins + self.user_plugins

        for plugin in self.app_plugins + [None]:
            if plugin:
                name = plugin.name
                p_defs = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER, plugin=plugin, user_modifiable=True
                )
            else:
                name = 'projectroles'
                p_defs = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER,
                    plugin_name=name,
                    user_modifiable=True,
                )
            for s_key, s_val in p_defs.items():
                s_field = 'settings.{}.{}'.format(name, s_key)
                self._set_app_setting_field(name, s_field, s_key, s_val)
                self.fields[s_field].label = self.get_app_setting_label(
                    plugin, self.fields[s_field].label
                )

    def clean(self):
        """Function for custom form validation and cleanup"""
        for plugin in self.app_plugins + [None]:
            p_kwargs = {'user_modifiable': True}
            if plugin:
                p_name = plugin.name
                p_kwargs['plugin'] = plugin
            else:
                p_name = 'projectroles'
                p_kwargs['plugin_name'] = p_name
            p_defs = app_settings.get_definitions(
                APP_SETTING_SCOPE_USER, **p_kwargs
            )
            p_settings = {}

            for s_key, s_val in p_defs.items():
                s_field = '.'.join(['settings', p_name, s_key])
                p_settings[s_key] = self.cleaned_data.get(s_field)

                if s_val['type'] == 'JSON':
                    if not self.cleaned_data.get(s_field):
                        self.cleaned_data[s_field] = '{}'
                    try:
                        self.cleaned_data[s_field] = json.loads(
                            self.cleaned_data.get(s_field)
                        )
                    except json.JSONDecodeError as err:
                        self.add_error(s_field, 'Invalid JSON\n' + str(err))
                elif s_val['type'] == 'INTEGER':
                    # Convert integers from select fields
                    self.cleaned_data[s_field] = int(self.cleaned_data[s_field])

                if not app_settings.validate(
                    setting_type=s_val['type'],
                    setting_value=self.cleaned_data.get(s_field),
                    setting_options=s_val.get('options'),
                    user=self.user,
                ):
                    self.add_error(s_field, 'Invalid value')

            # Custom plugin validation for app settings
            if plugin and hasattr(plugin, 'validate_form_app_settings'):
                try:
                    p_errors = plugin.validate_form_app_settings(
                        p_settings, user=self.user
                    )
                    if p_errors:
                        for field, error in p_errors.items():
                            f_name = '.'.join(['settings', p_name, field])
                            self.add_error(f_name, error)
                except Exception as ex:
                    self.add_error(
                        None,
                        SETTING_CUSTOM_VALIDATE_MSG.format(
                            plugin=p_name, exception=ex
                        ),
                    )
        return self.cleaned_data


class UserEmailForm(SODARModelForm):
    """Form for creating additional email addresses for user"""

    class Meta:
        model = SODARUserAdditionalEmail
        fields = ['email', 'user', 'secret']

    def __init__(self, current_user=None, *args, **kwargs):
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
