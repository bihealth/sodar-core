import json

from django import forms

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import SODARForm
from projectroles.models import APP_SETTING_VAL_MAXLENGTH, SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins


# SODAR Constants
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']


# App settings API
app_settings = AppSettingAPI()


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
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER, plugin=plugin, user_modifiable=True
                )
            else:
                name = 'projectroles'
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_USER, app_name=name, user_modifiable=True
                )

            for s_key, s_val in p_settings.items():
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

    def clean(self):
        """Function for custom form validation and cleanup"""
        for plugin in self.app_plugins + [None]:
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
            plugin_app_settings = {}

            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(name, s_key)
                plugin_app_settings[s_key] = self.cleaned_data.get(s_field)

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
                    # When field is a select/dropdown, the information of the
                    # data type gets lost. We need to convert that here,
                    # otherwise subsequent checks will fail.
                    self.cleaned_data[s_field] = int(self.cleaned_data[s_field])

                if not app_settings.validate(
                    setting_type=s_val['type'],
                    setting_value=self.cleaned_data.get(s_field),
                    setting_options=s_val.get('options'),
                    user=self.user,
                ):
                    self.add_error(s_field, 'Invalid value')
            try:
                app_settings_errors = plugin.validate_form_app_settings(
                    plugin_app_settings, user=self.user
                )
                if app_settings_errors:
                    for field, error in app_settings_errors.items():
                        if error:
                            self.add_error(field, error)
            except AttributeError:
                # Plugin does not have a validate_form_app_settings method
                pass

        return self.cleaned_data
