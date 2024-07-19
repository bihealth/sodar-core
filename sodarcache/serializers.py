"""Serializers for the sodarcache app REST API"""

# Projectroles dependency
from projectroles.serializers import (
    SODARProjectModelSerializer,
    SODARUserSerializer,
)

from sodarcache.models import JSONCacheItem


class JSONCacheItemSerializer(SODARProjectModelSerializer):
    """Serializer for the JSONCacheItem model"""

    user = SODARUserSerializer(read_only=True)

    class Meta:
        model = JSONCacheItem
        fields = [
            'project',
            'app_name',
            'name',
            'date_modified',
            'user',
            'data',
        ]  # NOTE: No UUID returned as these should not be referred to directly
        read_only_fields = ['date_modified']
