"""Django Rest Framework serializers for the timeline app"""

from rest_framework import serializers

# Projectroles dependency
from projectroles.serializers import (
    SODARModelSerializer,
    SODARProjectModelSerializer,
)

from timeline.models import (
    TimelineEvent,
    TimelineEventStatus,
    TimelineEventObjectRef,
)


class ExtraDataRepresentationMixin:
    """Mixin for controlling extra data visibility to users"""

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        user = self.context['request'].user
        project = instance.get_project()
        if (
            project
            and not user.has_perm('timeline.view_event_extra_data', project)
            and not user.is_superuser
        ):
            ret.pop('extra_data')
        elif not project and not user.is_superuser:
            ret.pop('extra_data')
        return ret


class TimelineEventObjectRefSerializer(
    ExtraDataRepresentationMixin, serializers.ModelSerializer
):
    """
    Serializer for the TimelineEventObjectRef model. All fields are set to
    read-only.
    """

    event = serializers.SlugRelatedField(
        slug_field='sodar_uuid', read_only=True
    )

    class Meta:
        model = TimelineEventObjectRef
        fields = [
            'event',
            'label',
            'name',
            'object_model',
            'object_uuid',
            'extra_data',
            'sodar_uuid',
        ]
        read_only_fields = fields


class TimelineEventStatusSerializer(
    ExtraDataRepresentationMixin, SODARModelSerializer
):
    """
    Serializer for the TimelineEventStatus model. All fields are set to
    read-only.
    """

    event = serializers.SlugRelatedField(
        slug_field='sodar_uuid', read_only=True
    )

    class Meta:
        model = TimelineEventStatus
        fields = [
            'event',
            'timestamp',
            'status_type',
            'description',
            'extra_data',
            'sodar_uuid',
        ]
        read_only_fields = fields


class TimelineEventSerializer(
    ExtraDataRepresentationMixin, SODARProjectModelSerializer
):
    """
    Serializer for the TimelineEvent model. All fields are set to read-only.
    """

    user = serializers.SlugRelatedField(
        allow_null=True, slug_field='sodar_uuid', read_only=True
    )
    status_changes = TimelineEventStatusSerializer(many=True, read_only=True)
    event_objects = TimelineEventObjectRefSerializer(many=True, read_only=True)

    class Meta:
        model = TimelineEvent
        fields = [
            'project',
            'app',
            'plugin',
            'user',
            'event_name',
            'description',
            'extra_data',
            'classified',
            'status_changes',
            'event_objects',
            'sodar_uuid',
        ]
        read_only_fields = fields
