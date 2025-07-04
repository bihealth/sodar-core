"""Batchupdateroles management command for updating user roles in batch"""

import sys

from email.utils import parseaddr

from django.conf import settings
from django.contrib import auth
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from django.utils import timezone

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import (
    Project,
    Role,
    ProjectInvite,
    SODARUser,
    SODAR_CONSTANTS,
)
from projectroles.views import RoleAssignmentModifyMixin, ProjectInviteMixin
from projectroles.utils import build_secret


logger = ManagementCommandLogger(__name__)
User = auth.get_user_model()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']


# HACK for issue #612
class MockRequest(HttpRequest):
    scheme = 'http'

    def mock_scheme(self, host):
        self.scheme = host.scheme

    def scheme(self):  # noqa
        return self.scheme


class Command(RoleAssignmentModifyMixin, ProjectInviteMixin, BaseCommand):
    help = 'Batch updates project roles and sends invites'

    roles = None
    owner_role = None
    del_role = None
    issuer = None
    update_count = 0
    invite_count = 0
    request = None

    # Internal helpers ---------------------------------------------------------

    def _make_request(self) -> HttpRequest:
        """
        Make HttpRequest to supply to view-based handlers.

        :return: HttpRequest object
        """
        host = settings.SODAR_API_DEFAULT_HOST
        request = MockRequest()
        request.mock_scheme(host)
        request.META['HTTP_HOST'] = host.hostname
        if host.port:
            request.META['HTTP_HOST'] += ':' + str(host.port)
        request.user = self.issuer
        return request

    def _update_role(self, project: Project, user: SODARUser, role: Role):
        """
        Handle role update for an existing user.

        :param project: Project object
        ;param user: SODARUser object
        :param role: Role object
        """
        logger.info(f'Updating role of user {user.username} to {role.name}..')
        role_as = project.get_role(user)
        if role_as and role_as.role == self.owner_role:
            logger.warning(
                'Skipping as ownership transfer is not permitted here'
            )
            return
        elif role_as and role_as.role == role:
            logger.info('Skipping as role already exists for user')
            return
        elif (
            role_as
            and role_as.project != project
            and role_as.role.rank > role.rank
        ):
            logger.warning(
                'Skipping as demoting an inherited role is not permitted'
            )
            return
        self.modify_assignment(
            data={'user': user, 'role': role},
            request=self.request,
            project=project,
            instance=role_as,
        )
        self.update_count += 1

    def _invite_user(self, email: str, project: Project, role: Role):
        """
        Create and send user for user not yet in system.

        :param email: String
        :param project: Project object
        :param role: Role object
        """
        logger.info(
            f'Creating and sending invite to {email} for role {role.name}..'
        )
        invite = ProjectInvite.objects.filter(
            email=email,
            project=project,
            active=True,
            date_expire__gte=timezone.now(),
        ).first()
        if invite:
            logger.info('Invite already exists for user in project')
            return
        invite = ProjectInvite.objects.create(
            email=email,
            project=project,
            role=role,
            issuer=self.issuer,
            secret=build_secret(),
        )
        self.handle_invite(invite, self.request, add_message=False)
        self.invite_count += 1

    def _handle_list_row(self, project: Project, role_name: str, email: str):
        """
        Handle row in CSV list.

        :param project: Project object
        :param role_name: String
        :param email: String
        """
        if role_name not in self.roles:
            raise Exception(f'Unknown role: "{role_name}"')
        elif role_name == SODAR_CONSTANTS['PROJECT_ROLE_OWNER']:
            raise Exception(
                'Ownership transfer not permitted in this operation, '
                'use appropriate UI or REST API endpoint'
            )
        role = self.roles[role_name]
        if not parseaddr(email)[1]:
            raise Exception(f'Invalid email: "{email}"')

        users = User.objects.filter(email=email)
        if users.count() > 1:
            logger.warning(
                f'Skipping due to multiple user accounts found for email '
                f'"{email}"'
            )
            return
        user = users.first()
        del_limit = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)

        if (
            role == self.del_role
            and del_limit != 0
            and len(project.get_delegates(inherited=False)) >= del_limit
        ):
            raise Exception(f'Delegate limit of {del_limit} has been reached')

        elif role == self.del_role and not self.issuer.has_perm(
            'projectroles.update_project_delegate', project
        ):
            raise Exception(
                'Issuer lacks perms to update delegates in this project'
            )

        # Update role for existing user in the system
        if user:
            try:
                self._update_role(project, user, role)
            except Exception as ex:
                raise Exception(f'Exception raised by _update_role(): {ex}')
        # Invite user not yet in the system
        else:
            try:
                self._invite_user(email, project, role)
            except Exception as ex:
                raise Exception(f'Exception raised by _invite_user(): {ex}')

    # Command ------------------------------------------------------------------

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--file',
            dest='file',
            type=str,
            required=True,
            help='Semicolon separated file with project UUID, email and role '
            'columns',
        )
        parser.add_argument(
            '-i',
            '--issuer',
            dest='issuer',
            type=str,
            required=False,
            help='User name of issuing user (optional)',
        )

    def handle(self, *args, **options):
        logger.info('Batch updating project roles and/or sending invites..')
        logger.debug('File = {}'.format(options['file']))
        logger.debug('Issuer = {}'.format(options['issuer']))
        if (
            settings.PROJECTROLES_SITE_MODE == 'TARGET'
            and not settings.PROJECTROLES_TARGET_CREATE
        ):
            logger.error(
                'Operation not permitted on a target site without the ability '
                'to create local projects, aborting..'
            )
            sys.exit(1)

        if options['issuer']:
            self.issuer = User.objects.filter(
                username=options['issuer']
            ).first()
        else:
            self.issuer = User.objects.filter(
                username=settings.PROJECTROLES_DEFAULT_ADMIN
            ).first()

        if not self.issuer:
            logger.error(
                'Issuer not found with username "{}"'.format(options['issuer'])
            )
            sys.exit(1)

        file = options['file']
        try:
            with open(file, 'r') as f:
                file_data = [d for d in (line.strip() for line in f) if d]
        except Exception as ex:
            logger.error(f'Unable to read file: {ex}')
            sys.exit(1)

        # Validate file
        row_num = 1
        for d in file_data:
            ds = d.split(';')
            if len(ds) != 3 or len(ds[0]) != 36 or '@' not in ds[1]:
                logger.error(f'Invalid data in CSV file on row {row_num}')
                sys.exit(1)
            row_num += 1

        self.roles = {r.name: r for r in Role.objects.all()}
        self.owner_role = self.roles[SODAR_CONSTANTS['PROJECT_ROLE_OWNER']]
        self.del_role = self.roles[SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']]
        self.request = self._make_request()
        project_uuids = list(set([d.split(';')[0] for d in file_data]))
        error_count = 0

        for p_uuid in project_uuids:
            project = Project.objects.filter(sodar_uuid=p_uuid).first()
            if not project:
                logger.error(f'Project not found with UUID: {p_uuid}')
                continue
            if project.is_remote():
                logger.error(
                    f'Skipping remote {project.type.lower()} '
                    f'{project.get_log_title()}'
                )
                continue

            if not self.issuer.has_perm(
                'projectroles.update_project_members', project
            ) or not self.issuer.has_perm('projectroles.invite_users', project):
                logger.error(
                    f'Skipping project, issuer {self.issuer.username} lacks '
                    f'perms to update or invite members'
                )
                continue

            logger.info(
                f'Updating roles in {project.type.lower()} '
                f'{project.get_log_title()}..'
            )
            for ds in [
                d.split(';') for d in file_data if d.split(';')[0] == p_uuid
            ]:
                try:
                    self._handle_list_row(
                        project=project, role_name=ds[2].strip(), email=ds[1]
                    )
                except Exception as ex:
                    logger.error(ex)
                    error_count += 1
                    # if settings.DEBUG:
                    #     raise ex

        logger.info(
            'Update done: {} invite{} sent, {} role{} updated, '
            '{} error{}'.format(
                self.invite_count,
                's' if self.invite_count != 1 else '',
                self.update_count,
                's' if self.update_count != 1 else '',
                error_count,
                's' if error_count != 1 else '',
            )
        )
