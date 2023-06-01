"""Forms for the projectroles app"""

import json
import logging

from django import forms
from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from dal import autocomplete, forward as dal_forward
from pagedown.widgets import PagedownWidget


from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    SODAR_CONSTANTS,
    ROLE_RANKING,
    APP_SETTING_VAL_MAXLENGTH,
    CAT_DELIMITER,
    CAT_DELIMITER_ERROR_MSG,
)

from projectroles.plugins import get_active_plugins
from projectroles.utils import (
    get_display_name,
    get_user_display_name,
    build_secret,
)
from projectroles.app_settings import AppSettingAPI, APP_SETTING_LOCAL_DEFAULT


User = auth.get_user_model()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']

# Local constants
APP_NAME = 'projectroles'
EMPTY_CHOICE_LABEL = '--------'
PROJECT_TYPE_CHOICES = [
    (None, EMPTY_CHOICE_LABEL),
    (
        PROJECT_TYPE_CATEGORY,
        get_display_name(PROJECT_TYPE_CATEGORY, title=True),
    ),
    (PROJECT_TYPE_PROJECT, get_display_name(PROJECT_TYPE_PROJECT, title=True)),
]


# Base Classes and Mixins ------------------------------------------------------


class SODARFormMixin:
    """General mixin for SODAR form setup and helpers"""

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super().__init__(*args, **kwargs)

    def add_error(self, field, error):
        """
        Add error to form along with error logging.

        :param field: Name of field (string)
        :param error: Error message(s) (list)
        """
        if isinstance(error, ValidationError):
            log_err = ';'.join(error.messages)
        else:
            log_err = error
        log_msg = 'Field "{}": {}'.format(field, log_err)
        if hasattr(self, 'current_user') and self.current_user:
            log_msg += ' (user={})'.format(self.current_user.username)
        self.logger.error(log_msg)
        super().add_error(field, error)  # Call the error method in Django forms

    def get_app_setting_label(self, plugin, label):
        """Return label for app setting key"""
        if plugin:
            return format_html(
                '{} <i class="iconify text-info" title="{}" data-icon="{}">'
                '</i>',
                label,
                plugin.title,
                plugin.icon,
            )
        return format_html(
            '{} <i class="iconify text-info" title="projectroles" '
            'data-icon="mdi-cube"></i>',
            label,
        )


class SODARForm(SODARFormMixin, forms.Form):
    """Override of Django base form with SODAR Core specific helpers."""


class SODARModelForm(SODARFormMixin, forms.ModelForm):
    """Override of Django model form with SODAR Core specific helpers."""


class SODARPagedownWidget(PagedownWidget):
    class Media:
        css = {'all': ['projectroles/css/pagedown.css']}


# User autocompletion ----------------------------------------------------------


class SODARUserAutocompleteWidget(autocomplete.ModelSelect2):
    """
    Custom Select widget for user field autocompletion which uses the SODAR
    User class sodar_uuid instead of pk.
    """

    # Override function to use sodar_uuid instead of pk
    def filter_choices_to_render(self, selected_choices):
        """Filter out un-selected choices if choices is a QuerySet."""
        self.choices.queryset = self.choices.queryset.filter(
            sodar_uuid__in=[c for c in selected_choices if c]
        )


class SODARUserRedirectWidget(SODARUserAutocompleteWidget):
    """Version of SODARUserAutocompleteWidget to allow redirect on selection"""

    autocomplete_function = 'autocomplete_redirect'


# TODO: Refactor into widget?
def get_user_widget(
    scope='all',
    project=None,
    exclude=None,
    forward=None,
    url=None,
    widget_class=None,
):
    """
    Get an user autocomplete widget for your form.

    :param scope: Scope of users to include: "all"/"project"/"project_exclude"
    :param project: Project object or project UUID string (optional)
    :param exclude: List of User objects or User UUIDs to exclude
    :param forward: Parameters to forward to autocomplete view (optional)
    :param url: Autocomplete ajax class override (optional)
    :param widget_class: Widget class override (optional)
    :return: SODARUserAutocompleteWidget or an overridden widget class
    """
    url = url or 'projectroles:ajax_autocomplete_user'
    wg = {'url': url, 'forward': [dal_forward.Const(scope, 'scope')]}

    if project:
        p_uuid = (
            str(project.sodar_uuid)
            if isinstance(project, Project)
            else str(project)
        )
        wg['forward'].append(dal_forward.Const(p_uuid, 'project'))
    if forward and isinstance(forward, list):
        wg['forward'] += forward
    if exclude:
        wg['forward'].append(
            dal_forward.Const(
                [
                    str(u.sodar_uuid) if isinstance(u, User) else u
                    for u in exclude
                ],
                'exclude',
            )
        )
    if widget_class:
        return widget_class(**wg)
    return SODARUserAutocompleteWidget(**wg)


