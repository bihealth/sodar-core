"""Utility functions for the timeline app"""

from projectroles.templatetags.projectroles_common_tags import (
    get_user_badge,
    get_project_badge,
)

from timeline.templatetags.timeline_tags import (
    get_app_badge,
    get_event_description,
)


def get_event_full_description(event, plugin_lookup, extra_class='mr-1'):
    """Get an HTML string giving the full description of a timeline event"""
    components = [get_app_badge(event, plugin_lookup, extra_class=extra_class)]
    if event.user:
        components.append(get_user_badge(event.user, extra_class=extra_class))
    if event.project:
        components.append(
            get_project_badge(event.project, extra_class=extra_class)
        )
    components.append(
        '<span>'
        + get_event_description(event, plugin_lookup).capitalize()
        + '</span>'
    )
    return ' '.join(components)
