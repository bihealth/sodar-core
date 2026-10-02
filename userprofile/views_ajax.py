from django.contrib import auth
from django.utils.timezone import localtime
from rest_framework.response import Response

from projectroles.views_ajax import SODARBasePermissionAjaxView
from projectroles.templatetags.projectroles_common_tags import get_user_html


User = auth.get_user_model()


class UserListAjaxView(SODARBasePermissionAjaxView):
    """Ajax view for retrieving the list of all users"""

    permission_required = 'userprofile.view_list'

    def get(self, request, *args, **kwargs):
        queryset = User.objects.all()
        res = [
            {
                'user_html': get_user_html(obj, request),
                'first_name': obj.first_name,
                'last_name': obj.last_name,
                'email': obj.email,
                'date_joined': localtime(obj.date_joined).strftime('%Y-%m-%d'),
            }
            for obj in queryset
        ]
        return Response(res, 200)
