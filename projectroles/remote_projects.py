"""Remote project management utilities for the projectroles app"""

import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import Group
from django.utils import timezone

from projectroles.models import Project, Role, RoleAssignment, RemoteProject, \
    SODAR_CONSTANTS
from projectroles.plugins import get_backend_api


User = auth.get_user_model()
logger = logging.getLogger(__name__)

APP_NAME = 'projectroles'


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_CHOICES = SODAR_CONSTANTS['PROJECT_TYPE_CHOICES']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS[
    'SUBMIT_STATUS_PENDING_TASKFLOW']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
REMOTE_LEVEL_NONE = SODAR_CONSTANTS['REMOTE_LEVEL_NONE']
REMOTE_LEVEL_VIEW_AVAIL = SODAR_CONSTANTS['REMOTE_LEVEL_VIEW_AVAIL']
REMOTE_LEVEL_READ_INFO = SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']


class RemoteProjectAPI:
    """Remote project data handling API"""

    @classmethod
    def get_target_data(cls, target_site):
        """
        Get user and project data to be synchronized into a target site
        :param target_site: RemoteSite object for the target site
        :return: Dict
        """

        sync_data = {'users': {}, 'projects': {}}

        def add_user(user):
            if user.username not in [
                    u['username'] for u in sync_data['users'].values()]:
                sync_data['users'][str(user.sodar_uuid)] = {
                    'username': user.username,
                    'name': user.name,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'groups': [g.name for g in user.groups.all()]}

        def add_parent_categories(category, project_level):
            if category.parent:
                add_parent_categories(category.parent, project_level)

            if str(category.sodar_uuid) not in sync_data['projects'].keys():
                cat_data = {
                    'title': category.title,
                    'type': PROJECT_TYPE_CATEGORY,
                    'parent_uuid': str(category.parent.sodar_uuid) if
                    category.parent else None,
                    'description': category.description,
                    'readme': category.readme.raw}

                if project_level == REMOTE_LEVEL_READ_ROLES:
                    cat_data['level'] = REMOTE_LEVEL_READ_ROLES
                    role_as = category.get_owner()
                    cat_data['roles'] = {}
                    cat_data['roles'][str(role_as.sodar_uuid)] = {
                        'user': role_as.user.username,
                        'role': role_as.role.name}
                    add_user(role_as.user)

                else:
                    cat_data['level'] = REMOTE_LEVEL_READ_INFO

                sync_data['projects'][str(category.sodar_uuid)] = cat_data

        for rp in target_site.projects.all():
            project = rp.get_project()
            project_data = {
                'level': rp.level,
                'title': project.title,
                'type': PROJECT_TYPE_PROJECT}

            # View available projects
            if rp.level == REMOTE_LEVEL_VIEW_AVAIL:
                project_data['available'] = True if project else False

            # Add info
            elif project and rp.level in [
                    REMOTE_LEVEL_READ_INFO, REMOTE_LEVEL_READ_ROLES]:
                project_data['description'] = project.description
                project_data['readme'] = project.readme.raw

                # Add categories
                if project.parent:
                    add_parent_categories(project.parent, rp.level)
                    project_data['parent_uuid'] = str(project.parent.sodar_uuid)

            # If level is READ_ROLES, add categories and roles
            if rp.level in REMOTE_LEVEL_READ_ROLES:
                project_data['roles'] = {}

                for role_as in project.roles.all():
                    project_data['roles'][str(role_as.sodar_uuid)] = {
                        'user': role_as.user.username,
                        'role': role_as.role.name}
                    add_user(role_as.user)

            sync_data['projects'][str(rp.project_uuid)] = project_data

        return sync_data

    @classmethod
    def sync_source_data(cls, site, remote_data, request=None):
        """
        Synchronize remote user and project data into the local Django database
        and return information of additions
        :param site: RemoteSite object for the source site
        :param remote_data: Data returned by get_target_data() in the source
        :param request: Request object (optional)
        :return: Dict with updated remote_data
        :raise: ValueError if user from PROJECTROLES_ADMIN_OWNER is not found
        """

        # Get default owner if remote projects have a local owner
        try:
            default_owner = User.objects.get(
                username=settings.PROJECTROLES_ADMIN_OWNER)

        except User.DoesNotExist:
            error_msg = \
                'Local user "{}" defined in PROJECTROLES_ADMIN_OWNER ' \
                'not found'.format(settings.PROJECTROLES_ADMIN_OWNER)
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Set up timeline and default user
        timeline = get_backend_api('timeline_backend')
        if timeline:
            tl_user = request.user if request else default_owner

        logger.info('Synchronizing data from "{}"..'.format(site.name))

        # Return unchanged data if no projects with READ_ROLES are included
        if not {k: v for k, v in remote_data['projects'].items() if
                v['type'] == PROJECT_TYPE_PROJECT and
                v['level'] == REMOTE_LEVEL_READ_ROLES}.values():
            logger.info('No READ_ROLES access set, nothing to synchronize')
            return remote_data

        def update_obj(obj, data, fields):
            """Update object"""
            for f in [f for f in fields if hasattr(obj, f)]:
                setattr(obj, f, data[f])
            obj.save()
            return obj

        ########
        # Users
        ########

        logger.info('Synchronizing LDAP/AD users..')

        # NOTE: only sync LDAP/AD users
        for sodar_uuid, u in {
                k: v for k, v in remote_data['users'].items() if
                '@' in v['username']}.items():

            # Update existing user
            try:
                user = User.objects.get(username=u['username'])
                updated_fields = []

                for k, v in u.items():
                    if (k not in ['groups', 'sodar_uuid'] and
                            hasattr(user, k) and
                            str(getattr(user, k)) != str(v)):
                        updated_fields.append(k)

                if updated_fields:
                    user = update_obj(user, u, updated_fields)
                    u['status'] = 'updated'

                    logger.info('Updated user: {} ({}): {}'.format(
                        u['username'], sodar_uuid,
                        ', '.join(updated_fields)))

                # Check and update groups
                if sorted([g.name for g in user.groups.all()]) != \
                        sorted(u['groups']):
                    for g in user.groups.all():
                        if g.name not in u['groups']:
                            g.user_set.remove(user)
                            logger.debug(
                                'Removed user {} ({}) from group "{}"'.format(
                                    user.username, user.sodar_uuid, g.name))

                    existing_groups = [g.name for g in user.groups.all()]

                    for g in u['groups']:
                        if g not in existing_groups:
                            group, created = Group.objects.get_or_create(
                                name=g)
                            group.user_set.add(user)
                            logger.debug(
                                'Added user {} ({}) to group "{}"'.format(
                                    user.username, user.sodar_uuid, g))

            # Create new user
            except User.DoesNotExist:
                create_values = {k: v for k, v in u.items() if k != 'groups'}
                user = User.objects.create(**create_values)
                u['status'] = 'created'
                logger.info('Created user: {}'.format(user.username))

                for g in u['groups']:
                    group, created = Group.objects.get_or_create(name=g)
                    group.user_set.add(user)
                    logger.debug('Added user {} ({}) to group "{}"'.format(
                        user.username, user.sodar_uuid, g))

        logger.info('User sync OK')

        ##########################
        # Categories and Projects
        ##########################
        updated_parents = []

        def update_project(uuid, p, remote_data):
            """Create or update project and its parents"""

            def handle_project_error(error_msg, uuid, p, action, remote_data):
                """Add and log project error"""
                logger.error('{} {} "{}" ({}): {}'.format(
                    action.capitalize(), p['type'].lower(), p['title'],
                    uuid, error_msg))
                remote_data['projects'][uuid]['status'] = 'error'
                remote_data['projects'][uuid]['status_msg'] = error_msg
                return remote_data

            # Add/update parents if not yet handled
            if p['parent_uuid'] and p['parent_uuid'] not in updated_parents:
                c = remote_data['projects'][p['parent_uuid']]
                remote_data = update_project(p['parent_uuid'], c, remote_data)
                updated_parents.append(p['parent_uuid'])

            project = None
            parent = None
            action = 'create'

            logger.info('Processing {} "{}" ({})..'.format(
                p['type'].lower(), p['title'], uuid))

            # Get existing project
            try:
                project = Project.objects.get(type=p['type'], sodar_uuid=uuid)
                action = 'update'

            except Project.DoesNotExist:
                pass

            # Get parent and ensure it exists
            if p['parent_uuid']:
                try:
                    parent = Project.objects.get(sodar_uuid=p['parent_uuid'])

                except Project.DoesNotExist:
                    # Handle error
                    error_msg = 'Parent {} not found'.format(p['parent_uuid'])
                    remote_data = handle_project_error(
                        error_msg, uuid, p, action, remote_data)
                    return remote_data

            # Update project
            if project:
                updated_fields = []

                for k, v in p.items():
                    if (k not in ['parent', 'sodar_uuid', 'roles', 'readme'] and
                            hasattr(project, k) and
                            str(getattr(project, k)) != str(v)):
                        updated_fields.append(k)

                # README is a special case
                if project.readme.raw != p['readme']:
                    updated_fields.append('readme')

                if updated_fields or project.parent != parent:
                    project = update_obj(project, p, updated_fields)

                    # Manually update parent
                    if parent != project.parent:
                        project.parent = parent
                        project.save()
                        updated_fields.append('parent')

                    remote_data['projects'][uuid]['status'] = 'updated'

                    if timeline:
                        tl_desc = \
                            'update project from remote site ' \
                            '"{{{}}}" ({})'.format(
                                'site', ', '.join(updated_fields))
                        # TODO: Add extra_data
                        tl_event = timeline.add_event(
                            project=project,
                            app_name=APP_NAME,
                            user=tl_user,
                            event_name='remote_project_update',
                            description=tl_desc,
                            status_type='OK')
                        tl_event.add_object(site, 'site', site.name)

                    logger.info('Updated {}: {}'.format(
                        p['type'].lower(), ', '.join(sorted(updated_fields))))

                else:
                    logger.info('Nothing to update')

            # Create new project
            else:
                # Check existing title under the same parent
                try:
                    old_project = Project.objects.get(
                        parent=parent, title=p['title'])

                    # Handle error
                    error_msg = \
                        '{} with the title "{}" exists under the same ' \
                        'parent, unable to create'.format(
                            old_project.type.capitalize(),
                            old_project.title)
                    remote_data = handle_project_error(
                        error_msg, uuid, p, action, remote_data)
                    return remote_data

                except Project.DoesNotExist:
                    pass

                create_fields = ['title', 'description', 'readme']
                create_values = {
                    k: v for k, v in p.items() if k in create_fields}
                create_values['type'] = p['type']
                create_values['parent'] = parent
                create_values['sodar_uuid'] = uuid
                project = Project.objects.create(**create_values)

                remote_data['projects'][uuid]['status'] = 'created'

                if timeline:
                    tl_event = timeline.add_event(
                        project=project,
                        app_name=APP_NAME,
                        user=tl_user,
                        event_name='remote_project_create',
                        description='create project from remote site {site}',
                        status_type='OK')
                    # TODO: Add extra_data
                    tl_event.add_object(site, 'site', site.name)

                logger.info('Created {}'.format(p['type'].lower()))

            # Create/update a RemoteProject object
            try:
                remote_project = RemoteProject.objects.get(
                    site=site, project_uuid=project.sodar_uuid)
                remote_project.level = p['level']
                remote_project.project = project
                remote_project.date_access = timezone.now()
                remote_action = 'updated'

            except RemoteProject.DoesNotExist:
                remote_project = RemoteProject.objects.create(
                    site=site,
                    project_uuid=project.sodar_uuid,
                    project=project,
                    level=p['level'],
                    date_access=timezone.now())
                remote_action = 'created'

            logger.debug('{} RemoteProject {}'.format(
                remote_action.capitalize(), remote_project.sodar_uuid))

            # Skip the rest if not updating roles
            if 'level' in p and p['level'] != REMOTE_LEVEL_READ_ROLES:
                return remote_data

            # Create/update roles
            # NOTE: Only update AD/LDAP user roles and local owner roles
            # TODO: Refactor this
            for r_uuid, r in {
                    k: v for k, v in p['roles'].items() if
                    '@' in v['user'] or
                    v['role'] == PROJECT_ROLE_OWNER}.items():
                # Ensure the Role exists
                try:
                    role = Role.objects.get(name=r['role'])

                except Role.DoesNotExist:
                    error_msg = \
                        'Role object "{}" not found (assignment {})'.format(
                            r['role'], r_uuid)
                    logger.error(error_msg)
                    remote_data[
                        'projects'][project.sodar_uuid]['roles'][r_uuid][
                        'status'] = 'error'
                    remote_data[
                        'projects'][project.sodar_uuid]['roles'][r_uuid][
                        'status_msg'] = error_msg
                    continue

                # If role is "project owner" for a non-LDAP user, get
                # the default local user instead
                if r['role'] == PROJECT_ROLE_OWNER and '@' not in r['user']:
                    role_user = default_owner

                    # Notify of assigning role to default owner
                    status_msg = \
                        'Non-LDAP/AD user "{}" set as owner, assigning role ' \
                        'to user "{}"'.format(r['user'], default_owner.username)

                    remote_data['projects'][uuid]['roles'][
                        r_uuid]['user'] = default_owner.username
                    remote_data['projects'][uuid]['roles'][
                        r_uuid]['status_msg'] = status_msg
                    logger.info(status_msg)

                else:
                    role_user = User.objects.get(username=r['user'])

                # Update RoleAssignment if it exists and is changed
                as_updated = False
                role_query = {'project__sodar_uuid': project.sodar_uuid}

                if r['role'] == PROJECT_ROLE_OWNER:
                    role_query['role__name'] = PROJECT_ROLE_OWNER

                else:
                    role_query['user'] = role_user

                try:
                    old_as = RoleAssignment.objects.get(**role_query)

                except RoleAssignment.DoesNotExist:
                    old_as = None

                # Owner updating
                if old_as and r['role'] == PROJECT_ROLE_OWNER:
                    # Update user or local admin user
                    if (('@' in r['user'] and old_as.user != role_user) or
                            (role_user == default_owner and
                             project.get_owner().user != default_owner)):
                        as_updated = True

                        # Delete existing role of the new owner if it exists
                        try:
                            RoleAssignment.objects.get(
                                project__sodar_uuid=project.sodar_uuid,
                                user=role_user).delete()
                            logger.debug(
                                'Deleted existing owner role from '
                                'user "{}"'.format(role_user.username))

                        except RoleAssignment.DoesNotExist:
                            pass

                # Updating of other roles
                elif (old_as and r['role'] != PROJECT_ROLE_OWNER and
                        old_as.role != role):
                    as_updated = True

                if as_updated:
                    old_as.role = role
                    old_as.user = role_user
                    old_as.save()
                    remote_data[
                        'projects'][str(project.sodar_uuid)]['roles'][
                        r_uuid]['status'] = 'updated'

                    if timeline:
                        tl_desc = \
                            'update role to "{}" for {{{}}} from site ' \
                            '{{{}}}'.format(role.name, 'user', 'site')
                        tl_event = timeline.add_event(
                            project=project,
                            app_name=APP_NAME,
                            user=tl_user,
                            event_name='remote_role_update',
                            description=tl_desc,
                            status_type='OK')
                        tl_event.add_object(
                            role_user, 'user', role_user.username)
                        tl_event.add_object(site, 'site', site.name)

                    logger.info('Updated role {}: {} = {}'.format(
                        r_uuid, role_user.username, role.name))

                # Create a new RoleAssignment
                elif not old_as:
                    role_values = {
                        'sodar_uuid': r_uuid,
                        'project': project,
                        'role': role,
                        'user': role_user}
                    RoleAssignment.objects.create(**role_values)

                    remote_data[
                        'projects'][str(project.sodar_uuid)]['roles'][r_uuid][
                        'status'] = 'created'

                    if timeline:
                        tl_desc = \
                            'add role "{}" for {{{}}} from site {{{}}}'.format(
                                role.name, 'user', 'site')
                        tl_event = timeline.add_event(
                            project=project,
                            app_name=APP_NAME,
                            user=tl_user,
                            event_name='remote_role_create',
                            description=tl_desc,
                            status_type='OK')
                        tl_event.add_object(
                            role_user, 'user', role_user.username)
                        tl_event.add_object(site, 'site', site.name)

                    logger.info('Created role {}: {} -> {}'.format(
                        r_uuid, role_user.username, role.name))

            # Remove deleted user roles
            current_users = [v['user'] for k, v in p['roles'].items()]

            deleted_roles = RoleAssignment.objects.filter(
                project=project).exclude(
                    role__name=PROJECT_ROLE_OWNER).exclude(
                        user__username__in=current_users)
            deleted_count = deleted_roles.count()

            if deleted_count > 0:
                deleted_users = sorted([r.user.username for r in deleted_roles])

                for del_as in deleted_roles:
                    del_user = del_as.user
                    del_role = del_as.role
                    del_uuid = str(del_as.sodar_uuid)
                    del_as.delete()

                    remote_data['projects'][uuid]['roles'][del_uuid] = {
                        'user': del_user.username,
                        'role': del_role.name,
                        'status': 'deleted'}

                    if timeline:
                        tl_desc = \
                            'remove role "{}" from {{{}}} by site ' \
                            '{{{}}}'.format(del_role.name, 'user', 'site')
                        tl_event = timeline.add_event(
                            project=project,
                            app_name=APP_NAME,
                            user=tl_user,
                            event_name='remote_role_delete',
                            description=tl_desc,
                            status_type='OK')
                        tl_event.add_object(del_user, 'user', del_user.username)
                        tl_event.add_object(site, 'site', site.name)

                logger.info(
                    'Deleted {} removed role{} for: {}'.format(
                        deleted_count,
                        's' if deleted_count != 1 else '',
                        ', '.join(deleted_users)))

            return remote_data

        # Update projects
        logger.info('Synchronizing projects..')

        for sodar_uuid, p in {
                k: v for k, v in remote_data['projects'].items() if
                v['type'] == PROJECT_TYPE_PROJECT and
                v['level'] == REMOTE_LEVEL_READ_ROLES}.items():
            remote_data = update_project(sodar_uuid, p, remote_data)

        logger.info('Synchronization OK')
        return remote_data