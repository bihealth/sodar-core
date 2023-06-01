"""UI views for the appalerts app"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, View
from django.conf import settings

# Projectroles dependency
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
)

from appalerts.models import AppAlert


class AppAlertListView(LoginRequiredMixin, LoggedInPermissionMixin, ListView):
    """App alert list view"""

    permission_required = 'appalerts.view_alerts'
    template_name = 'appalerts/alert_list.html'

    def get_queryset(self):
        status = self.kwargs.get('status', 'active')
        if status == 'dismissed':
            return AppAlert.objects.filter(
                user=self.request.user, active=False
            ).order_by('-pk')
        return AppAlert.objects.filter(
            user=self.request.user, active=True
        ).order_by('-pk')

    def get_paginate_by(self, queryset):
        status = self.kwargs.get('status', 'active')
        if status == 'dismissed':
            return getattr(settings, 'DEFAULT_PAGINATION', 15)
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dismissed'] = (
            True if self.kwargs.get('status') == 'dismissed' else False
        )
        return context


class AppAlertLinkRedirectView(
    LoginRequiredMixin, LoggedInPermissionMixin, View
):
    """View for redirecting to alert link and dismissing alert"""

    permission_required = 'appalerts.view_alerts'

    def _handle_error(self, msg):
        messages.error(self.request, msg)
        return redirect(reverse('appalerts:list'))

    def get(self, request, **kwargs):
        alert = AppAlert.objects.filter(
            sodar_uuid=kwargs.get('appalert')
        ).first()
        # Handle errors
        if not alert:
            return self._handle_error('Alert not found.')
        if request.user != alert.user:
            return self._handle_error('Alert assigned to different user.')
        if not alert.url:
            return self._handle_error('No URL found for alert.')
        # All OK = dismiss and redirect
        alert.active = False
        alert.save()
        return redirect(alert.url)
