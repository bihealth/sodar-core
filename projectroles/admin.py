from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    AppSetting,
    ProjectInvite,
)


# Local constants
SODAR_USER_FIELDSET = (('SODAR Core', {'fields': ('enable_update',)}),)


# Register models --------------------------------------------------------------


admin.site.register(Project)
admin.site.register(Role)
admin.site.register(RoleAssignment)
admin.site.register(AppSetting)
admin.site.register(ProjectInvite)


# Default user admin -----------------------------------------------------------


class SODARUserAdmin(AuthUserAdmin):
    """
    Base implementation of SODAR user admin. Use or extend this on your SODAR
    Core based site.
    """

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (('User profile', {'fields': ('name',)}),)
        + AuthUserAdmin.fieldsets
        + SODAR_USER_FIELDSET
    )
    list_display = ('username', 'name', 'is_superuser')
    search_fields = ['name']
