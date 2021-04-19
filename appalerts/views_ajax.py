"""Ajax API views for the appalerts app"""

from rest_framework.response import Response

# Projectroles dependency
from projectroles.views_ajax import SODARBaseAjaxView

from appalerts.models import AppAlert


class AppAlertDismissAjaxView(SODARBaseAjaxView):
    """View to handle app alert dismissal in UI"""

    permission_required = 'appalerts.view_alerts'

    def post(self, request, **kwargs):
        # HACK: Manually refuse access to anonymous as this view is an exception
        if not request.user or request.user.is_anonymous:
            return Response({'detail': 'Anonymous access denied'}, status=401)

        alert = AppAlert.objects.filter(
            sodar_uuid=kwargs.get('appalert')
        ).first()

        if not alert:
            return Response({'detail': 'Alert not found'}, status=404)
        if not request.user.is_superuser and request.user != alert.user:
            return Response(
                {'detail': 'User lacks permissions to update alert'}, status=403
            )

        alert.active = False
        alert.save()
        return Response({'detail': 'OK'}, status=200)