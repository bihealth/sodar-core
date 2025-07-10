"""Celery tasks for the samplesheets app"""

import logging

from django.conf import settings

from config.celery import app

from projectroles.app_settings import AppSettingAPI
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.models import RemoteSite, SODAR_CONSTANTS


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']

# Local constants
APP_NAME = 'projectroles'
READ_ONLY_SKIP_MSG = 'Site read-only mode enabled, skipping'


@app.task(bind=True)
def sync_remote_site_task(_self):
    """Synchronize remote project"""
    remote_api = RemoteProjectAPI()
    source_site = RemoteSite.objects.filter(mode=SITE_MODE_SOURCE).first()
    if source_site:
        if app_settings.get(APP_NAME, 'site_read_only'):
            logger.info(READ_ONLY_SKIP_MSG)
            return
        try:
            remote_data = remote_api.get_remote_data(source_site)
            logger.debug(remote_data)
            remote_api.sync_remote_data(source_site, remote_data)
        except Exception as ex:
            logger.error(f'Unable to synchronize {source_site.name}: {ex}')


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET and getattr(
        settings, 'PROJECTROLES_TARGET_SYNC_ENABLE', False
    ):
        sender.add_periodic_task(
            getattr(settings, 'PROJECTROLES_TARGET_SYNC_INTERVAL', 5) * 60,
            sync_remote_site_task.s(),
            name='synchronize_remote_site',
        )