class SODARUserChoiceField(forms.ModelChoiceField):
    """User choice field to be used with SODAR User objects and autocomplete"""

    def __init__(
        self,
        scope='all',
        project=None,
        exclude=None,
        forward=None,
        url=None,
        widget_class=None,
        *args,
        **kwargs
    ):
        """
        Override of ModelChoiceField initialization.

        Most arguments given to ModelChoiceField can be set, with the exception
        of queryset, to_field_name, limit_choices_to and widget.

        :param scope: Scope of users to include:
                      "all"/"project"/"project_exclude"
        :param project: Project object or project UUID string (optional)
        :param exclude: List of User objects or User UUIDs to exclude
        :param forward: Parameters to forward to autocomplete view (optional)
        :param url: Autocomplete ajax class override (optional)
        :param widget_class: Widget class override (optional)
        """
        widget = get_user_widget(
            scope, project, exclude, forward, url, widget_class
        )
        super().__init__(
            User.objects.all(),
            to_field_name='sodar_uuid',
            limit_choices_to=None,
            widget=widget,
            *args,
            **kwargs
        )


# Project form -----------------------------------------------------------------


class ProjectForm(SODARModelForm):
    """Form for Project creation/updating"""

    # Set up owner field
    owner = SODARUserChoiceField(label='Owner', help_text='Owner')

    class Meta:
        model = Project
        fields = [
            'title',
            'type',
            'parent',
            'owner',
            'description',
            'readme',
            'public_guest_access',
        ]

    @classmethod
    def _get_parent_choices(cls, instance, user):
        """
        Return valid choices of parent categories for moving a project.

        :param instance: Project instance being updated
        :param user: Request user
        :return: List of tuples
        """
        ret = []
        # Add empty choice (root) in cases where valid
        if (
            user.is_superuser
            or not instance.parent
            or (
                instance.type == PROJECT_TYPE_PROJECT
                and getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False)
            )
        ):
            ret.append((None, EMPTY_CHOICE_LABEL))

        categories = Project.objects.filter(type=PROJECT_TYPE_CATEGORY).exclude(
            pk=instance.pk
        )
        if not user.is_superuser:
            categories = categories.filter(
                local_roles__in=RoleAssignment.objects.filter(
                    user=user,
                    role__name__in=[
                        PROJECT_ROLE_OWNER,
                        PROJECT_ROLE_DELEGATE,
                        PROJECT_ROLE_CONTRIBUTOR,
                    ],
                )
            )
            # Add categories with inherited ownership
            role_owner = Role.objects.filter(name=PROJECT_ROLE_OWNER).first()
            owned_cats = [
                r.project.full_title + CAT_DELIMITER
                for r in RoleAssignment.objects.filter(
                    project__type=PROJECT_TYPE_CATEGORY,
                    user=user,
                    role=role_owner,
                )
            ]
            other_categories = Project.objects.filter(
                type=PROJECT_TYPE_CATEGORY
            ).exclude(pk__in=categories)
            categories = list(categories)
            for c in other_categories:
                if any(c.full_title.startswith(t) for t in owned_cats):
                    categories.append(c)

        # If instance is category, exclude children
        if instance.type == PROJECT_TYPE_CATEGORY:
            categories = [
                c
                for c in categories
                if (
                    c.parent != instance
                    and c not in instance.get_children(flat=True)
                )
            ]

        # FIX for #558: Ensure current parent is in choices
        if (
            categories
            and not user.is_superuser
            and instance.parent
            and instance.parent not in categories
        ):
            categories.append(instance.parent)

        ret += [(c.sodar_uuid, c.full_title) for c in categories]
        return sorted(ret, key=lambda x: x[1])

    def _set_app_setting_widget(self, app_name, s_field, s_key, s_val):
        """
        Internal helper for setting app setting widget and value.

        :param app_name: App name
        :param s_field: Form field name
        :param s_key: Setting key
        :param s_val: Setting value
        """
        s_widget_attrs = s_val.get('widget_attrs') or {}

        # Set project type
        s_project_types = s_val.get('project_types') or [PROJECT_TYPE_PROJECT]
        s_widget_attrs['data-project-types'] = ','.join(s_project_types).lower()

        if 'placeholder' in s_val:
            s_widget_attrs['placeholder'] = s_val.get('placeholder')
        setting_kwargs = {
            'required': False,
            'label': s_val.get('label') or '{}.{}'.format(app_name, s_key),
            'help_text': s_val['description'],
        }
        if s_val['type'] == 'JSON':
            # NOTE: Attrs MUST be supplied here (#404)
            if 'class' in s_widget_attrs:
                s_widget_attrs['class'] += ' sodar-json-input'
            else:
                s_widget_attrs['class'] = 'sodar-json-input'
            self.fields[s_field] = forms.CharField(
                widget=forms.Textarea(attrs=s_widget_attrs), **setting_kwargs
            )
            if self.instance.pk:
                json_data = self.app_settings.get(
                    app_name=app_name,
                    setting_name=s_key,
                    project=self.instance,
                )
            else:
                json_data = self.app_settings.get_default(
                    app_name=app_name,
                    setting_name=s_key,
                    project=None,
                )
            self.initial[s_field] = json.dumps(json_data)
        else:
            if s_val.get('options'):
                if callable(s_val['options']) and self.instance.pk:
                    values = s_val['options'](project=self.instance)
                    self.fields[s_field] = forms.ChoiceField(
                        choices=[
                            (str(value[0]), str(value[1]))
                            if isinstance(value, tuple)
                            else (str(value), str(value))
                            for value in values
                        ],
                        **setting_kwargs
                    )
                elif callable(s_val['options']) and not self.instance.pk:
                    values = s_val['options'](project=None)
                    self.fields[s_field] = forms.ChoiceField(
                        choices=[
                            (str(value[0]), str(value[1]))
                            if isinstance(value, tuple)
                            else (str(value), str(value))
                            for value in values
                        ],
                        **setting_kwargs
                    )
                else:
                    self.fields[s_field] = forms.ChoiceField(
                        choices=[
                            (int(option), int(option))
                            if s_val['type'] == 'INTEGER'
                            else (option, option)
                            for option in s_val['options']
                        ],
                        **setting_kwargs
                    )
            elif s_val['type'] == 'STRING':
                self.fields[s_field] = forms.CharField(
                    max_length=APP_SETTING_VAL_MAXLENGTH,
                    widget=forms.TextInput(attrs=s_widget_attrs),
                    **setting_kwargs
                )
            elif s_val['type'] == 'INTEGER':
                self.fields[s_field] = forms.IntegerField(
                    widget=forms.NumberInput(attrs=s_widget_attrs),
                    **setting_kwargs
                )
            elif s_val['type'] == 'BOOLEAN':
                self.fields[s_field] = forms.BooleanField(**setting_kwargs)

            # Add optional attributes from plugin (#404)
            # NOTE: Experimental! Use at your own risk!
            self.fields[s_field].widget.attrs.update(s_widget_attrs)

            # Set initial value
            if self.instance.pk:
                self.initial[s_field] = self.app_settings.get(
                    app_name=app_name,
                    setting_name=s_key,
                    project=self.instance,
                )
            else:
                self.initial[s_field] = self.app_settings.get_default(
                    app_name=app_name,
                    setting_name=s_key,
                    project=None,
                )

    def _set_app_setting_notes(self, s_field, s_val, plugin):
        """
        Internal helper for setting app setting label notes.

        :param s_field: Form field name
        :param s_val: Setting value
        :param plugin: Plugin object
        """
        if s_val.get('user_modifiable') is False:
            self.fields[s_field].label += ' [HIDDEN]'
            self.fields[s_field].help_text += ' [HIDDEN FROM USERS]'
        if s_val.get('local', APP_SETTING_LOCAL_DEFAULT) is False:
            if self.instance.is_remote():
                self.fields[s_field].label += ' [DISABLED]'
                self.fields[
                    s_field
                ].help_text += ' [Only editable on source site]'
                self.fields[s_field].disabled = True
            else:
                self.fields[
                    s_field
                ].help_text += ' [Not editable on target sites]'
        self.fields[s_field].label = self.get_app_setting_label(
            plugin, self.fields[s_field].label
        )

    def _init_app_settings(self):
        # Set up setting query kwargs
        self.p_kwargs = {}
        if not self.current_user.is_superuser:
            self.p_kwargs['user_modifiable'] = True
        self.app_settings = AppSettingAPI()
        self.app_plugins = sorted(get_active_plugins(), key=lambda x: x.name)

        # plugin == 'None' refers to projectroles app
        for plugin in self.app_plugins + [None]:
            # Show non-modifiable settings to superusers
            if plugin:
                app_name = plugin.name
                p_settings = self.app_settings.get_definitions(
                    APP_SETTING_SCOPE_PROJECT, plugin=plugin, **self.p_kwargs
                )
            else:
                app_name = APP_NAME
                p_settings = self.app_settings.get_definitions(
                    APP_SETTING_SCOPE_PROJECT,
                    app_name=app_name,
                    **self.p_kwargs
                )
            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(app_name, s_key)
                # Set widget and value
                self._set_app_setting_widget(app_name, s_field, s_key, s_val)
                # Set label notes
                self._set_app_setting_notes(s_field, s_val, plugin)

    @classmethod
    def _validate_app_settings(
        self,
        cleaned_data,
        app_plugins,
        app_settings,
        p_kwargs,
        instance,
        instance_owner_as,
    ):
        """Validate and clean app_settings form fields"""
        errors = []

        for plugin in app_plugins + [None]:
            if plugin:
                name = plugin.name
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_PROJECT, app_name=name, **p_kwargs
                )
            else:
                name = 'projectroles'
                p_settings = app_settings.get_definitions(
                    APP_SETTING_SCOPE_PROJECT, app_name=name, **p_kwargs
                )

            plugin_app_settings = {}
            for s_key, s_val in p_settings.items():
                s_field = 'settings.{}.{}'.format(name, s_key)
                plugin_app_settings[s_key] = cleaned_data.get(s_field)

                if s_val['type'] == 'JSON':
                    if not plugin_app_settings[s_key]:
                        cleaned_data[s_field] = '{}'
                    try:
                        cleaned_data[s_field] = json.loads(
                            cleaned_data.get(s_field)
                        )
                    except json.JSONDecodeError as err:
                        errors.append((s_field, 'Invalid JSON\n' + str(err)))
                elif s_val['type'] == 'INTEGER':
                    # When the field is a select/dropdown the information of
                    # the datatype gets lost. We need to convert that here,
                    # otherwise subsequent checks will fail.
                    cleaned_data[s_field] = int(cleaned_data[s_field])

                if not app_settings.validate(
                    setting_type=s_val['type'],
                    setting_value=cleaned_data.get(s_field),
                    setting_options=s_val.get('options'),
                    project=instance,
                ):
                    errors.append((s_field, 'Invalid value'))

            # Custom validation for app settings
            try:
                app_settings_errors = plugin.validate_app_settings(
                    plugin_app_settings,
                    project=instance,
                    user=instance_owner_as,
                )
                if app_settings_errors:
                    for field, error in app_settings_errors.items():
                        if error:
                            errors.append((field, error))
            except AttributeError:
                # Plugin does not have a validate_form_app_settings method
                pass
        return cleaned_data, errors

    def __init__(self, project=None, current_user=None, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)
        disable_categories = getattr(
            settings, 'PROJECTROLES_DISABLE_CATEGORIES', False
        )
        # Get current user for checking permissions for form items
        if current_user:
            self.current_user = current_user
        # Add settings fields
        self._init_app_settings()
        # Access parent project if present
        parent_project = None
        if project:
            parent_project = Project.objects.filter(sodar_uuid=project).first()

        # Update help texts to match DISPLAY_NAMES
        self.fields['title'].help_text = 'Title'
        self.fields['type'].help_text = 'Type of container ({} or {})'.format(
            get_display_name(PROJECT_TYPE_CATEGORY),
            get_display_name(PROJECT_TYPE_PROJECT),
        )
        self.fields['type'].choices = PROJECT_TYPE_CHOICES
        self.fields['parent'].help_text = 'Parent {} if nested'.format(
            get_display_name(PROJECT_TYPE_CATEGORY)
        )
        self.fields['description'].help_text = 'Short description'
        self.fields['readme'].help_text = 'README (optional, supports markdown)'

        # Modify ModelChoiceFields to use sodar_uuid
        self.fields['parent'].to_field_name = 'sodar_uuid'
        # Set readme widget with preview
        self.fields['readme'].widget = SODARPagedownWidget(
            attrs={'show_preview': True}
        )

        # Updating an existing project
        if self.instance.pk:
            # Set readme value as raw markdown
            self.initial['readme'] = self.instance.readme.raw
            # Hide project type selection
            self.fields['type'].widget = forms.HiddenInput()
            # Set hidden project field for autocomplete
            self.initial['project'] = self.instance
            # Set owner value
            self.initial['owner'] = self.instance.get_owner().user.sodar_uuid
            # Hide owner widget if updating (changed in member modification UI)
            self.fields['owner'].widget = forms.HiddenInput()

            # Set valid choices for parent
            if not disable_categories:
                self.fields['parent'].choices = self._get_parent_choices(
                    self.instance, self.current_user
                )
                # Hide widget if no valid choices are available
                if len(self.fields['parent'].choices) == 0:
                    self.fields['parent'].widget = forms.HiddenInput()
                # Set initial value for parent
                if self.instance.parent:
                    self.initial['parent'] = self.instance.parent.sodar_uuid
            else:  # Categories disabled
                # Hide parent selection
                self.fields['parent'].widget = forms.HiddenInput()

        # Project creation
        else:
            # Set hidden project field for autocomplete
            self.initial['project'] = None
            # Hide parent selection
            self.fields['parent'].widget = forms.HiddenInput()

            # Set owner
            if self.current_user.is_superuser and parent_project:
                self.initial['owner'] = parent_project.get_owner().user
            else:
                self.initial['owner'] = self.current_user
            self.fields[
                'owner'
            ].label_from_instance = lambda x: x.get_form_label(email=True)
            # Hide owner select widget for regular users
            if not self.current_user.is_superuser:
                self.fields['owner'].widget = forms.HiddenInput()

            # Creating a subproject
            if parent_project:
                # Parent must be current parent
                self.initial['parent'] = parent_project.sodar_uuid
                # Set initial value for type
                self.initial['type'] = None
            # Creating a top level project
            else:
                # Force project type
                if disable_categories:
                    self.initial['type'] = PROJECT_TYPE_PROJECT
                else:
                    self.initial['type'] = PROJECT_TYPE_CATEGORY
                # Hide project type selection
                self.fields['type'].widget = forms.HiddenInput()
                # Set up parent field
                self.initial['parent'] = None

        if self.instance.is_remote():
            self.fields['title'].widget = forms.HiddenInput()
            self.fields['type'].widget = forms.HiddenInput()
            self.fields['parent'].widget = forms.HiddenInput()
            self.fields['description'].widget = forms.HiddenInput()
            self.fields['readme'].widget = forms.HiddenInput()

    def clean(self):
        """Function for custom form validation and cleanup"""
        self.instance_owner_as = (
            self.instance.get_owner() if self.instance else None
        )
        disable_categories = getattr(
            settings, 'PROJECTROLES_DISABLE_CATEGORIES', False
        )
        parent = self.cleaned_data.get('parent')
        title = self.cleaned_data.get('title')
        p_type = self.cleaned_data.get('type')
        owner = self.cleaned_data.get('owner')

        # Check for category/project being placed in root
        if not parent and (not self.instance or self.instance.parent):
            if (
                p_type == PROJECT_TYPE_CATEGORY
                and not self.current_user.is_superuser
            ):
                self.add_error(
                    'parent',
                    'You do not have permission to place a {} under '
                    'root'.format(get_display_name(PROJECT_TYPE_CATEGORY)),
                )
            elif p_type == PROJECT_TYPE_PROJECT and not disable_categories:
                self.add_error(
                    'parent', 'Projects can not be placed under root'
                )

        # Ensure prohibited substrings are not found in title
        if (
            CAT_DELIMITER in title
            or title.startswith(CAT_DELIMITER.strip())
            or title.endswith(CAT_DELIMITER.strip())
        ):
            self.add_error('title', CAT_DELIMITER_ERROR_MSG)
        # Ensure title does not match parent
        if parent and parent.title == title:
            self.add_error(
                'title',
                '{} and parent titles can not be equal'.format(
                    get_display_name(p_type, title=True)
                ),
            )
        # Ensure title is unique within parent
        existing_project = Project.objects.filter(
            parent=parent,
            title=title,
        ).first()
        if existing_project and (
            not self.instance or existing_project.pk != self.instance.pk
        ):
            self.add_error('title', 'Title must be unique within parent')

        # Ensure owner has been set
        if not owner:
            self.add_error(
                'owner',
                'Owner must be set for {}'.format(get_display_name(p_type)),
            )
        # Ensure owner is not changed on update (must use ownership transfer)
        if self.instance_owner_as and owner != self.instance_owner_as.user:
            self.add_error(
                'owner',
                'Owner update is not allowed in this form, use Ownership '
                'Transfer instead',
            )

        # Ensure public_guest_access is not set on a category
        if p_type == PROJECT_TYPE_CATEGORY and self.cleaned_data.get(
            'public_guest_access'
        ):
            self.add_error(
                'public_guest_access',
                'Public guest access is not allowed for categories',
            )

        # Verify settings fields
        cleaned_data, errors = self._validate_app_settings(
            self.cleaned_data,
            self.app_plugins,
            self.app_settings,
            self.p_kwargs,
            self.instance,
            self.instance_owner_as,
        )
        for key, value in cleaned_data.items():
            self.cleaned_data[key] = value
        for field, error in errors:
            self.add_error(field, error)
        return self.cleaned_data


