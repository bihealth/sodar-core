"""Celery tasks for the samplesheets app"""

import logging

from django.conf import settings

from config.celery import app

# Projectroles dependency
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.constants import SODAR_CONSTANTS
from projectroles.models import RemoteSite


remote_api = RemoteProjectAPI()
logger = logging.getLogger(__name__)

# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


@app.task(bind=True)
def sync_remote_site(_self, target_site_uuid):
    """Synchronise remote project"""
    source_site = RemoteSite.objects.filter(mode=SITE_MODE_SOURCE).first()
    target_site = RemoteSite.objects.filter(sodar_uuid=target_site_uuid).first()
    if source_site:
        try:
            remote_data = remote_api.get_remote_data(source_site)
            remote_api.sync_remote_data(target_site, remote_data)
        except Exception as ex:
            logger.error(
                'Unable to synchronize {}: {}'.format(source_site.name, ex),
            )


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET and getattr(
        settings, 'PROJECTROLES_TARGET_SYNC_ENABLE', False
    ):
        sender.add_periodic_task(
            getattr(settings, 'PROJECTROLES_TARGET_SYNC_INTERVAL', 5) * 60,
            sync_remote_site.s(),
            name='synchronise_remote_site',
        )
