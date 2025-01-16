from django.urls import path

from userprofile import views

app_name = 'userprofile'

urlpatterns = [
    path(
        route='profile',
        view=views.UserDetailView.as_view(),
        name='detail',
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
