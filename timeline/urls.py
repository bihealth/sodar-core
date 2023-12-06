"""URLs for the timeline app"""

from django.urls import path

from timeline import views, views_ajax


app_name = 'timeline'

# UI views for project plugin
urls_ui_project = [
    path(
        route='<uuid:project>',
        view=views.ProjectTimelineView.as_view(),
        name='list_project',
    ),
    path(
        route='<uuid:project>/<str:object_model>/<uuid:object_uuid>',
        view=views.ProjectObjectTimelineView.as_view(),
        name='list_object',
    ),
]

# UI views for site app plugin
urls_ui_site = [
    path(route='site', view=views.SiteTimelineView.as_view(), name='list_site'),
    path(
        route='site/<str:object_model>/<uuid:object_uuid>',
        view=views.SiteObjectTimelineView.as_view(),
        name='list_object_site',
    ),
]

# UI views for admin site app plugin
urls_ui_admin = [
    path(
        route='site/all',
        view=views.AdminTimelineView.as_view(),
        name='list_admin',
    ),
]

# Ajax API views
urls_ajax = [
    path(
        route='ajax/detail/<uuid:projectevent>',
        view=views_ajax.ProjectEventDetailAjaxView.as_view(),
        name='ajax_detail_project',
    ),
    path(
        route='ajax/detail/site/<uuid:projectevent>',
        view=views_ajax.SiteEventDetailAjaxView.as_view(),
        name='ajax_detail_site',
    ),
    path(
        route='ajax/extra/<uuid:projectevent>',
        view=views_ajax.ProjectEventExtraAjaxView.as_view(),
        name='ajax_extra_project',
    ),
    path(
        route='ajax/extra/site/<uuid:projectevent>',
        view=views_ajax.SiteEventExtraAjaxView.as_view(),
        name='ajax_extra_site',
    ),
    path(
        route='ajax/extra/status/<uuid:eventstatus>',
        view=views_ajax.EventStatusExtraAjaxView.as_view(),
        name='ajax_extra_status',
    ),
]

urlpatterns = urls_ui_project + urls_ui_site + urls_ui_admin + urls_ajax
