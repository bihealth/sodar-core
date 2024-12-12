"""Syncremote management command for synchronizing remote projects"""

import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import RemoteSite, SODAR_CONSTANTS
from projectroles.remote_projects import RemoteProjectAPI


logger = ManagementCommandLogger(__name__)


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


class Command(BaseCommand):
    help = 'Synchronizes user and project data from the source site'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        remote_api = RemoteProjectAPI()
        if getattr(settings, 'PROJECTROLES_DISABLE_CATEGORIES', False):
            logger.info(
                'Project categories and nesting disabled, '
                'remote sync disabled'
            )
            sys.exit(0)
        if settings.PROJECTROLES_SITE_MODE != SITE_MODE_TARGET:
            logger.error('Site not in TARGET mode, unable to sync')
            sys.exit(1)
        try:
            source_site = RemoteSite.objects.get(mode=SITE_MODE_SOURCE)
        except RemoteSite.DoesNotExist:
            logger.error('No source site set, unable to sync')
            sys.exit(1)

        if getattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS', False):
            logger.info(
                'PROJECTROLES_ALLOW_LOCAL_USERS=True, will sync '
                'roles for existing local users'
            )
        logger.info(
            'Retrieving data from source site "{}" ({})..'.format(
                source_site.name, source_site.get_url()
            )
        )
        try:
            remote_data = remote_api.get_remote_data(source_site)
        except Exception as ex:
            logger.error(
                'Failed to retrieve data from source site: {}'.format(ex)
            )
            sys.exit(1)

        logger.info('Synchronizing remote data from source site..')
        try:
            remote_api.sync_remote_data(source_site, remote_data)
        except Exception as ex:
            logger.error('Remote sync failed with exception: {}'.format(ex))
            sys.exit(1)
        logger.info('Syncremote command OK')
