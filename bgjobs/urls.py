"""
URL configuration for the bgjobs app.

Note that the job detail view is implemented
"""

from django.urls import path

from bgjobs import views

app_name = 'bgjobs'

urls_ui_project = [
    # List jobs that the user has access to
    path(
        route='list/<uuid:project>',
        view=views.ProjectBackgroundJobView.as_view(),
        name='list',
    ),
    # Clear jobs in project owned by the current user
    path(
        route='clear/own/<uuid:project>',
        view=views.BackgroundJobClearOwnView.as_view(),
        name='clear_own',
    ),
    # Clear jobs in project regardless of the user
    path(
        route='clear/all/<uuid:project>',
        view=views.BackgroundJobClearAllView.as_view(),
        name='clear_all',
    ),
]

urls_ui_site = [
    # List site background jobs
    path(
        route='list',
        view=views.SiteBackgroundJobView.as_view(),
        name='site_list',
    ),
]

urlpatterns = urls_ui_project + urls_ui_site
