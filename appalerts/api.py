"""Backend API for the appalerts app"""

from typing import Optional

from djangoplugins.models import Plugin

from appalerts.models import AppAlert, ALERT_LEVELS

# Projectroles dependency
from projectroles.models import Project, SODARUser


class AppAlertAPI:
    """App Alerts backend API"""

    @classmethod
    def get_model(cls) -> type[AppAlert]:
        """
        Return AppAlert model for direct model access.

        :returns: AppAlert class
        """
        return AppAlert

    @classmethod
    def add_alert(
        cls,
        app_name: str,
        alert_name: str,
        user: SODARUser,
        message: str,
        level: str = 'INFO',
        url: Optional[str] = None,
        project: Optional[Project] = None,
    ) -> AppAlert:
        """
        Create an AppAlert.

        :param app_name: Name of app plugin which creates the alert (string)
        :param alert_name: Internal alert name string
        :param user: User object for user receiving the alert
        :param message: Message string (can contain HTML)
        :param level: Alert level string (INFO, SUCCESS, WARNING or DANGER)
        :param url: URL for following up on alert (string, optional)
        :param project: Project the alert belongs to (Project object, optional)
        :raise: ValueError if the plugin is not found or the level is invalid
        :return: AppAlert object
        """
        app_plugin = None  # None = projectroles
        if app_name != 'projectroles':
            try:
                app_plugin = Plugin.objects.get(name=app_name)
            except Plugin.DoesNotExist:
                raise ValueError(f'Plugin not found with name: {app_name}')
        if level not in ALERT_LEVELS:
            raise ValueError(
                f'Invalid level "{level}", accepted values: '
                f'{", ".join(ALERT_LEVELS)}'
            )
        return AppAlert.objects.create(
            app_plugin=app_plugin,
            alert_name=alert_name,
            user=user,
            message=message,
            level=level,
            url=url,
            project=project,
        )

    @classmethod
    def add_alerts(
        cls,
        app_name: str,
        alert_name: str,
        users: list[SODARUser],
        message: str,
        level: str = 'INFO',
        url: Optional[str] = None,
        project: Optional[Project] = None,
    ):
        """
        Create an AppAlert for multiple users.

        :param app_name: Name of app plugin which creates the alert (string)
        :param alert_name: Internal alert name string
        :param users: list of User objects
        :param message: Message string (can contain HTML)
        :param level: Alert level string (INFO, SUCCESS, WARNING or DANGER)
        :param url: URL for following up on alert (string, optional)
        :param project: Project the alert belongs to (Project object, optional)
        :raise: ValueError if the plugin is not found or the level is invalid
        """
        for user in users:
            cls.add_alert(
                app_name,
                alert_name,
                user,
                message,
                level,
                url,
                project,
            )
