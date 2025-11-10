from django.urls import path

from tokens import views, views_api

app_name = 'tokens'

urlpatterns = [
    path(
        route='',
        view=views.UserTokenListView.as_view(),
        name='list',
    ),
    path(
        route='create/',
        view=views.UserTokenCreateView.as_view(),
        name='create',
    ),
    path(
        route='delete/<str:pk>',
        view=views.UserTokenDeleteView.as_view(),
        name='delete',
    ),
    path(
        route='api/login',
        view=views_api.TokenCreateLoginAPIView.as_view(),
        name='api_login',
    ),
]
