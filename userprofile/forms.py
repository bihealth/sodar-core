import json

from django import forms

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import SODARForm, SETTING_CUSTOM_VALIDATE_ERROR
from projectroles.models import APP_SETTING_VAL_MAXLENGTH, SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins


app_settings = AppSettingAPI()


# SODAR Constants
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']


# User Settings Form -----------------------------------------------------------


class UserSettingsForm(SODARForm):
    """The form for configuring user settings."""

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
                    APP_SETTING_SCOPE_USER, app_name=name, user_modifiable=True
                )

            for s_key, s_val in p_defs.items():
                s_field = 'settings.{}.{}'.format(name, s_key)
                s_widget_attrs = s_val.get('widget_attrs') or {}
                if 'placeholder' in s_val:
                    s_widget_attrs['placeholder'] = s_val.get('placeholder')
                setting_kwargs = {
                    'required': False,
                    'label': s_val.get('label') or '{}.{}'.format(name, s_key),
                    'help_text': s_val.get('description'),
                }

                if s_val['type'] == 'STRING':
                    if 'options' in s_val:
                        if callable(s_val['options']):
                            self.fields[s_field] = forms.ChoiceField(
                                choices=[
                                    (str(value[0]), str(value[1]))
                                    if isinstance(value, tuple)
                                    else (str(value), str(value))
                                    for value in s_val['options'](
                                        user=self.user
                                    )
                                ],
                                **setting_kwargs,
                            )
                        else:
                            self.fields[s_field] = forms.ChoiceField(
                                choices=[
                                    (option, option)
                                    for option in s_val['options']
                                ],
                                **setting_kwargs,
                            )
                    else:
                        self.fields[s_field] = forms.CharField(
                            max_length=APP_SETTING_VAL_MAXLENGTH,
                            widget=forms.TextInput(attrs=s_widget_attrs),
                            **setting_kwargs,
                        )
                elif s_val['type'] == 'INTEGER':
                    if 'options' in s_val:
                        self.fields[s_field] = forms.ChoiceField(
                            choices=[
                                (int(option), int(option))
                                for option in s_val['options']
                            ],
                            **setting_kwargs,
                        )
                    else:
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
                if s_val['type'] != 'JSON':
                    # Add optional attributes from plugin (#404)
                    # NOTE: Experimental! Use at your own risk!
                    self.fields[s_field].widget.attrs.update(s_widget_attrs)

                    self.initial[s_field] = app_settings.get(
                        app_name=name, setting_name=s_key, user=self.user
                    )
                else:
                    self.initial[s_field] = json.dumps(
                        app_settings.get(
                            app_name=name,
                            setting_name=s_key,
                            user=self.user,
                        )
                    )
                self.fields[s_field].label = self.get_app_setting_label(
                    plugin, self.fields[s_field].label
                )
                # TODO: Disable editing global USER settings (#1329)

    def clean(self):
        """Function for custom form validation and cleanup"""
        for plugin in self.app_plugins + [None]:
            p_kwargs = {'user_modifiable': True}
            if plugin:
                p_name = plugin.name
                p_kwargs['plugin'] = plugin
            else:
                p_name = 'projectroles'
                p_kwargs['app_name'] = p_name
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
                        SETTING_CUSTOM_VALIDATE_ERROR.format(
                            plugin=p_name, exception=ex
                        ),
                    )
        return self.cleaned_data
