"""Ajax views for the adminalerts app"""

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseBadRequest

from rest_framework.response import Response
from rest_framework.views import APIView

# Projectroles dependency
from projectroles.views_ajax import SODARBasePermissionAjaxView

from adminalerts.models import AdminAlert, AdminAlertDismissal


class AdminAlertActiveToggleAjaxView(SODARBasePermissionAjaxView):
    """AdminAlert acivation toggling Ajax view"""

    permission_required = 'adminalerts.update_alert'
    http_method_names = ['post']

    def post(self, request, **kwargs):
        alert_uuid = kwargs.get('adminalert', None)
        try:
            alert = AdminAlert.objects.get(sodar_uuid__exact=alert_uuid)
        except AdminAlert.DoesNotExist:
            return HttpResponseBadRequest()
        alert.active = not alert.active
        alert.save()
        return Response({'is_active': alert.active}, status=200)


class AdminAlertDismissAjaxView(APIView):
    """View to dismiss an AdminAlert for a specific user"""

    http_method_names = ['get']

    def get(self, request, **kwargs):
        if not request.user or request.user == AnonymousUser():
            return Response(status=200)
        alert_uuid = kwargs.get('adminalert', None)
        try:
            alert = AdminAlert.objects.get(sodar_uuid__exact=alert_uuid)
        except AdminAlert.DoesNotExist:
            return HttpResponseBadRequest()
        AdminAlertDismissal.objects.get_or_create(
            user=request.user, alert=alert
        )
        return Response(status=200)
