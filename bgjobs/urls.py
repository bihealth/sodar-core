"""
URL configuration for the bgjobs app.

Note that the job detail view is implemented
"""

from django.urls import path

from bgjobs import views

app_name = 'bgjobs'

urlpatterns = [
    # List jobs that the user has access to
    path(
        route='<uuid:project>/list/',
        view=views.ProjectBackgroundJobView.as_view(),
        name='list',
    ),
    # Clear jobs in project owned by the current user
    path(
        route='<uuid:project>/clear/own/',
        view=views.BackgroundJobClearOwnView.as_view(),
        name='clear_own',
    ),
    # Clear jobs in project regardless of the user
    path(
        route='<uuid:project>/clear/all/',
        view=views.BackgroundJobClearAllView.as_view(),
        name='clear_all',
    ),
    # List global background jobs
    path(
        route='list/',
        view=views.GlobalBackgroundJobView.as_view(),
        name='site_list',
    ),
]
