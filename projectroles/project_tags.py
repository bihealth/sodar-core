"""Functions for project tagging/starring in the projectroles app"""
# NOTE: This can be expanded to include other types of tags later on

from projectroles.app_settings import AppSettingAPI


app_settings = AppSettingAPI()


def get_tag_state(project, user):
    """Return True if project is starred"""
    return app_settings.get('projectroles', 'project_star', project, user)


def set_tag_state(project, user, star=True):
    """Creating Star in app_setting"""
    app_settings.set(
        app_name='projectroles',
        setting_name='project_star',
        value=star,
        project=project,
        user=user,
        validate=False,
    )
