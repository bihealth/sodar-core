from django.contrib import auth
from django.utils.timezone import localtime
from rest_framework.response import Response

from projectroles.views_ajax import SODARBasePermissionAjaxView


User = auth.get_user_model()


class UserListAjaxView(SODARBasePermissionAjaxView):
    """Ajax view for retrieving the list of all users"""

    permission_required = 'userprofile.view_list'

    def get(self, request, *args, **kwargs):
        queryset = User.objects.values()
        res = [
            {
                'username': obj['username'],
                'first_name': obj['first_name'],
                'last_name': obj['last_name'],
                'email': obj['email'],
                'is_active': obj['is_active'],
                'date_joined': localtime(obj['date_joined']).strftime(
                    '%Y-%m-%d %H:%M:%S'
                ),
                'sodar_uuid': str(obj['sodar_uuid']),
            }
            for obj in queryset
        ]
        return Response(res, 200)
