"""URLs for the timeline app"""

from django.conf.urls import url

from timeline import views, views_ajax


app_name = 'timeline'

# UI views
urls_ui = [
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ProjectTimelineView.as_view(),
        name='list_project',
    ),
    url(
        regex=r'^site$',
        view=views.SiteTimelineView.as_view(),
        name='list_site',
    ),
    url(
        regex=r'^(?P<project>[0-9a-f-]+)/(?P<object_model>[\w-]+)/'
        r'(?P<object_uuid>[0-9a-f-]+)$',
        view=views.ProjectObjectTimelineView.as_view(),
        name='list_object',
    ),
    url(
        regex=r'^site/(?P<object_model>[\w-]+)/(?P<object_uuid>[0-9a-f-]+)$',
        view=views.SiteObjectTimelineView.as_view(),
        name='list_object_site',
    ),
]

# Ajax API views
urls_ajax = [
    url(
        regex=r'^ajax/detail/(?P<projectevent>[0-9a-f-]+)$',
        view=views_ajax.ProjectEventDetailAjaxView.as_view(),
        name='ajax_detail_project',
    ),
    url(
        regex=r'^ajax/detail/site/(?P<projectevent>[0-9a-f-]+)$',
        view=views_ajax.SiteEventDetailAjaxView.as_view(),
        name='ajax_detail_site',
    ),
    url(
        regex=r'^ajax/extra/(?P<projectevent>[0-9a-f-]+)$',
        view=views_ajax.ProjectEventExtraAjaxView.as_view(),
        name='ajax_extra_project',
    ),
    url(
        regex=r'^ajax/extra/site/(?P<projectevent>[0-9a-f-]+)$',
        view=views_ajax.SiteEventExtraAjaxView.as_view(),
        name='ajax_extra_site',
    ),
]

urlpatterns = urls_ui + urls_ajax
