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
        route='profile/settings/update',
        view=views.UserSettingUpdateView.as_view(),
        name='settings_update',
    ),
]
