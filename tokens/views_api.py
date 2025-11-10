"""REST API views for the tokens app"""

import datetime
import logging

from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.views import APIView

from knox.models import AuthToken

from drf_spectacular.utils import extend_schema, inline_serializer


logger = logging.getLogger(__name__)


# Local constants
TOKENS_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar-core.tokens+json'
TOKENS_API_DEFAULT_VERSION = '1.0'
TOKENS_API_ALLOWED_VERSIONS = ['1.0']


# Base Classes and Mixins ------------------------------------------------------


class TokensAPIVersioningMixin:
    """
    Tokens API view versioning mixin for overriding media type and
    accepted versions.
    """

    class TokensAPIRenderer(JSONRenderer):
        media_type = TOKENS_API_MEDIA_TYPE

    class TokensAPIVersioning(AcceptHeaderVersioning):
        allowed_versions = TOKENS_API_ALLOWED_VERSIONS
        default_version = TOKENS_API_DEFAULT_VERSION

    renderer_classes = [TokensAPIRenderer]
    versioning_class = TokensAPIVersioning


# API Views --------------------------------------------------------------------


@extend_schema(
    responses={
        '201': inline_serializer(
            'UserTokenCreate',
            fields={
                'delete_count': serializers.IntegerField(),
                'expiry': serializers.CharField(),
                'token': serializers.CharField(),
                'user_uuid': serializers.CharField(),
            },
        ),
    }
)
class UserTokenCreateAPIView(TokensAPIVersioningMixin, APIView):
    """
    Create and return an API access token for a user logging in with basic
    authentication. Deletes any previously existing tokens for the user.

    The returned token string is only visible once and should be stored upon
    retrieval.

    **URL:** ``/tokens/api/create``

    **Methods:** ``POST``

    **Parameters:**

    - ``expiry``: Token expiry in hours (integer, optional)

    **Returns:**

    - ``delete_count``: Number of deleted previous tokens for the user (integer)
    - ``expiry``: Expiry datetime for token (YYYY-MM-DDThh:mm:ssZ or None)
    - ``token``: API token (string)
    - ``user_uuid`` User ``sodar_uuid`` value (string)
    """

    permisston_classes = [IsAuthenticated]
    serializer_class = None

    def post(self, request, *args, **kwargs):
        user = request.user
        user_tokens = user.auth_token_set.all()
        tc = user_tokens.count()
        user_tokens.delete()
        if tc > 0:
            logger.info(
                'Deleted {} token{} from {}'.format(
                    tc, 's' if tc != 1 else '', user.username
                )
            )
        expiry = request.data.get('expiry')
        e_delta = datetime.timedelta(hours=int(expiry)) if expiry else None
        instance, token = AuthToken.objects.create(self.request.user, e_delta)
        ret = {
            'token': token,
            'expiry': (
                timezone.localtime(
                    instance.expiry, ZoneInfo(settings.TIME_ZONE)
                ).isoformat()
                if instance.expiry
                else None
            ),
            'delete_count': tc,
            'user_uuid': str(user.sodar_uuid),
        }
        return Response(ret, status=201)
