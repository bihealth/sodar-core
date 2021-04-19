"""UI views for the appalerts app"""

from django.views.generic import ListView

# Projectroles dependency
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
)

from appalerts.models import AppAlert


class AppAlertListView(LoginRequiredMixin, LoggedInPermissionMixin, ListView):
    """App alert list view"""

    permission_required = 'projectroles.view_app_alerts'
    template_name = 'appalerts/alert_list.html'

    def get_queryset(self):
        return AppAlert.objects.filter(
            user=self.request.user, active=True
        ).order_by('-pk')
