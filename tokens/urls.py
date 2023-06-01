from django.urls import path

from tokens import views

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
]
