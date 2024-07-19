from django.urls import path, re_path

from example_project_app import views, views_api

app_name = 'example_project_app'

# NOTE: Name of object in kwarg which is a Project or has "project" as a member
#       is expected to correspond 1:1 to the model in question (lowercase ok)!
# NOTE: If referring to a model from another app, notation is "app__model"

urls = [
    re_path(
        r'^(?P<project>[0-9a-f-]+)$',
        view=views.ExampleView.as_view(),
        name='example',
    ),
    # Example view with model from an external app
    re_path(
        r'^ext/(?P<filesfolders__folder>[0-9a-f-]+)$',
        view=views.ExampleView.as_view(),
        name='example_ext_model',
    ),
    # Example view with Django path URL
    path(
        route='path-url/<uuid:project>',
        view=views.ExampleView.as_view(),
        name='example_path_url',
    ),
    # Example view with Django path URL and model from external app
    path(
        route='path-ext/<uuid:filesfolders__folder>',
        view=views.ExampleView.as_view(),
        name='example_path_ext',
    ),
]

urls_api = [
    re_path(
        r'^api/hello/(?P<project>[0-9a-f-]+)$',
        view=views_api.HelloExampleProjectAPIView.as_view(),
        name='example_api_hello',
    )
]

urlpatterns = urls + urls_api
