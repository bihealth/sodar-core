from django.urls import path

from siteinfo import views

app_name = 'siteinfo'

urlpatterns = [
    path(
        route='info',
        view=views.SiteInfoView.as_view(),
        name='info',
    ),
]
