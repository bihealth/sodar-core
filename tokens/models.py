"""Models for the tokens app"""

from django.db import models

from knox.models import AbstractAuthToken


# Local constants
TOKEN_LABEL_MAX_LENGTH = 256


class SODARAuthToken(AbstractAuthToken):
    """API token model extending the django-rest-knox AuthToken model"""

    class Meta:
        swappable = 'KNOX_TOKEN_MODEL'

    #: Token label
    sodar_label = models.CharField(
        max_length=TOKEN_LABEL_MAX_LENGTH,
        blank=True,
        unique=False,
        help_text='Optional label for token',
    )

    def __str__(self) -> str:
        # Following the AuthToken convention for maximum compatibility
        return '{} : {}{}'.format(
            self.digest,
            self.user.username,
            f' : {self.sodar_label}' if self.sodar_label else '',
        )
