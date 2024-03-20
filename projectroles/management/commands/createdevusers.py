"""
Createdevusers management command for creating fictitious local user accounts
for development.
"""

import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from projectroles.management.logging import ManagementCommandLogger


logger = ManagementCommandLogger(__name__)
User = get_user_model()


DEV_USER_NAMES = ['alice', 'bob', 'carol', 'dan', 'erin']
LAST_NAME = 'Example'
EMAIL_DOMAIN = 'example.com'
DEFAULT_PASSWORD = 'sodarpass'


class Command(BaseCommand):
    help = 'Create fictitious local user accounts for development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--password',
            dest='password',
            type=str,
            required=False,
            help='Password to use for created dev users. If not given, the '
            'default password "{}" will be used'.format(DEFAULT_PASSWORD),
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            logger.error(
                'DEBUG not enabled, cancelling. Are you attempting to create '
                'development users on a production instance?'
            )
            sys.exit(1)
        pw = (
            DEFAULT_PASSWORD
            if not options.get('password')
            else options['password']
        )
        password = make_password(pw)
        for u in DEV_USER_NAMES:
            if User.objects.filter(username=u).first():
                logger.info('User "{}" already exists'.format(u))
                continue
            try:
                User.objects.create(
                    username=u,
                    first_name=u.capitalize(),
                    last_name=LAST_NAME,
                    name='{} {}'.format(u.capitalize(), LAST_NAME),
                    email='{}@{}'.format(u, EMAIL_DOMAIN),
                    password=password,
                )
                logger.info('Created user "{}"'.format(u))
            except Exception as ex:
                logger.error(
                    'Exception in creating user "{}": {}'.format(u, ex)
                )
