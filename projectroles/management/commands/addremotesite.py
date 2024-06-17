"""
Addremotesite management command for creating remote sites for remote project
sync
"""

import re
import sys

from django.conf import settings
from django.contrib import auth
from django.core.management.base import BaseCommand

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import RemoteSite, SODAR_CONSTANTS
from projectroles.plugins import get_backend_api


logger = ManagementCommandLogger(__name__)
User = auth.get_user_model()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']


class Command(BaseCommand):
    help = 'Creates a remote site from given arguments'

    def add_arguments(self, parser):
        # RemoteSite Model Argumments
        parser.add_argument(
            '-n',
            '--name',
            dest='name',
            type=str,
            required=True,
            help='Name of the remote site',
        )
        parser.add_argument(
            '-u',
            '--url',
            dest='url',
            type=str,
            required=True,
            help='URL of the remote site. Can be provided without protocol '
            'prefix, defaults to HTTP',
        )
        parser.add_argument(
            '-m',
            '--mode',
            dest='mode',
            type=str,
            required=True,
            help='Mode of the remote site',
        )
        parser.add_argument(
            '-d',
            '--description',
            dest='description',
            type=str,
            required=False,
            default='',
            help='Description of the remote site',
        )
        parser.add_argument(
            '-t',
            '--token',
            dest='secret',
            type=str,
            required=True,
            help='Secret token of the remote site',
        )
        parser.add_argument(
            '-ud',
            '--user-display',
            dest='user_display',
            default=True,
            required=False,
            type=bool,
            help='User display of the remote site',
        )
        parser.add_argument(
            '-o',
            '--owner-modifiable',
            dest='owner_modifiable',
            default=True,
            required=False,
            type=bool,
            help='Allow owners and delegates to modify project access for this '
            'site',
        )
        # Additional Arguments
        parser.add_argument(
            '-s',
            '--suppress-error',
            dest='suppress_error',
            required=False,
            default=False,
            action='store_true',
            help='Suppresses error if site already exists',
        )

    def handle(self, *args, **options):
        timeline = get_backend_api('timeline_backend')
        logger.info('Creating remote site..')
        name = options['name']
        url = options['url']

        # Validate URL
        if not url.startswith('http://') and not url.startswith('https://'):
            url = ''.join(['http://', url])
        pattern = re.compile(r'(http|https)://.*\..*')
        if not pattern.match(url):
            logger.error('Invalid URL "{}"'.format(url))
            sys.exit(1)

        # Validate site mode
        site_mode = options['mode'].upper()
        host_mode = settings.PROJECTROLES_SITE_MODE
        if site_mode not in [SITE_MODE_SOURCE, SITE_MODE_TARGET]:
            logger.error('Invalid mode "{}"'.format(site_mode))
            sys.exit(1)
        if site_mode == host_mode:
            logger.error('Attempting to create site with the same mode as host')
            sys.exit(1)

        # Validate whether site exists
        name_exists = RemoteSite.objects.filter(name=name).count()
        url_exists = RemoteSite.objects.filter(url=url).count()
        if name_exists or url_exists:
            err_msg = 'Remote site exists with {} "{}"'.format(
                'name' if name_exists else 'URL', name if name_exists else url
            )
            if not options['suppress_error']:
                logger.error(err_msg)
                sys.exit(1)
            else:
                logger.info(err_msg)
                sys.exit(0)

        create_kw = {
            'name': name,
            'url': url,
            'mode': site_mode,
            'description': options['description'],
            'secret': options['secret'],
            'user_display': options['user_display'],
            'owner_modifiable': options['owner_modifiable'],
        }
        site = RemoteSite.objects.create(**create_kw)

        if timeline:
            tl_event = timeline.add_event(
                project=None,
                app_name='projectroles',
                user=None,
                event_name='{}_site_create'.format(site_mode.lower()),
                description='create {} remote site {{{}}} via management '
                'command'.format(site_mode.lower(), 'remote_site'),
                classified=True,
                status_type=timeline.TL_STATUS_OK,
                extra_data=create_kw,
            )
            tl_event.add_object(obj=site, label='remote_site', name=site.name)
        logger.info(
            'Created remote site "{}" with mode {}'.format(site.name, site.mode)
        )
