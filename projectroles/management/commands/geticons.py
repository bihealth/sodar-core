"""Geticons management command for retrieving icons for iconify"""

import os

import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

from projectroles.management.logging import ManagementCommandLogger


logger = ManagementCommandLogger(__name__)


# Local constants
JSON_URL = (
    'https://raw.githubusercontent.com/iconify/collections-json/'
    'master/collections.json'
)
COLL_URL = (
    'https://raw.githubusercontent.com/iconify/collections-json/'
    'master/json/{id}.json'
)


class Command(BaseCommand):
    help = 'Retrieves or updates JSON Iconify icons'

    def _download(self, url: str, base_path: str, file_name: str):
        """
        Download file.

        :param url: URL to file
        :param base_path: Base path in local file system
        :param file_name: File name
        """
        logger.debug(f'Downloading "{file_name}"..')
        response = urllib.request.urlopen(url)
        with open(os.path.join(base_path, file_name), 'wb') as f:
            f.write(response.read())
        logger.info(f'Download of "{file_name}" OK')

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--collections',
            dest='collections',
            nargs='+',
            required=False,
            help='Additional collection IDs to retrieve',
        )
        parser.add_argument(
            '-p',
            '--path',
            dest='path',
            type=str,
            required=False,
            help='Base path if not {SITE_PACKAGE}/static/iconify',
        )

    def handle(self, *args, **options):
        logger.info('Retrieving/updating JSON icons..')
        colls = options.get('collections')
        if options.get('path'):
            iconify_path = options['path']
        else:
            iconify_path = os.path.join(settings.APPS_DIR, 'static', 'iconify')
        coll_path = os.path.join(iconify_path, 'json')

        # Create Iconify dirs if not there
        if not os.path.exists(coll_path):
            os.makedirs(coll_path, mode=0o755)
            logger.info(
                f'Created Iconify JSON directories in {settings.SITE_PACKAGE}'
                f'/static'
            )
        else:
            logger.debug('Found existing Iconify JSON dirs')

        # Make sure we have .gitkeep files so large JSONs are not committed
        open(os.path.join(iconify_path, '.gitkeep'), 'a').close()
        open(os.path.join(coll_path, '.gitkeep'), 'a').close()

        # Download collections.json
        self._download(JSON_URL, iconify_path, 'collections.json')
        # Download mdi.json
        self._download(
            COLL_URL.format(id='mdi'),
            coll_path,
            'mdi.json',
        )
        # Download extra collections if set
        if colls:
            logger.info(
                'Downloading {} additional collection{}..'.format(
                    len(colls), 's' if len(colls) != 1 else ''
                )
            )
            for c in colls:
                self._download(
                    COLL_URL.format(id=c),
                    coll_path,
                    c + '.json',
                )
        logger.info('Retrieval/update done')
        logger.info('Remember to run "collectstatic" after updating icons!')
