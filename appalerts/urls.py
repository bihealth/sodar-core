from django.urls import path

from appalerts import views, views_ajax

app_name = 'appalerts'

urlpatterns = [
    path(
        route='list',
        view=views.AppAlertListView.as_view(),
        kwargs={'status': 'active'},
        name='list',
    ),
    path(
        route='list/dismissed',
        view=views.AppAlertListView.as_view(),
        kwargs={'status': 'dismissed'},
        name='list_dismissed',
    ),
    path(
        route='redirect/<uuid:appalert>',
        view=views.AppAlertLinkRedirectView.as_view(),
        name='redirect',
    ),
    path(
        route='ajax/status',
        view=views_ajax.AppAlertStatusAjaxView.as_view(),
        name='ajax_status',
    ),
    path(
        route='ajax/dismiss/<uuid:appalert>',
        view=views_ajax.AppAlertDismissAjaxView.as_view(),
        name='ajax_dismiss',
    ),
    path(
        route='ajax/dismiss/all',
        view=views_ajax.AppAlertDismissAjaxView.as_view(),
        name='ajax_dismiss_all',
    ),
]
