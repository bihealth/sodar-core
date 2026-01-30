"""
Transferroles management command for transferring all project roles
to another user.
"""

import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import SODAR_CONSTANTS, Project, RoleAssignment
from projectroles.views import (
    RoleAssignmentDeleteMixin,
    RoleAssignmentModifyMixin,
    RoleAssignmentOwnerTransferMixin,
)

logger = ManagementCommandLogger(__name__)
User = get_user_model()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']

# Local constants
USER_NOT_FOUND_MSG = 'User not found with username: {}'


class Command(
    RoleAssignmentOwnerTransferMixin,
    RoleAssignmentModifyMixin,
    RoleAssignmentDeleteMixin,
    BaseCommand,
):
    help = 'Transfer all project roles to another user.'

    def _transfer_owner(
        self,
        project: Project,
        new_user: User,
        role_as: RoleAssignment,
        p_title: str,
    ) -> bool:
        try:
            with transaction.atomic():
                self.transfer_owner(
                    project=project,
                    new_owner=new_user,
                    old_owner_as=role_as,
                    old_owner_role=None,
                    notify_old=False,
                    notify_new=False,
                )
                logger.info(
                    f'Transferred ownership in {p_title} to {new_user.username}'
                )
                return True
        except Exception as ex:
            logger.error(
                f'Failed to transfer ownership in {p_title} to '
                f'{new_user.username}: {ex}'
            )
            return False

    def _create_role_or_promote(
        self,
        project: Project,
        new_user: User,
        role_as: RoleAssignment,
        p_title: str,
    ):
        new_user_roles = RoleAssignment.objects.filter(
            user=new_user, project=project
        )
        data = {
            'user': new_user,
            'role': role_as.role,
        }
        if new_user_roles.count() == 0:
            # Create the new role
            self.modify_assignment(
                data=data,
                project=project,
                notify=False,
            )
            logger.info(
                f'Created role "{role_as.role}" in {p_title} for '
                f'{new_user.username}'
            )
        else:
            # Promote user to higher role
            assert new_user_roles.count() == 1
            new_user_role = new_user_roles.first()
            if role_as.role.rank < new_user_role.role.rank:
                self.modify_assignment(
                    data=data,
                    project=project,
                    instance=new_user_role,
                    notify=False,
                )
                logger.info(
                    f'Promoted {new_user.username} to role "{role_as.role}" '
                    f'in {p_title}'
                )
            else:
                logger.info(
                    f'Skipping "{role_as.role}" role assignment for '
                    f'{new_user.username} in {p_title}'
                )

    def _transfer_assignment(
        self,
        project: Project,
        new_user: User,
        role_as: RoleAssignment,
        p_title: str,
    ) -> bool:
        try:
            with transaction.atomic():
                self.delete_assignment(role_as, None, False)
                self._create_role_or_promote(
                    project, new_user, role_as, p_title
                )
                return True
        except Exception as ex:
            logger.error(
                f'Failed to transfer role "{role_as.role}" in {p_title} to '
                f'{new_user.username}: {ex}'
            )
            return False

    def add_arguments(self, parser):
        parser.add_argument(
            '-o',
            '--old-user',
            dest='old_user',
            required=True,
            help='User name of user whose roles will be removed',
        )
        parser.add_argument(
            '-n',
            '--new-user',
            dest='new_user',
            required=True,
            help='User name of user who will receive the new roles',
        )
        parser.add_argument(
            '-d',
            '--deactivate',
            dest='deactivate',
            required=False,
            default=False,
            action='store_true',
            help='Deactivate old-user after removing their roles',
        )

    def handle(self, *args, **options):
        if options['old_user'] == options['new_user']:
            logger.error(
                'Same username given for both old and new user: {}'.format(
                    options['old_user']
                )
            )
            sys.exit(1)

        try:
            old_user = User.objects.get(username=options['old_user'])
        except User.DoesNotExist:
            logger.error(USER_NOT_FOUND_MSG.format(options['old_user']))
            sys.exit(1)
        try:
            new_user = User.objects.get(username=options['new_user'])
        except User.DoesNotExist:
            logger.error(USER_NOT_FOUND_MSG.format(options['new_user']))
            sys.exit(1)
        logger.info(
            'Transferring project roles from user "{}" to user "{}"..'.format(
                old_user.username,
                new_user.username,
            )
        )
        old_user_roles = RoleAssignment.objects.filter(user=old_user).order_by(
            'project__full_title'
        )
        if old_user_roles.count() == 0:
            logger.info(f'No roles found for {old_user.username}')
            return

        role_count = 0
        fail_count = 0
        for role_as in old_user_roles:
            project = role_as.project
            p_title = project.get_log_title()
            if project.is_remote():  # Skip remote projects
                logger.debug(f'Skipping remote project: {p_title}')
                continue
            # Owner role reassignment
            if role_as.role.name == PROJECT_ROLE_OWNER:
                update_ok = self._transfer_owner(
                    project, new_user, role_as, p_title
                )
            else:  # Non-owner role transfer
                update_ok = self._transfer_assignment(
                    project, new_user, role_as, p_title
                )
            if update_ok is True:
                role_count += 1
            else:
                fail_count += 1

        if options['deactivate']:
            old_user.is_active = False
            old_user.save()
            logger.info(f'User "{old_user.username}" deactivated')

        logger.info(
            f'Transferred roles from user "{old_user.username}" to user '
            f'"{new_user.username}" ({role_count} OK, {fail_count} failed)'
        )
