"""Syncgroups management command for synchronizing user groups"""

from django.contrib import auth
from django.core.management.base import BaseCommand
from django.db import transaction

from projectroles.management.logging import ManagementCommandLogger


logger = ManagementCommandLogger(__name__)
User = auth.get_user_model()


class Command(BaseCommand):
    help = 'Synchronizes user groups based on user name'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        logger.info('Synchronizing user groups..')
        with transaction.atomic():
            for user in User.objects.all():
                user.groups.clear()
                user.save()  # Group is updated during save

                if user.groups.count() > 0:
                    logger.info(
                        'Group set: {} -> {}'.format(
                            user.username, user.groups.first().name
                        )
                    )
        logger.info(
            'Synchronized groups for {} users'.format(
                User.objects.all().count()
            )
        )
