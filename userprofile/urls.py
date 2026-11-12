from django.urls import path

from userprofile import views
from userprofile import views_ajax

app_name = 'userprofile'

urls_detail = [
    path(
        route='profile',
        view=views.UserDetailView.as_view(),
        name='detail',
    ),
    path(
        route='profile/<uuid:user>',
        view=views.UserDetailView.as_view(),
        name='detail_public',
    ),
    path(
        route='settings/update',
        view=views.UserAppSettingsView.as_view(),
        name='settings_update',
    ),
    path(
        route='email/create',
        view=views.UserEmailCreateView.as_view(),
        name='email_create',
    ),
    path(
        route='email/verify/<str:secret>',
        view=views.UserEmailVerifyView.as_view(),
        name='email_verify',
    ),
    path(
        route='email/resend/<uuid:sodaruseradditionalemail>',
        view=views.UserEmailVerifyResendView.as_view(),
        name='email_verify_resend',
    ),
    path(
        route='email/delete/<uuid:sodaruseradditionalemail>',
        view=views.UserEmailDeleteView.as_view(),
        name='email_delete',
    ),
]

urls_list = [
    path(route='profiles', view=views.UserListView.as_view(), name='list'),
]

# Ajax API views
urls_ajax = [
    path(
        route='ajax/profiles',
        view=views_ajax.UserListAjaxView.as_view(),
        name='ajax_list',
    ),
]

urlpatterns = urls_detail + urls_list + urls_ajax
