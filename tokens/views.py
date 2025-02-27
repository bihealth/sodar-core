import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic.edit import DeleteView, FormView
from django.views.generic.list import ListView
from django.urls import reverse
from knox.models import AuthToken

# Projectroles dependency
from projectroles.models import RoleAssignment
from projectroles.views import LoggedInPermissionMixin

from tokens.forms import UserTokenCreateForm


# Local constants
TOKEN_CREATE_MSG = 'Token created.'
TOKEN_DELETE_MSG = 'Token deleted.'
TOKEN_CREATE_RESTRICT_MSG = (
    'Token creation is restricted to users with project access'
)


class UserTokenListView(LoginRequiredMixin, LoggedInPermissionMixin, ListView):
    """View for listing and accessing user API tokens"""

    model = AuthToken
    permission_required = 'tokens.view_list'
    template_name = 'tokens/token_list.html'

    def get_queryset(self):
        """Only allow access to this user's query set"""
        return AuthToken.objects.filter(user=self.request.user).order_by('-pk')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.request.user
        context['token_create_enable'] = True
        context['token_create_msg'] = ''
        if (
            not user.is_superuser
            and getattr(settings, 'TOKENS_CREATE_PROJECT_USER_RESTRICT', False)
            and RoleAssignment.objects.filter(user=user).count() == 0
        ):
            context['token_create_enable'] = False
            context['token_create_msg'] = TOKEN_CREATE_RESTRICT_MSG
        return context


class UserTokenCreateView(
    LoginRequiredMixin, LoggedInPermissionMixin, FormView
):
    """View for API token creation"""

    form_class = UserTokenCreateForm
    permission_required = 'tokens.create'
    template_name = 'tokens/token_create.html'

    def form_valid(self, form):
        ttl = datetime.timedelta(hours=form.clean().get('ttl')) or None
        context = self.get_context_data()
        _, context['token'] = AuthToken.objects.create(self.request.user, ttl)
        messages.success(self.request, TOKEN_CREATE_MSG)
        return render(self.request, 'tokens/token_create_success.html', context)


class UserTokenDeleteView(
    LoginRequiredMixin, LoggedInPermissionMixin, DeleteView
):
    """View for API token deletion"""

    model = AuthToken
    permission_required = 'tokens.delete'
    template_name = 'tokens/token_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, TOKEN_DELETE_MSG)
        return reverse('tokens:list')

    def get_queryset(self):
        """Only allow access to this user's query set"""
        return AuthToken.objects.filter(user=self.request.user)