# RoleAssignment form ----------------------------------------------------------


class RoleAssignmentForm(SODARModelForm):
    """Form for editing Project role assignments"""

    promote = forms.BooleanField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = RoleAssignment
        fields = ['project', 'user', 'role', 'promote']

    def __init__(
        self, project=None, current_user=None, promote_as=None, *args, **kwargs
    ):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)
        # Get current user for checking permissions for form items
        if current_user:
            self.current_user = current_user
        # Get the project for which role is being assigned
        self.project = None
        if self.instance.pk:
            self.project = self.instance.project
        else:
            self.project = Project.objects.filter(sodar_uuid=project).first()
        # Get promote assignment in case of promoting inherited user
        # NOTE: This is already validated in get()
        if promote_as:
            promote_as = RoleAssignment.objects.filter(
                sodar_uuid=promote_as
            ).first()

        # Modify project field to use sodar_uuid
        self.fields['project'].to_field_name = 'sodar_uuid'
        # Set up user field
        if promote_as:
            self.initial['user'] = promote_as.user
            self.fields['user'].widget = forms.HiddenInput()
            self.initial['promote'] = True
        else:
            self.fields['user'] = SODARUserChoiceField(
                scope='project_exclude',
                project=self.project,
                forward=['role'],
                url=reverse('projectroles:ajax_autocomplete_user_redirect'),
                widget_class=SODARUserRedirectWidget,
            )
            self.initial['promote'] = False

        # Limit role choices
        q_kwargs = {'project': self.project, 'current_user': self.current_user}
        if promote_as:
            q_kwargs['promote_as'] = promote_as
        elif self.instance.pk:  # Restrict choices by overridden inactive role
            active_as = self.project.get_role(self.instance.user)
            if active_as and active_as.project != self.project:
                inactive_as = RoleAssignment.objects.filter(
                    project=self.project, user=self.instance.user
                ).first()
                if inactive_as and inactive_as.role.rank > active_as.role.rank:
                    q_kwargs['promote_as'] = active_as
        self.fields['role'].choices = get_role_choices(**q_kwargs)

        # Updating an existing assignment
        if self.instance.pk:
            # Set values
            self.initial['project'] = self.instance.project.sodar_uuid
            self.initial['user'] = self.instance.user.sodar_uuid
            # Hide project and user switching
            self.fields['project'].widget = forms.HiddenInput()
            self.fields['user'].widget = forms.HiddenInput()
            # Set initial role
            self.initial['role'] = self.instance.role

        # Creating a new assignment
        elif self.project:  # TODO: I think this could just be "else"
            # Limit project choice to self.project, hide widget
            self.initial['project'] = self.project.sodar_uuid
            self.fields['project'].widget = forms.HiddenInput()
            if promote_as:
                self.fields['role'].initial = max(
                    [c[0] for c in self.fields['role'].choices]
                )
            if not promote_as:
                self.fields['role'].initial = Role.objects.get(
                    name=PROJECT_ROLE_GUEST
                ).pk

    def clean(self):
        """Function for custom form validation and cleanup"""
        role = self.cleaned_data.get('role')
        existing_as = RoleAssignment.objects.filter(
            project=self.cleaned_data.get('project'),
            user=self.cleaned_data.get('user'),
        ).first()

        # Adding a new RoleAssignment
        if not self.instance.pk:
            # Make sure user doesn't already have role in project
            if existing_as:
                self.add_error(
                    'user',
                    'User {} already assigned as {}'.format(
                        existing_as.role.name,
                        get_user_display_name(self.cleaned_data.get('user')),
                    ),
                )
        # Updating a RoleAssignment
        else:
            # Ensure not setting existing role again
            if existing_as and existing_as.role == role:
                self.add_error('role', 'Role already assigned to user')

        # Delegate checks
        if role.name == PROJECT_ROLE_DELEGATE:
            del_limit = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)
            # Ensure current user has permission to set delegate
            if not self.current_user.has_perm(
                'projectroles.update_project_delegate', obj=self.project
            ):
                self.add_error(
                    'role', 'Insufficient permissions for altering delegate'
                )
            # Ensure delegate limit is not exceeded
            if (
                del_limit != 0
                and len(self.project.get_delegates(inherited=False))
                >= del_limit
            ):
                self.add_error(
                    'role',
                    'The limit ({}) of delegates for this {} has '
                    'already been reached.'.format(
                        del_limit, get_display_name(self.project.type)
                    ),
                )
        return self.cleaned_data


