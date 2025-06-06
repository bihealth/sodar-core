"""Django Rest Framework serializers for the filesfolders app"""

# NB: Creating abstract serializers is not easily possible as explained in the
# following StackOverflow post: https://stackoverflow.com/a/33137535

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

# Projectroles dependency
from projectroles.serializers import SODARProjectModelSerializer
from projectroles.utils import build_secret

from filesfolders.models import File, Folder, HyperLink


class FilesfoldersSerializerBase(SODARProjectModelSerializer):
    """Base class for filesfolders serializers"""

    folder = serializers.SlugRelatedField(
        slug_field='sodar_uuid', queryset=Folder.objects.all(), required=False
    )
    owner = serializers.SlugRelatedField(
        slug_field='sodar_uuid', read_only=True
    )

    def _process_validated_data(self, validated_data):
        if 'folder' in self.context['request'].data:
            folder_uuid = self.context['request'].data['folder']
            folder = get_object_or_404(
                Folder.objects.filter(project=self.context['project']),
                sodar_uuid=folder_uuid,
            )
            validated_data['folder'] = folder
        return validated_data

    def update(self, instance, validated_data):
        validated_data = self._process_validated_data(validated_data)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        validated_data['project'] = self.context['project']
        validated_data['owner'] = self.context['request'].user
        validated_data = self._process_validated_data(validated_data)
        return super().create(validated_data)


class FolderSerializer(FilesfoldersSerializerBase):
    """
    Serializer for the Folder model.

    Makes the following fields directly editable: name, flag, description.

    The folder field can be set to a UUID that must refer to a parent folder
    in the parent's folder.

    On creation, the owner is automatically set to the current user that
    cannot be changed later. The project is set to the current project
    on creation and is not updated later.
    """

    class Meta:
        model = Folder
        fields = [
            'name',
            'folder',
            'owner',
            'project',
            'flag',
            'description',
            'date_modified',
            'sodar_uuid',
        ]
        read_only_fields = ['date_modified']


class FileSerializer(FilesfoldersSerializerBase):
    """
    Serializer for the File model.

    Makes the following fields directly editable: name, flag, description.

    The folder field can be set to a UUID that must refer to a parent folder
    in the parent's folder.

    On creation, the owner is automatically set to the current user that
    cannot be changed later. The project is set to the current project
    on creation and is not updated later.

    The secret will be created and updated automatically when the 'public_url'
    flag is changed.
    """

    file = serializers.FileField(write_only=True)

    class Meta:
        model = File
        fields = [
            'name',
            'folder',
            'owner',
            'project',
            'flag',
            'description',
            'date_modified',
            'public_url',
            'secret',
            'file',
            'sodar_uuid',
        ]
        read_only_fields = ['date_modified', 'secret']

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.secret = build_secret()
        instance.save()
        return instance

    def update(self, instance, validated_data):
        if instance.public_url != bool(
            validated_data.get('public_url', instance.public_url)
        ):
            instance.secret = build_secret()
            instance.save()
        return super().update(instance, validated_data)


class HyperLinkSerializer(FilesfoldersSerializerBase):
    """
    Serializer for the HyperLink model.

    Makes the following fields directly editable: name, flag, description.

    The folder field can be set to a UUID that must refer to a parent folder
    in the parent's folder.

    On creation, the owner is automatically set to the current user that
    cannot be changed later. The project is set to the current project
    on creation and is not updated later.
    """

    class Meta:
        model = HyperLink
        fields = [
            'name',
            'folder',
            'owner',
            'project',
            'flag',
            'description',
            'date_modified',
            'url',
            'sodar_uuid',
        ]
        read_only_fields = ['date_modified']
