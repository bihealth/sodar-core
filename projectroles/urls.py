from django.urls import path

from projectroles import views, views_ajax, views_api

app_name = 'projectroles'

# UI views
urls_ui = [
    path(
        route='<uuid:project>',
        view=views.ProjectDetailView.as_view(),
        name='detail',
    ),
    path(
        route='update/<uuid:project>',
        view=views.ProjectUpdateView.as_view(),
        name='update',
    ),
    path(
        route='create',
        view=views.ProjectCreateView.as_view(),
        name='create',
    ),
    path(
        route='create/<uuid:project>',
        view=views.ProjectCreateView.as_view(),
        name='create',
    ),
    path(
        route='archive/<uuid:project>',
        view=views.ProjectArchiveView.as_view(),
        name='archive',
    ),
    # Search views
    path(
        route='search/results/',
        view=views.ProjectSearchResultsView.as_view(),
        name='search',
    ),
    path(
        route='search/advanced',
        view=views.ProjectAdvancedSearchView.as_view(),
        name='search_advanced',
    ),
    # Project role views
    path(
        route='members/<uuid:project>',
        view=views.ProjectRoleView.as_view(),
        name='roles',
    ),
    path(
        route='members/<uuid:project>',
        view=views.ProjectRoleView.as_view(),
        name='roles',
    ),
    path(
        route='members/create/<uuid:project>',
        view=views.RoleAssignmentCreateView.as_view(),
        name='role_create',
    ),
    path(
        route='members/promote/<uuid:project>/assignment/<uuid:promote_as>',
        view=views.RoleAssignmentCreateView.as_view(),
        name='role_create_promote',
    ),
    path(
        route='members/update/<uuid:roleassignment>',
        view=views.RoleAssignmentUpdateView.as_view(),
        name='role_update',
    ),
    path(
        route='members/delete/<uuid:roleassignment>',
        view=views.RoleAssignmentDeleteView.as_view(),
        name='role_delete',
    ),
    path(
        route='members/owner/transfer/<uuid:project>',
        view=views.RoleAssignmentOwnerTransferView.as_view(),
        name='role_owner_transfer',
    ),
    # Project invite views
    path(
        route='invites/<uuid:project>',
        view=views.ProjectInviteView.as_view(),
        name='invites',
    ),
    path(
        route='invites/create/<uuid:project>',
        view=views.ProjectInviteCreateView.as_view(),
        name='invite_create',
    ),
    path(
        route='invites/accept/<str:secret>',
        view=views.ProjectInviteAcceptView.as_view(),
        name='invite_accept',
    ),
    path(
        route='invites/process/ldap/<str:secret>',
        view=views.ProjectInviteProcessLDAPView.as_view(),
        name='invite_process_ldap',
    ),
    path(
        route='invites/process/local/<str:secret>',
        view=views.ProjectInviteProcessLocalView.as_view(),
        name='invite_process_local',
    ),
    path(
        route='invites/resend/<uuid:projectinvite>',
        view=views.ProjectInviteResendView.as_view(),
        name='invite_resend',
    ),
    path(
        route='invites/revoke/<uuid:projectinvite>',
        view=views.ProjectInviteRevokeView.as_view(),
        name='invite_revoke',
    ),
    path(
        route='user/update',
        view=views.UserUpdateView.as_view(),
        name='user_update',
    ),
    # Remote site and project views
    path(
        route='remote/sites',
        view=views.RemoteSiteListView.as_view(),
        name='remote_sites',
    ),
    path(
        route='remote/site/add',
        view=views.RemoteSiteCreateView.as_view(),
        name='remote_site_create',
    ),
    path(
        route='remote/site/update/<uuid:remotesite>',
        view=views.RemoteSiteUpdateView.as_view(),
        name='remote_site_update',
    ),
    path(
        route='remote/site/delete/<uuid:remotesite>',
        view=views.RemoteSiteDeleteView.as_view(),
        name='remote_site_delete',
    ),
    path(
        route='remote/site/<uuid:remotesite>',
        view=views.RemoteProjectListView.as_view(),
        name='remote_projects',
    ),
    path(
        route='remote/site/access/<uuid:remotesite>',
        view=views.RemoteProjectBatchUpdateView.as_view(),
        name='remote_projects_update',
    ),
    path(
        route='remote/site/sync/<uuid:remotesite>',
        view=views.RemoteProjectSyncView.as_view(),
        name='remote_projects_sync',
    ),
]

