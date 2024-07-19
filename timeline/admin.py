from django.contrib import admin

from .models import TimelineEvent, TimelineEventObjectRef, TimelineEventStatus


admin.site.register(TimelineEvent)
admin.site.register(TimelineEventObjectRef)
admin.site.register(TimelineEventStatus)
