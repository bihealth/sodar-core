"""
Checkusers management command for checking user status and reporting disabled or
removed users.
"""

import ldap
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from projectroles.management.logging import ManagementCommandLogger


logger = ManagementCommandLogger(__name__)
User = get_user_model()


# Local constants
# UserAccountControl flags for disabled accounts
# TODO: Can we get these from python-ldap and print out exact status?
UAC_DISABLED_VALUES = [
    2,
    514,
    546,
    66050,
    66082,
    262658,
    262690,
    328194,
    328226,
]
UAC_LOCKED_VALUE = 16
# Messages
USER_DISABLED_MSG = 'Disabled'
USER_LOCKED_MSG = 'Locked'
USER_NOT_FOUND_MSG = 'Not found'
USER_OK_MSG = 'OK'


class Command(BaseCommand):
    help = (
        'Check user status and report disabled or removed users. Prints out '
        'user name, real name, email and status as semicolon-separated values.'
    )

    @classmethod
    def _print_result(cls, django_user, msg):
        print(
            '{};{};{};{}'.format(
                django_user.username,
                django_user.get_full_name(),
                django_user.email,
                msg,
            )
        )

    @classmethod
    def _get_setting_prefix(cls, primary):
        return 'AUTH_LDAP{}_'.format('' if primary else '2')

    def _check_search_base_setting(self, primary):
        pf = self._get_setting_prefix(primary)
        s_name = pf + 'USER_SEARCH_BASE'
        if not hasattr(settings, s_name):
            logger.error(s_name + ' not in Django settings')
            sys.exit(1)

    def _check_ldap_users(self, users, primary, all_users):
        """
        Check and print out user status for a specific LDAP server.

        :param users: QuerySet of SODARUser objects
        :param primary: Whether to check for primary or secondary server (bool)
        :param all_users: Display status for all users (bool)
        """

        def _get_s(name):
            pf = self._get_setting_prefix(primary)
            return getattr(settings, pf + name)

        domain = _get_s('USERNAME_DOMAIN')
        domain_users = users.filter(username__endswith='@' + domain.upper())
        server_uri = _get_s('SERVER_URI')
        server_str = '{} LDAP server at "{}"'.format(
            'primary' if primary else 'secondary', server_uri
        )
        if not domain_users:
            logger.debug('No users found for {}, skipping'.format(server_str))
            return

        bind_dn = _get_s('BIND_DN')
        bind_pw = _get_s('BIND_PASSWORD')
        start_tls = _get_s('START_TLS')
        options = _get_s('CONNECTION_OPTIONS')
        user_filter = _get_s('USER_FILTER')
        search_base = _get_s('USER_SEARCH_BASE')

        # Enable debug if set in env
        if settings.LDAP_DEBUG:
            ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)

        # Connect to LDAP
        lc = ldap.initialize(server_uri)
        for k, v in options.items():
            lc.set_option(k, v)
        if start_tls:
            lc.protocol_version = 3
            lc.start_tls_s()
        try:
            lc.simple_bind_s(bind_dn, bind_pw)
        except Exception as ex:
            logger.error(
                'Exception connecting to {}: {}'.format(server_str, ex)
            )
            return

        for d_user in domain_users:
            r = lc.search(
                search_base,
                ldap.SCOPE_SUBTREE,
                user_filter.replace('%(user)s', d_user.username.split('@')[0]),
            )
            _, l_user = lc.result(r, 60)
            if len(l_user) > 0:
                name, attrs = l_user[0]
                user_ok = True
                # logger.debug('Result: {}; {}'.format(name, attrs))
                if (
                    'userAccountControl' in attrs
                    and len(attrs['userAccountControl']) > 0
                ):
                    val = int(attrs['userAccountControl'][0].decode('utf-8'))
                    if val in UAC_DISABLED_VALUES:
                        self._print_result(d_user, USER_DISABLED_MSG)
                        user_ok = False
                    elif val == UAC_LOCKED_VALUE:
                        self._print_result(d_user, USER_LOCKED_MSG)
                        user_ok = False
                if all_users and user_ok:
                    self._print_result(d_user, USER_OK_MSG)
            else:  # Not found
                self._print_result(d_user, USER_NOT_FOUND_MSG)

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--all',
            dest='all',
            action='store_true',
            required=False,
            help='Display results for all users even if status is OK',
        )
        parser.add_argument(
            '-l',
            '--limit',
            dest='limit',
            required=False,
            help='Limit search to "ldap1" or "ldap2".',
        )

    def handle(self, *args, **options):
        if not settings.ENABLE_LDAP:
            logger.info('LDAP not enabled, nothing to do')
            return
        self._check_search_base_setting(primary=True)
        self._check_search_base_setting(primary=False)
        u_query = Q(
            username__endswith='@{}'.format(
                settings.AUTH_LDAP_USERNAME_DOMAIN.upper()
            )
        )
        if settings.ENABLE_LDAP_SECONDARY:
            q_secondary = Q(
                username__endswith='@{}'.format(
                    settings.AUTH_LDAP2_USERNAME_DOMAIN.upper()
                )
            )
            u_query.add(q_secondary, Q.OR)
        users = User.objects.filter(u_query).order_by('username')
        limit = options.get('limit')
        if not limit or limit == 'ldap1':
            self._check_ldap_users(
                users, primary=True, all_users=options.get('all', False)
            )
        if settings.ENABLE_LDAP_SECONDARY and (not limit or limit == 'ldap2'):
            self._check_ldap_users(
                users, primary=False, all_users=options.get('all', False)
            )
