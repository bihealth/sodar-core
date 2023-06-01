"""URL configuration for the adminalerts app"""

from django.urls import path

import adminalerts.views_ajax
from adminalerts import views

app_name = 'adminalerts'

urls_ui = [
    path(
        route='list',
        view=views.AdminAlertListView.as_view(),
        name='list',
    ),
    path(
        route='detail/<uuid:adminalert>',
        view=views.AdminAlertDetailView.as_view(),
        name='detail',
    ),
    path(
        route='create',
        view=views.AdminAlertCreateView.as_view(),
        name='create',
    ),
    path(
        route='update/<uuid:adminalert>',
        view=views.AdminAlertUpdateView.as_view(),
        name='update',
    ),
    path(
        route='delete/<uuid:adminalert>/delete',
        view=views.AdminAlertDeleteView.as_view(),
        name='delete',
    ),
]

urls_ajax = [
    path(
        route='ajax/active/toggle/<uuid:adminalert>',
        view=adminalerts.views_ajax.AdminAlertActiveToggleAjaxView.as_view(),
        name='ajax_active_toggle',
    ),
]

urlpatterns = urls_ui + urls_ajax