# Owner transfer form ----------------------------------------------------------


class RoleAssignmentOwnerTransferForm(SODARForm):
    """Form for transferring owner role assignment between users"""

    @classmethod
    def _get_old_owner_choices(cls, project, old_owner_as):
        q_kwargs = {'project_types__contains': [project.type]}
        inh_role_as = project.get_role(old_owner_as.user, inherited_only=True)
        if (
            not inh_role_as
            or inh_role_as.role.rank != ROLE_RANKING[PROJECT_ROLE_OWNER]
        ):
            q_kwargs['rank__gt'] = ROLE_RANKING[PROJECT_ROLE_OWNER]
        if inh_role_as:
            q_kwargs['rank__lte'] = inh_role_as.role.rank
        return [
            get_role_option(project, role)
            for role in Role.objects.filter(**q_kwargs).order_by('rank')
        ]

    def __init__(self, project, current_user, current_owner, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)
        # Get current user for checking permissions for form items
        self.current_user = current_user
        # Get the project for which role is being assigned
        self.project = project
        self.current_owner = current_owner

        self.fields['new_owner'] = SODARUserChoiceField(
            label='New owner',
            help_text='Select a member of the {} to become owner.'.format(
                get_display_name(project.type)
            ),
            scope='project',
            project=project,
            exclude=[current_owner],
        )

        old_owner_as = RoleAssignment.objects.get(
            project=project, user=current_owner, role__name=PROJECT_ROLE_OWNER
        )
        self.selectable_roles = self._get_old_owner_choices(
            project, old_owner_as
        )
        self.fields['old_owner_role'] = forms.ChoiceField(
            label='New role for {}'.format(current_owner.username),
            help_text='New role for the current owner. Select "Remove" in '
            'the member list to remove the user\'s membership.',
            choices=self.selectable_roles,
            initial=self.selectable_roles[0][0],
            disabled=True if len(self.selectable_roles) == 1 else False,
        )

        self.fields['project'] = forms.Field(
            widget=forms.HiddenInput(), initial=project.sodar_uuid
        )

    def clean_old_owner_role(self):
        role = Role.objects.filter(
            pk=self.cleaned_data.get('old_owner_role')
        ).first()
        if not role:
            raise forms.ValidationError('Selected role not found')

        if role.name == PROJECT_ROLE_DELEGATE:
            del_limit = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)
            # Ensure current user has permission to set delegate
            if not self.current_user.has_perm(
                'projectroles.update_project_delegate', obj=self.project
            ):
                raise forms.ValidationError(
                    'Insufficient permissions for assigning a delegate role'
                )
            # Ensure delegate limit is not exceeded
            new_owner_role = RoleAssignment.objects.filter(
                project=self.project, user=self.cleaned_data.get('new_owner')
            ).first()
            if (
                del_limit != 0
                and new_owner_role
                and new_owner_role.role.name != PROJECT_ROLE_DELEGATE
                and len(self.project.get_delegates(inherited=False))
                >= del_limit
            ):
                raise forms.ValidationError(
                    'The limit of delegates ({}) for this {} has already been '
                    'reached.'.format(
                        del_limit, get_display_name(self.project.type)
                    )
                )
        return role

    def clean_new_owner(self):
        user = self.cleaned_data['new_owner']
        if user == self.current_owner:
            raise forms.ValidationError(
                'The new owner shouldn\'t be the current owner.'
            )
        role_as = self.project.get_role(user)
        if not role_as:
            raise forms.ValidationError(
                'The new owner has no inherited or local roles in the '
                '{}.'.format(get_display_name(self.project.type))
            )
        return user


