"""Template tags for the appalerts app"""

from django import template

from appalerts.models import AppAlert


register = template.Library()


@register.simple_tag
def get_alert_message(alert: AppAlert) -> str:
    """
    Return alert message formatted as HTML.

    :param alert: AppAlert object
    :return: String (can contain HTML)
    """
    # NOTE: The built-in "linebreaks" template filter doesn't work here
    if '\n' not in alert.message:
        return alert.message
    return '<br />' + alert.message.replace('\n', '<br />')