# Ajax API views
urls_ajax = [
    path(
        route='ajax/list',
        view=views_ajax.ProjectListAjaxView.as_view(),
        name='ajax_project_list',
    ),
    path(
        route='ajax/list/columns',
        view=views_ajax.ProjectListColumnAjaxView.as_view(),
        name='ajax_project_list_columns',
    ),
    path(
        route='ajax/list/roles',
        view=views_ajax.ProjectListRoleAjaxView.as_view(),
        name='ajax_project_list_roles',
    ),
    path(
        route='ajax/star/<uuid:project>',
        view=views_ajax.ProjectStarringAjaxView.as_view(),
        name='ajax_star',
    ),
    path(
        route='ajax/sidebar/<uuid:project>',
        view=views_ajax.SidebarContentAjaxView.as_view(),
        name='ajax_sidebar',
    ),
    path(
        route='ajax/dropdown',
        view=views_ajax.UserDropdownContentAjaxView.as_view(),
        name='ajax_user_dropdown',
    ),
    path(
        route='ajax/user/current',
        view=views_ajax.CurrentUserRetrieveAjaxView.as_view(),
        name='ajax_user_current',
    ),
    path(
        route='ajax/autocomplete/user',
        view=views_ajax.UserAutocompleteAjaxView.as_view(),
        name='ajax_autocomplete_user',
    ),
    path(
        route='ajax/autocomplete/user/redirect',
        view=views_ajax.UserAutocompleteRedirectAjaxView.as_view(
            create_field='user'
        ),
        name='ajax_autocomplete_user_redirect',
    ),
]

# REST API views
urls_api = [
    path(
        route='api/list',
        view=views_api.ProjectListAPIView.as_view(),
        name='api_project_list',
    ),
    path(
        route='api/retrieve/<uuid:project>',
        view=views_api.ProjectRetrieveAPIView.as_view(),
        name='api_project_retrieve',
    ),
    path(
        route='api/create',
        view=views_api.ProjectCreateAPIView.as_view(),
        name='api_project_create',
    ),
    path(
        route='api/update/<uuid:project>',
        view=views_api.ProjectUpdateAPIView.as_view(),
        name='api_project_update',
    ),
    path(
        route='api/roles/create/<uuid:project>',
        view=views_api.RoleAssignmentCreateAPIView.as_view(),
        name='api_role_create',
    ),
    path(
        route='api/roles/update/<uuid:roleassignment>',
        view=views_api.RoleAssignmentUpdateAPIView.as_view(),
        name='api_role_update',
    ),
    path(
        route='api/roles/destroy/<uuid:roleassignment>',
        view=views_api.RoleAssignmentDestroyAPIView.as_view(),
        name='api_role_destroy',
    ),
    path(
        route='api/roles/owner-transfer/<uuid:project>',
        view=views_api.RoleAssignmentOwnerTransferAPIView.as_view(),
        name='api_role_owner_transfer',
    ),
    path(
        route='api/invites/list/<uuid:project>',
        view=views_api.ProjectInviteListAPIView.as_view(),
        name='api_invite_list',
    ),
    path(
        route='api/invites/create/<uuid:project>',
        view=views_api.ProjectInviteCreateAPIView.as_view(),
        name='api_invite_create',
    ),
    path(
        route='api/invites/revoke/<uuid:projectinvite>',
        view=views_api.ProjectInviteRevokeAPIView.as_view(),
        name='api_invite_revoke',
    ),
    path(
        route='api/invites/resend/<uuid:projectinvite>',
        view=views_api.ProjectInviteResendAPIView.as_view(),
        name='api_invite_resend',
    ),
    path(
        route='api/settings/retrieve/<uuid:project>',
        view=views_api.ProjectSettingRetrieveAPIView.as_view(),
        name='api_project_setting_retrieve',
    ),
    path(
        route='api/settings/set/<uuid:project>',
        view=views_api.ProjectSettingSetAPIView.as_view(),
        name='api_project_setting_set',
    ),
    path(
        route='api/settings/retrieve/user',
        view=views_api.UserSettingRetrieveAPIView.as_view(),
        name='api_user_setting_retrieve',
    ),
    path(
        route='api/settings/set/user',
        view=views_api.UserSettingSetAPIView.as_view(),
        name='api_user_setting_set',
    ),
    path(
        route='api/users/list',
        view=views_api.UserListAPIView.as_view(),
        name='api_user_list',
    ),
    path(
        route='api/users/current',
        view=views_api.CurrentUserRetrieveAPIView.as_view(),
        name='api_user_current',
    ),
    path(
        route='api/remote/get/<str:secret>',
        view=views_api.RemoteProjectGetAPIView.as_view(),
        name='api_remote_get',
    ),
]

urlpatterns = urls_ui + urls_ajax + urls_api
