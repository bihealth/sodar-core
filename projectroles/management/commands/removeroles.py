"""
Removeroles management command for removing all roles from a user.
"""

import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import RoleAssignment, SODAR_CONSTANTS
from projectroles.views import (
    RoleAssignmentOwnerTransferMixin,
    RoleAssignmentDeleteMixin,
)

logger = ManagementCommandLogger(__name__)
User = get_user_model()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']

# Local constants
CHECK_MODE_MSG = 'Check mode enabled, database will not be altered'
USER_NOT_FOUND_MSG = 'User not found with username: {}'


class Command(
    RoleAssignmentOwnerTransferMixin, RoleAssignmentDeleteMixin, BaseCommand
):
    help = (
        'Remove all roles from a user. Replace owner roles with given user or '
        'parent owner.'
    )

    @classmethod
    def _get_parent_owner(cls, project, prev_owner):
        """Return assignment for first parent owner who is not previous owner"""
        if not project.parent:
            return None
        parent_owner_as = project.parent.get_owner()
        if parent_owner_as.user != prev_owner:
            return parent_owner_as.user
        return cls._get_parent_owner(project.parent, prev_owner)

    def _reassign_owner(self, project, user, owner, role_as, p_title, check):
        """Reassign owner role"""
        # Fail top category if no new owner is specified
        if not owner and not project.parent:
            logger.warning(
                'Unable to transfer ownership for top level {} {}: no '
                'new owner provided'.format(project.type.lower(), p_title)
            )
            return False
        # Get parent owner if not set
        if not owner:
            owner = self._get_parent_owner(project, user)
        # Fail if alternate parent owner is not found
        if not owner:
            logger.warning(
                'Unable to transfer ownership in {}: no parent owner '
                'found'.format(p_title)
            )
            return False
        if check:
            logger.info(
                'Found role "{}" in {}: transfer to user {}'.format(
                    PROJECT_ROLE_OWNER, p_title, owner.username
                )
            )
            return True
        try:
            with transaction.atomic():
                self.transfer_owner(
                    project=project,
                    new_owner=owner,
                    old_owner_as=role_as,
                    old_owner_role=None,
                    notify_old=False,
                )
                logger.info(
                    'Transferred ownership in {} to {}'.format(
                        p_title, owner.username
                    )
                )
                return True
        except Exception as ex:
            logger.error(
                'Failed to transfer ownership in {} to {}: {}'.format(
                    p_title, owner.username, ex
                )
            )
            return False

    def _remove_role(self, role_as, p_title, check):
        """Remove non-owner role"""
        r_name = role_as.role.name
        if check:
            logger.info(
                'Found role "{}" in {}: to be removed'.format(r_name, p_title)
            )
            return True
        try:
            with transaction.atomic():
                self.delete_assignment(role_as, None, False)
            logger.info('Deleted role "{}" from {}'.format(r_name, p_title))
            return True
        except Exception as ex:
            logger.error(
                'Failed to delete assignment "{}" from {}: '
                '{}'.format(r_name, p_title, ex)
            )
            return False

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--user',
            dest='user',
            required=True,
            help='User name of user whose roles will be removed',
        )
        parser.add_argument(
            '-o',
            '--owner',
            dest='owner',
            required=False,
            help='Set owner role for user by given user name if set, otherwise '
            'set to parent owner',
        )
        parser.add_argument(
            '-c',
            '--check',
            dest='check',
            required=False,
            default=False,
            action='store_true',
            help='Log roles to be removed or transferred without altering the '
            'database',
        )

    def handle(self, *args, **options):
        check = options.get('check', False)
        if check:
            logger.info(CHECK_MODE_MSG)
        if options['user'] == options.get('owner'):
            logger.error(
                'Same username given for both user and new owner: {}'.format(
                    options['user']
                )
            )
            sys.exit(1)
        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            logger.error(USER_NOT_FOUND_MSG.format(options['user']))
            sys.exit(1)
        owner_name = options.get('owner')
        owner = None
        if owner_name:
            try:
                owner = User.objects.get(username=owner_name)
            except User.DoesNotExist:
                logger.error(USER_NOT_FOUND_MSG.format(owner_name))
                sys.exit(1)

        logger.info(
            '{} roles {} user "{}"..'.format(
                'Checking' if check else 'Removing',
                'for' if check else 'from',
                user.username,
            )
        )
        if owner:
            logger.info(
                'New owner for replacing owner roles: {}'.format(owner.username)
            )
        role_count = 0
        fail_count = 0
        roles = RoleAssignment.objects.filter(user=user).order_by(
            'project__full_title'
        )
        if roles.count() == 0:
            logger.info('No roles found')
            return

        for role_as in roles:
            project = role_as.project
            p_title = project.get_log_title()
            if project.is_remote():  # Skip remote projects
                logger.debug('Skipping remote project: {}'.format(p_title))
                continue
            # Owner role reassignment
            if role_as.role.name == PROJECT_ROLE_OWNER:
                update_ok = self._reassign_owner(
                    project, user, owner, role_as, p_title, check
                )
            else:  # Non-owner role removal
                update_ok = self._remove_role(role_as, p_title, check)
            if not check and update_ok is True:
                role_count += 1
            elif not check:
                fail_count += 1
        if check:
            logger.info('Check done')
        else:
            logger.info(
                'Removed roles from user "{}" ({} OK, {} failed)'.format(
                    user.username, role_count, fail_count
                )
            )
