from django.conf.urls import url

from appalerts import views

app_name = 'appalerts'

urlpatterns = [
    url(
        regex=r'^list$',
        view=views.AppAlertListView.as_view(),
        name='list',
    ),
]
