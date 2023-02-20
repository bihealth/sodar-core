from django.urls import path

from . import views, views_api

# NOTE: file/folder/hyperlink objects can be referred to as 'item', but only if
#       ObjectPermissionMixin is used in the view

app_name = 'filesfolders'

urls_ui = [
    path(
        route='<uuid:project>',
        view=views.ProjectFileView.as_view(),
        name='list',
    ),
    path(
        route='folder/<uuid:folder>',
        view=views.ProjectFileView.as_view(),
        name='list',
    ),
    path(
        route='upload/<uuid:project>',
        view=views.FileCreateView.as_view(),
        name='file_create',
    ),
    path(
        route='upload/in/<uuid:folder>',
        view=views.FileCreateView.as_view(),
        name='file_create',
    ),
    path(
        route='update/<uuid:item>',
        view=views.FileUpdateView.as_view(),
        name='file_update',
    ),
    path(
        route='delete/<uuid:item>',
        view=views.FileDeleteView.as_view(),
        name='file_delete',
    ),
    path(
        route='download/<uuid:file>/<path:file_name>',
        view=views.FileServeView.as_view(),
        name='file_serve',
    ),
    path(
        route='download/<str:secret>/<path:file_name>',
        view=views.FileServePublicView.as_view(),
        name='file_serve_public',
    ),
    path(
        route='link/<uuid:file>',
        view=views.FilePublicLinkView.as_view(),
        name='file_public_link',
    ),
    path(
        route='folder/add/<uuid:project>',
        view=views.FolderCreateView.as_view(),
        name='folder_create',
    ),
    path(
        route='folder/add/in/<uuid:folder>',
        view=views.FolderCreateView.as_view(),
        name='folder_create',
    ),
    path(
        route='folder/update/<uuid:item>',
        view=views.FolderUpdateView.as_view(),
        name='folder_update',
    ),
    path(
        route='folder/delete/<uuid:item>',
        view=views.FolderDeleteView.as_view(),
        name='folder_delete',
    ),
    path(
        route='link/add/<uuid:project>',
        view=views.HyperLinkCreateView.as_view(),
        name='hyperlink_create',
    ),
    path(
        route='link/add/in/<uuid:folder>',
        view=views.HyperLinkCreateView.as_view(),
        name='hyperlink_create',
    ),
    path(
        route='link/update/<uuid:item>',
        view=views.HyperLinkUpdateView.as_view(),
        name='hyperlink_update',
    ),
    path(
        route='link/delete/<uuid:item>',
        view=views.HyperLinkDeleteView.as_view(),
        name='hyperlink_delete',
    ),
    path(
        route='batch/<uuid:project>',
        view=views.BatchEditView.as_view(),
        name='batch_edit',
    ),
    path(
        route='batch/in/<uuid:folder>',
        view=views.BatchEditView.as_view(),
        name='batch_edit',
    ),
]

urls_api = [
    path(
        route='api/folder/list-create/<uuid:project>',
        view=views_api.FolderListCreateAPIView.as_view(),
        name='api_folder_list_create',
    ),
    path(
        route='api/folder/retrieve-update-destroy/<uuid:folder>',
        view=views_api.FolderRetrieveUpdateDestroyAPIView.as_view(),
        name='api_folder_retrieve_update_destroy',
    ),
    path(
        route='api/file/list-create/<uuid:project>',
        view=views_api.FileListCreateAPIView.as_view(),
        name='api_file_list_create',
    ),
    path(
        route='api/file/retrieve-update-destroy/<uuid:file>',
        view=views_api.FileRetrieveUpdateDestroyAPIView.as_view(),
        name='api_file_retrieve_update_destroy',
    ),
    path(
        route='api/file/serve/<uuid:file>',
        view=views_api.FileServeAPIView.as_view(),
        name='api_file_serve',
    ),
    path(
        route='api/hyperlink/list-create/<uuid:project>',
        view=views_api.HyperLinkListCreateAPIView.as_view(),
        name='api_hyperlink_list_create',
    ),
    path(
        route='api/hyperlink/retrieve-update-destroy/<uuid:hyperlink>',
        view=views_api.HyperLinkRetrieveUpdateDestroyAPIView.as_view(),
        name='api_hyperlink_retrieve_update_destroy',
    ),
]

urlpatterns = urls_ui + urls_api
