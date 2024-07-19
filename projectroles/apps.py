from django.apps import AppConfig


class ProjectrolesConfig(AppConfig):
    name = 'projectroles'

    def ready(self):
        import projectroles.checks  # noqa
        import projectroles.signals  # noqa