# ProjectInvite form -----------------------------------------------------------


class ProjectInviteForm(SODARModelForm):
    """Form for ProjectInvite modification"""

    class Meta:
        model = ProjectInvite
        fields = ['email', 'role', 'message']

    def __init__(
        self,
        project=None,
        current_user=None,
        mail=None,
        role=None,
        *args,
        **kwargs
    ):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)
        # Get current user for checking permissions and saving issuer
        if current_user:
            self.current_user = current_user
        # in case it has been redirected from the RoleAssignment form
        if mail:
            self.fields['email'].initial = mail
        # Get the project for which invite is being sent
        self.project = Project.objects.filter(sodar_uuid=project).first()
        # Limit Role choices according to user permissions
        self.fields['role'].choices = get_role_choices(
            self.project, self.current_user, allow_delegate=True
        )
        if role:
            self.fields['role'].initial = role
        else:
            self.fields['role'].initial = Role.objects.get(
                name=PROJECT_ROLE_GUEST
            ).pk
        # Limit textarea height
        self.fields['message'].widget.attrs['rows'] = 4

    def clean(self):
        user_email = self.cleaned_data.get('email')
        # Check if user email is already in users
        existing_user = User.objects.filter(email=user_email).first()
        if existing_user:
            self.add_error(
                'email',
                'User "{}" already exists in the system with this email. '
                'Please use "Add Role" instead.'.format(existing_user.username),
            )

        # Check if user already has an invite in the project
        try:
            ProjectInvite.objects.get(
                project=self.project,
                email=user_email,
                active=True,
                date_expire__gt=timezone.now(),
            )
            self.add_error(
                'email',
                'There is already an active invite for email {} in {}'.format(
                    user_email, self.project.title
                ),
            )
        except ProjectInvite.DoesNotExist:
            pass

        # Local users check
        if user_email:
            domain = user_email[user_email.find('@') + 1 :]
            domain_list = [
                getattr(settings, 'AUTH_LDAP_USERNAME_DOMAIN', ''),
                getattr(settings, 'AUTH_LDAP2_USERNAME_DOMAIN', ''),
            ]
            if (
                not settings.PROJECTROLES_ALLOW_LOCAL_USERS
                and not settings.ENABLE_SAML
                and domain
                not in [
                    x.lower() for x in getattr(settings, 'LDAP_ALT_DOMAINS', [])
                ]
                and domain.split('.')[0].lower()
                not in [x.lower() for x in domain_list]
            ):
                self.add_error(
                    'email',
                    'Local users not allowed, email domain {} not recognized '
                    'for LDAP users'.format(domain),
                )

        # Delegate checks
        role = self.cleaned_data.get('role')
        if role.name == PROJECT_ROLE_DELEGATE:
            del_limit = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)
            # Ensure current user has permission to invite delegate
            if not self.current_user.has_perm(
                'projectroles.update_project_delegate', obj=self.project
            ):
                self.add_error(
                    'role', 'Insufficient permissions for inviting delegate.'
                )
            # Ensure delegate limit is not exceeded
            if (
                del_limit != 0
                and len(self.project.get_delegates(inherited=False))
                >= del_limit
            ):
                self.add_error(
                    'role',
                    'The delegate limit of {} for this {} has '
                    'already been reached.'.format(
                        del_limit, get_display_name(self.project.type)
                    ),
                )
        return self.cleaned_data

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)
        obj.project = self.project
        obj.issuer = self.current_user
        obj.date_expire = timezone.now() + timezone.timedelta(
            days=settings.PROJECTROLES_INVITE_EXPIRY_DAYS
        )
        obj.secret = build_secret()
        obj.save()
        return obj


