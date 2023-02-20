from django.urls import path

from sodarcache import views_api

app_name = 'sodarcache'

urlpatterns = [
    path(
        route='api/set/<uuid:project>',
        view=views_api.SodarCacheSetAPIView.as_view(),
        name='cache_set',
    ),
    path(
        route='api/get/<uuid:project>',
        view=views_api.SodarCacheGetAPIView.as_view(),
        name='cache_get',
    ),
    path(
        route='api/get/date/<uuid:project>',
        view=views_api.SodarCacheGetDateAPIView.as_view(),
        name='cache_get_date',
    ),
]
