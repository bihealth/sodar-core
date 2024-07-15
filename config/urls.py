from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from django.views import defaults as default_views


# Projectroles dependency
from projectroles.views import HomeView


urlpatterns = [
    path(route='', view=HomeView.as_view(), name='home'),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # Login and logout
    path(
        route='login/',
        view=auth_views.LoginView.as_view(template_name='users/login.html'),
        name='login',
    ),
    path(route='logout/', view=auth_views.logout_then_login, name='logout'),
    # Auth
    path('api/auth/', include('knox.urls')),
    # Iconify SVG icons
    path('icons/', include('dj_iconify.urls')),
    # Social auth for OIDC support
    path('social/', include('social_django.urls')),
    # Projectroles URLs
    path('project/', include('projectroles.urls')),
    # Admin Alerts URLs
    path('alerts/adm/', include('adminalerts.urls')),
    # App Alerts URLs
    path('alerts/app/', include('appalerts.urls')),
    # Background Jobs URLs
    path('bgjobs/', include('bgjobs.urls')),
    # Filesfolders URLs
    path('files/', include('filesfolders.urls')),
    # django-db-file-storage URLs (obfuscated for users)
    path('DJANGO-DB-FILE-STORAGE-CHANGE-ME/', include('db_file_storage.urls')),
    # Site Info URLs
    path('siteinfo/', include('siteinfo.urls')),
    # SODAR Cache app
    path('cache/', include('sodarcache.urls')),
    # Timeline URLs
    path('timeline/', include('timeline.urls')),
    # API Tokens URLs
    path('tokens/', include('tokens.urls')),
    # User Profile URLs
    path('user/', include('userprofile.urls')),
    # Example project app URLs
    path('examples/project/', include('example_project_app.urls')),
    # Example site app URLs
    path('examples/site/', include('example_site_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            route='400/',
            view=default_views.bad_request,
            kwargs={'exception': Exception('Bad Request!')},
        ),
        path(
            route='403/',
            view=default_views.permission_denied,
            kwargs={'exception': Exception('Permission Denied')},
        ),
        path(
            route='404/',
            view=default_views.page_not_found,
            kwargs={'exception': Exception('Page not Found')},
        ),
        path(route='500/', view=default_views.server_error),
    ]

    urlpatterns += staticfiles_urlpatterns()

    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