# RemoteSite form --------------------------------------------------------------


class RemoteSiteForm(SODARModelForm):
    """Form for RemoteSite creation/updating"""

    class Meta:
        model = RemoteSite
        fields = ['name', 'url', 'description', 'user_display', 'secret']

    def __init__(self, current_user=None, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)
        self.current_user = current_user

        # Default field modifications
        self.fields['description'].required = False
        self.fields['secret'].widget = forms.TextInput(
            attrs={'class': 'sodar-code-input'}
        )
        self.fields['description'].widget.attrs['rows'] = 4

        # Special cases for SOURCE
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            self.fields['secret'].widget.attrs['readonly'] = True
            self.fields['user_display'].widget = forms.CheckboxInput()
        elif settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET:
            self.fields['user_display'].widget = forms.HiddenInput()
        self.fields['user_display'].initial = True

        # Creation
        if not self.instance.pk:
            # Generate secret token for target site
            if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
                self.fields['secret'].initial = build_secret()

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)
        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            obj.mode = SITE_MODE_TARGET
        else:
            obj.mode = SITE_MODE_SOURCE
        obj.save()
        return obj


# Local user editing form ------------------------------------------------------


class LocalUserForm(SODARModelForm):
    """Form for local user creation and updating"""

    password_confirm = forms.CharField(
        label='Confirm password', widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'password',
            'password_confirm',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['password'].widget = forms.PasswordInput()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['password'] != cleaned_data['password_confirm']:
            self.add_error('password_confirm', 'Passwords didn\'t match!')
            self.add_error('password', 'Passwords didn\'t match!')
        return cleaned_data


# Helper functions -------------------------------------------------------------


def get_role_option(project, role):
    """
    Return form option value for a Role object.

    :param project: Project object
    :param role: Role object
    return: Role key and legend
    """
    return role.pk, '{} {}'.format(
        get_display_name(project.type, title=True),
        role.name.split(' ')[1].capitalize(),
    )


def get_role_choices(
    project, current_user, promote_as=None, allow_delegate=True
):
    """
    Return valid role choices according to permissions of current user.

    :param project: Project in which role will be assigned
    :param current_user: User for whom the form is displayed
    :param promote_as: Assignment for promoting inherited user, or inactive
                       overridden assignment (RoleAssignment or None)
    :param allow_delegate: Whether delegate should be allowed (bool)
    :return: List
    """
    # Owner cannot be changed
    role_excludes = [PROJECT_ROLE_OWNER]
    # Exclude delegate if not allowed or current user lacks perms
    if not allow_delegate or not current_user.has_perm(
        'projectroles.update_project_delegate', obj=project
    ):
        role_excludes.append(PROJECT_ROLE_DELEGATE)
    qs = Role.objects.filter(project_types__contains=[project.type])
    if promote_as:
        qs = qs.filter(rank__lt=promote_as.role.rank)
    return [
        get_role_option(project, role)
        for role in qs.exclude(name__in=role_excludes)
    ]
