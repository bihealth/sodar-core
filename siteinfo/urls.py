from django.urls import path

from siteinfo import views, views_ajax

app_name = 'siteinfo'

urlpatterns = [
    path(
        route='info',
        view=views.SiteInfoView.as_view(),
        name='info',
    ),
    path(
        route='ajax/stats',
        view=views_ajax.PluginStatisticsAjaxView.as_view(),
        name='ajax_stats',
    ),
]
