"""Serializers for the sodarcache app REST API"""

from rest_framework import serializers

# Projectroles dependency
from projectroles.serializers import SODARProjectModelSerializer

from sodarcache.models import JSONCacheItem


class JSONCacheItemSerializer(SODARProjectModelSerializer):
    """Serializer for the JSONCacheItem model"""

    user = serializers.SlugRelatedField(slug_field='sodar_uuid', read_only=True)

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
