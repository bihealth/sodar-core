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
        users = User.objects.all().order_by('username')
        res = [
            {
                'user_html': get_user_html(u, request),
                'name': u.name,
                'email': u.email,
                'date_joined': localtime(u.date_joined).strftime('%Y-%m-%d'),
            }
            for u in users
        ]
        return Response(res, 200)
