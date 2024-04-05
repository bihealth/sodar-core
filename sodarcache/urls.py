from django.urls import path

from sodarcache import views_api

app_name = 'sodarcache'

urlpatterns = [
    path(
        route='api/retrieve/<uuid:project>/<str:app_name>/<str:item_name>',
        view=views_api.CacheItemRetrieveAPIView.as_view(),
        name='api_retrieve',
    ),
    path(
        route='api/retrieve/date/<uuid:project>/<str:app_name>/<str:item_name>',
        view=views_api.CacheItemDateRetrieveAPIView.as_view(),
        name='api_retrieve_date',
    ),
    path(
        route='api/set/<uuid:project>/<str:app_name>/<str:item_name>',
        view=views_api.CacheItemSetAPIView.as_view(),
        name='api_set',
    ),
]
