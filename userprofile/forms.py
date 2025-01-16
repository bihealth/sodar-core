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
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']


class UserAppSettingsForm(SODARForm):
    """Form for configuring user settings"""

    def _set_app_setting_field(self, plugin_name, s_field, s_def):
        """
        Set user app setting field, widget and value.

        :param plugin_name: App plugin name
        :param s_field: Form field name
        :param s_def: PluginAppSettingDef object
        """
        s_widget_attrs = s_def.widget_attrs
        if s_def.placeholder is not None:
            s_widget_attrs['placeholder'] = s_def.placeholder
        setting_kwargs = {
            'required': False,
            'label': s_def.label or '{}.{}'.format(plugin_name, s_def.name),
            'help_text': s_def.description,
        }
        # Disable global user settings if on target site
        if (
            s_def.global_edit
            and settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
        ):
            setting_kwargs['label'] += ' ' + SETTING_DISABLE_LABEL
            setting_kwargs['help_text'] += ' ' + SETTING_SOURCE_ONLY_MSG
            setting_kwargs['disabled'] = True

        if s_def.options and callable(s_def.options):
            self.fields[s_field] = forms.ChoiceField(
                choices=[
                    (
                        (str(value[0]), str(value[1]))
                        if isinstance(value, tuple)
                        else (str(value), str(value))
                    )
                    for value in s_def.options(user=self.user)
                ],
                **setting_kwargs,
            )
        elif s_def.options:
            self.fields[s_field] = forms.ChoiceField(
                choices=[
                    (
                        (int(option), int(option))
                        if s_def.type == APP_SETTING_TYPE_INTEGER
                        else (option, option)
                    )
                    for option in s_def.options
                ],
                **setting_kwargs,
            )
        elif s_def.type == APP_SETTING_TYPE_STRING:
            self.fields[s_field] = forms.CharField(
                widget=forms.TextInput(attrs=s_widget_attrs),
                **setting_kwargs,
            )
        elif s_def.type == APP_SETTING_TYPE_INTEGER:
            self.fields[s_field] = forms.IntegerField(
                widget=forms.NumberInput(attrs=s_widget_attrs),
                **setting_kwargs,
            )
        elif s_def.type == APP_SETTING_TYPE_BOOLEAN:
            self.fields[s_field] = forms.BooleanField(**setting_kwargs)
        elif s_def.type == APP_SETTING_TYPE_JSON:
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
            plugin_name=plugin_name, setting_name=s_def.name, user=self.user
        )
        if s_def.type == APP_SETTING_TYPE_JSON:
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
                plugin_name = plugin.name
                s_defs = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER, plugin=plugin, user_modifiable=True
                )
            else:
                plugin_name = 'projectroles'
                s_defs = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER,
                    plugin_name=plugin_name,
                    user_modifiable=True,
                )
            for s_def in s_defs.values():
                s_field = 'settings.{}.{}'.format(plugin_name, s_def.name)
                self._set_app_setting_field(plugin_name, s_field, s_def)
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
            s_defs = app_settings.get_definitions(
                APP_SETTING_SCOPE_USER, **p_kwargs
            )
            p_settings = {}

            for s_def in s_defs.values():
                s_field = '.'.join(['settings', p_name, s_def.name])
                p_settings[s_def.name] = self.cleaned_data.get(s_field)

                if s_def.type == APP_SETTING_TYPE_JSON:
                    if not self.cleaned_data.get(s_field):
                        self.cleaned_data[s_field] = '{}'
                    try:
                        self.cleaned_data[s_field] = json.loads(
                            self.cleaned_data.get(s_field)
                        )
                    except json.JSONDecodeError as err:
                        self.add_error(s_field, 'Invalid JSON\n' + str(err))
                elif s_def.type == APP_SETTING_TYPE_INTEGER:
                    # Convert integers from select fields
                    self.cleaned_data[s_field] = int(self.cleaned_data[s_field])

                if not app_settings.validate(
                    setting_type=s_def.type,
                    setting_value=self.cleaned_data.get(s_field),
                    setting_options=s_def.options,
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
