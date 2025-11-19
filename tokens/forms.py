from django import forms

# Projectroles dependency
from projectroles.forms import SODARForm


class TokenCreateForm(SODARForm):
    """Form for SODARAuthToken creation"""

    #: Optional label
    sodar_label = forms.CharField(
        label='Token label',
        required=False,
        max_length=256,
        help_text='Optional label for token',
    )

    #: Time to live in hours
    expiry = forms.IntegerField(
        label='Expiry',
        min_value=0,
        required=True,
        initial=0,
        help_text='Expiry time in hours. Set to 0 for tokens that never '
        'expire.',
    )
