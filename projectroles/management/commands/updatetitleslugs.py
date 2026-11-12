"""
Updatetitleslugs management command to update Project title slugs.
"""

from django.core.management.base import BaseCommand

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import Project
from projectroles.utils import get_display_name


logger = ManagementCommandLogger(__name__)

# Local constants
CHECK_MODE_MSG = 'Check mode enabled, database will not be altered'
FORCE_MODE_MSG = 'Force mode enabled'


class Command(BaseCommand):
    help = 'Updates title slugs for existing Project objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--force',
            dest='force',
            required=False,
            default=False,
            action='store_true',
            help='Overwrite existing values (not recommended outside of '
            'development)',
        )
        parser.add_argument(
            '-c',
            '--check',
            dest='check',
            required=False,
            default=False,
            action='store_true',
            help='Log slugs to be updated without altering the database',
        )

    def handle(self, *args, **options):
        check = options.get('check', False)
        force = options.get('force', False)
        if check:
            logger.info(CHECK_MODE_MSG)
            action = 'found'
        else:
            action = 'updated'
        if force:
            logger.info(FORCE_MODE_MSG)
        count = 0
        for p in Project.objects.order_by('full_title'):
            d_name = get_display_name(p.type)
            if p.is_remote():
                logger.debug(f'Skip remote {d_name}: {p.get_log_title()}')
                continue  # Skip remote projects: title slugs synced from SOURCE
            if force or not p.title_slug:
                msg_mid = f'{d_name} {p.get_log_title()}: '
                try:
                    p.title_slug = p.title
                    if check:
                        p.title_slug = p._get_title_slug()  # noqa
                    else:
                        p.save()
                except Exception as ex:
                    logger.error(f'Error in {msg_mid}{ex}')
                finally:
                    logger.info(
                        f'{action.capitalize()} {msg_mid}{p.title_slug}'
                    )
                    count += 1
        pl = 's' if count != 1 else ''
        logger.info(f'{count} project{pl} {action}.')
