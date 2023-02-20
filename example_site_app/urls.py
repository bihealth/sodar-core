from django.urls import path

from . import views

app_name = 'example_site_app'

urlpatterns = [
    path(
        route='example',
        view=views.ExampleView.as_view(),
        name='example',
    ),
]
