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
PASSWORD = 'password'


class Command(BaseCommand):
    help = (
        'Create fictitious local user accounts for development. The password '
        'for each user will be set as "password".'
    )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            logger.error(
                'DEBUG not enabled, cancelling. Are you attempting to create '
                'development users on a production site?'
            )
            sys.exit(1)
        password = make_password(PASSWORD)
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
