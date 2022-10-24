from django.conf.urls import url

from siteinfo import views

app_name = 'siteinfo'

urlpatterns = [
    url(regex=r'^info$', view=views.SiteInfoView.as_view(), name='info')
]
