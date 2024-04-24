"""Forms for the adminalerts app"""

from django import forms
from django.utils import timezone

# Projectroles dependency
from projectroles.forms import SODARModelForm, SODARPagedownWidget

from adminalerts.models import AdminAlert


# Local constants
EMAIL_HELP_CREATE = 'Send alert as email to all users on this site'
EMAIL_HELP_UPDATE = 'Send updated alert as email to all users on this site'


class AdminAlertForm(SODARModelForm):
    """Form for AdminAlert creation/updating"""

    send_email = forms.BooleanField(
        initial=True,
        label='Send alert as email',
        required=False,
    )

    class Meta:
        model = AdminAlert
        fields = [
            'message',
            'date_expire',
            'active',
            'require_auth',
            'send_email',
            'description',
        ]

    def __init__(self, current_user=None, *args, **kwargs):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)
        self.current_user = current_user

        # Set date_expire properties
        # NOTE: "format" works in source but not in widget, any way to fix?
        self.fields['date_expire'].label = 'Expiry date'
        self.fields['date_expire'].widget = forms.widgets.DateInput(
            attrs={'type': 'date'}, format='%Y-%m-%d'
        )
        # Set description widget with preview
        self.fields['description'].widget = SODARPagedownWidget(
            attrs={'show_preview': True}
        )

        # Creation
        if not self.instance.pk:
            self.initial['date_expire'] = timezone.now() + timezone.timedelta(
                days=1
            )
            self.fields['send_email'].help_text = EMAIL_HELP_CREATE
        # Updating
        else:  # self.instance.pk
            # Set description value as raw markdown
            self.initial['description'] = self.instance.description.raw
            self.fields['send_email'].help_text = EMAIL_HELP_UPDATE
            # Sending email for update should be false by default
            self.initial['send_email'] = False

    def clean(self):
        """Custom form validation and cleanup"""
        # Don't allow alerts to expire in the past :)
        if self.cleaned_data.get('date_expire') <= timezone.now():
            self.add_error(
                'date_expire', 'Expiry date must be set in the future'
            )
        return self.cleaned_data

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)
        obj.user = self.current_user
        obj.save()
        return obj
