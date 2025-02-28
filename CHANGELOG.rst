SODAR Core Changelog
^^^^^^^^^^^^^^^^^^^^

Changelog for the **SODAR Core** Django app package. Loosely follows the
`Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.


v1.1.0 (2025-02-28)
===================

Added
-----

- **General**
    - ``drf-spectacular`` support (#1508)
    - REST API documentation section in documentation index (#1576)
- **Projectroles**
    - ``SODARUser.get_display_name()`` helper (#1487)
    - App setting type constants (#1458)
    - ``PluginAppSettingDef`` class for app setting definitions (#1456)
    - Django check for unique app setting names within each plugin (#1456)
    - App setting ``user_modifiable`` validation (#1536)
    - ``AppSettingAPI.get_all_by_scope()`` helper (#1534)
    - ``removeroles`` management command (#1391, #1541)
    - Site read only mode (#24)
    - ``site_read_only`` site app setting (#24)
    - ``is_site_writable()`` rule predicate (#24)
    - ``PermissionTestMixin.set_site_read_only()`` helper (#24)
    - ``PROJECTROLES_READ_ONLY_MSG`` setting (#24)
    - ``SiteReadOnlySettingAjaxView`` Ajax view (#24)
    - ``siteappsettings`` site app plugin (#1304)
    - ``SODARAppSettingFormMixin`` form helper mixin (#1545)
    - Old owner "remove role" option in ``RoleAssignmentOwnerTransferForm`` (#836)
    - Project deletion (#1090)
    - ``ProjectModifyPluginMixin.perform_project_delete()`` method (#1090)
    - ``ProjectDestroyAPIView`` REST API view (#1090)
    - ``ProjectSerializer`` ``children`` field (#1552)
    - ``SODARUserSerializer`` ``auth_type`` field (#1501)
    - ``UserRetrieveAPIView`` REST API view (#1555, #1575)
    - ``active`` arg in ``ProjectInviteMixin.make_invite()`` (#1403)
    - Ability for users to leave project (#918)
    - ``project_list_highlight`` and ``project_list_pagination`` app settings (#1005)
    - ``PROJECTROLES_API_USER_DETAIL_RESTRICT`` Django setting (#1574, #1575)
    - ``UserListAPIView`` ``include_system_users`` parameter (#1507)
    - CSS class ``sodar-alert-full-text-link`` for alert links (#1578)
- **Tokens**
    - ``TOKENS_CREATE_PROJECT_USER_RESTRICT`` Django setting (#1577)

Changed
-------

- **General**
    - Upgrade minimum Django version to v4.2.19 (#1531)
    - Upgrade general Python dependencies (#1531)
    - Replace ``awesome-slugify`` dependency with ``python-slugify`` (#1531, #1547)
    - Use ``SODARAPI*`` API view base classes instead of ``CoreAPI*`` (#1401)
    - Declare app setting definitions as ``PluginAppSettingDef`` objects (#1456)
    - Unify header layout in delete templates (#1548)
    - Upgrade to ``coverallsapp/github-action@v2`` in CI (#1566)
- **Adminalerts**
    - Display alert text as link if details are included (#1578)
- **Bgjobs**
    - Rename ``GlobalBackgroundJobView`` to ``SiteBackgroundJobView`` (#1333)
    - Unify naming in site view template to follow conventions (#1333)
- **Filesfolders**
    - Upgrade filesfolders REST API version to 2.0 (#1553)
    - Remove compability with filesfolders REST API <2.0 (#1553)
    - Replace REST API ``SODARUserSerializer`` fields with UUID ``SlugRelatedField`` (#1553)
- **Projectroles**
    - Deprecate ``get_user_display_name()``, use ``SODARUser.get_display_name()`` (#1487)
    - Deprecate declaring app setting definitions as dict (#1456)
    - Allow ``scope=None`` in ``AppSettingAPI.get_definitions()`` (#1535)
    - Deprecate ``AppSettingAPI.get_all()`` (#1534)
    - Allow no role for old owner in ``RoleAssignmentOwnerTransferMixin`` (#836, #1391)
    - Allow no role for old owner in ``perform_owner_transfer()`` (#836, #1391)
    - Move app setting form helpers in ``SODARAppSettingFormMixin`` (#1545)
    - Upgrade projectroles REST API version to v1.1 (#836)
    - Allow empty ``old_owner_role`` in ``RoleAssignmentOwnerTransferAPIView`` (#836)
    - Prevent project invite creation with active invite in parent category (#1403)
    - Allow ``null`` value for ``SODARUserAdditionalEmail.secret`` (#1477)
    - Display project list as flat list (#1005)
    - Optimize project list queries (#1005)
    - Hide "not editable on target sites" app settings label in forms (#1561)
    - Update search pagination layout to match new project list (#1560)
    - Enable ``UserListAPIView`` access restriction to contributors and above (#1574)
    - Unify project list loading element layouts (#1579)
- **Sodarcache**
    - Upgrade sodarcache REST API version to 2.0 (#1553)
    - Remove compability with sodarcache REST API <2.0 (#1553)
    - Replace REST API ``SODARUserSerializer`` fields with UUID ``SlugRelatedField`` (#1553)
- **Timeline**
    - Upgrade timeline REST API version to 2.0 (#1553)
    - Remove compability with timeline REST API <2.0 (#1553)
    - Replace REST API ``SODARUserSerializer`` fields with UUID ``SlugRelatedField`` (#1553)
- **Tokens**
    - Update UI for site read-only mode (#24)
    - Rename ``ProjectAppPlugin`` to ``SiteAppPlugin`` (#1337)
    - Enable restricting token creation to users with project roles (#1577)
- **Userprofile**
    - Update UI for site read-only mode (#24)
    - Rename ``UserAppSettingsForm`` and ``UserAppSettingsView`` (#1544)
    - Refactor ``UserAppSettingsForm`` to use ``SODARAppSettingFormMixin`` (#1545)
    - Add ``enable_project_uuid_copy`` setting description (#1419)

Fixed
-----

- **Projectroles**
    - Invalid ``app_permission`` in ``RemoteSiteAppPlugin`` (#1543)
    - Missing fields in ``ProjectRetrieveAPIView`` docstring (#1551)
    - Role delete alert dismissal fails with nested inherited roles (#1556)
    - Incorrect initial "N/A" access status for categories in project list (#1005)
    - App settings option validation as tuples (#1564)

Removed
-------

- **General**
    - Migrations squashed in v1.0 (#1455)
    - DRF ``generateschema`` support (#1508)
- **Projectroles**
    - Support for deprecated search results as dict (#1400)
    - Support for deprecated app setting ``local`` parameter (#1394)
    - Deprecated API view base classes and mixins (#1401)
    - Core API view base classes and mixins (#1401)
    - ``AppSettingAPI.get_global_value()`` helper (#1394, #1533)
- **Timeline**
    - Support for deprecated ``get_object_link()`` return values as dict (#1398)


v1.0.5 (2025-02-17)
===================

Changed
-------

- **Projectroles**
    - Optimize project list queries (#1005, #1571)

Fixed
-----

- **Projectroles**
    - System user group set for LDAP user on initial login (#1570)


v1.0.4 (2025-01-03)
===================

Added
-----

- **Projectroles**
    - Check mode in ``cleanappsettings`` command (#1520)
    - Support for all scopes in ``cleanappsettings`` undefined setting cleanup (#1526)
- **Timeline**
    - ``get_event_name()`` template tag (#1524)

Changed
-------

- **Projectroles**
    - Optimize ``cleanappsettings`` database queries (#1527)
- **Timeline**
    - Capitalize event description in UI (#1522)
    - Display event name in UI friendly format (#1524)
    - Display search results with new layout (#1521)
    - Enable search for display formatting of event name (#1525)


v1.0.3 (2024-12-12)
===================

Added
-----

- **Projectroles**
    - Info link for finder role in ``ProjectRoleView`` (#1511)
    - Table and strikethrough support in ``render_markdown()`` (#1272)
    - ``sodar-markdown-content`` CSS class (#1272)
- **Timeline**
    - User count in siteinfo stats (#1504)
    - Plugin tests (#1506)
- **Userprofile**
    - Authentication type in user details (#1500)

Changed
-------

- **General**
    - Upgrade minimum Django version to v4.2.17 (#1516)
    - Update dependency pinning (#1509)
- **Projectroles**
    - Update default OIDC login button template (#1503)
    - Update ownership transfer timeline event data (#1514)
    - Refactor ``syncremote`` management command (#1518)

Fixed
-----

- **Projectroles**
    - Deprecated ``SODAR_API_*`` settings required in tests (#1495)
    - Add workaround to ``ProjectInviteCreateView`` returning 404 with category and query string (#1510)
    - Broken tour help attachments in ``ProjectRoleView`` (#1512)
    - ``RoleAssignmentCreateView`` crash as delegate with promoting and delegate limit reached (#1515)
    - ``syncremote`` command crash from legacy API media type and version (#1517)


v1.0.2 (2024-09-09)
===================

Added
-----

- **General**
    - ``python3.11-gdbm`` dependency (#1491)
- **Projectroles**
    - ``get_user_by_uuid()`` common template tag (#1478)
    - ``ProjectInvite.get_url()`` helper (#1485)
    - ``ProjectInvite.refresh_date_expire()`` helper (#1486)

Changed
-------

- **General**
    - Upgrade minimum Django version to v4.2.16 (#1481)
- **Projectroles**
    - Truncate app setting values in ``remoteproject_sync.html`` (#1474)
    - JSON app setting value rendering in ``remoteproject_sync.html`` (#1472)
    - Change ``AppSettingAPI.compare_value()`` into public method (#1479)
    - Refactor ``AppLinkContent`` (#1470, #1483)
- **Userprofile**
    - Improve user settings list layout (#1490)

Fixed
-----

- **General**
    - Celery process raising ``dbm.error`` (#1491)
    - Celery process raising ``broker_connection_retry`` warning (#1493)
- **Bgjobs**
    - Non-migrated changes reported by squashed migrations (#1475)
- **Projectroles**
    - Incorrect app plugin link order in ``get_project_app_links()`` (#1468)
    - Remote sync crash on updating user with additional email (#1476)
    - User scope app setting display in ``remoteproject_sync.html`` (#1478)
    - Incorrect boolean comparison in ``AppSettingAPI._compare_value()`` with string value (#1473)
    - Boolean app setting update status in remote sync (#1473)

Removed
-------

- **Projectroles**
    - ``build_invite_url()`` utility method (#1485)
    - ``get_expiry_date()`` utility method (#1486)


v1.0.1 (2024-08-08)
===================

Added
-----

- **Projectroles**
    - Previously removed ``BatchUpdateRolesMixin`` (#1464)

Changed
-------

- **General**
    - Upgrade minimum Django version to v4.2.15 (#1466)
- **Timeline**
    - Rename search item category to ``Timeline Events`` (#1465)

Fixed
-----

- **Projectroles**
    - ``BatchUpdateRolesMixin`` removal breaking tests in other repos (#1464)
- **Timeline**
    - Deprecated link dict ``blank`` field assumed as mandatory (#1462)


v1.0.0 (2024-07-19)
===================

Added
-----

- **General**
    - Python v3.11 support (#1157)
    - Flake8 rule in ``Makefile`` (#1387)
    - OpenID Connect (OIDC) authentication support (#1367)
- **Adminalerts**
    - Admin alert email sending (#415)
    - ``notify_email_alert`` app setting (#415)
- **Filesfolders**
    - Optional pagination for REST API list views (#1313)
- **Projectroles**
    - ``full_title`` field in ``ProjectSerializer`` and API views (#1314)
    - Custom password argument in ``createdevusers`` management command (#1393)
    - ``PluginObjectLink`` data class in plugins (#1343)
    - ``PluginSearchResult`` data class in plugins (#1399)
    - Target user ``sodar_uuid`` updating in remote sync (#1316, #1317)
    - Update local user data in remote sync (#1407)
    - ``USER`` scope settings in remote sync (#1322)
    - ``AppLinkContent`` utility class (#1380, #1381)
    - ``checkusers`` management command (#1410)
    - ``SODARPageNumberPagination`` pagination class (#1313)
    - Optional pagination for REST API list views (#1313)
    - Email notification opt-out settings (#1417, #1418)
    - CC and BCC field support in sending generic emails (#415)
    - ``SODARUserAdditionalEmail`` model (#874)
    - ``is_source_site()`` and ``is_target_site()`` rule predicates
    - ``settings_link`` kwarg in ``send_generic_email()`` (#1418)
    - ``addremotesite`` and ``syncgroups`` command tests (#352)
    - ``RemoteSite.owner_modifiable`` field (#817)
    - ``assert_displayed()`` UI test helper
    - ``RemoteProjectAccessAjaxView`` Ajax view (#1358)
    - Remote project access status updating in project detail view (#1358)
    - ``SidebarContentAjaxView`` for sidebar and project dropdown content retrieval (#1366)
    - ``UserDropdownContentAjaxView`` for user dropdown content retrieval (#1366, #1392)
    - ``SODARUser.get_auth_type()`` helper (#1367)
    - ``ProjectInvite.is_ldap()`` helper (#1367)
    - ``AppSettingAPI.is_set()`` helper (#1450)
    - ``checks`` module for Django checks (#504)
    - Django check for enabled auth methods (#1451)
- **Timeline**
    - ``sodar_uuid`` field in ``TimelineEventObjectRef`` model (#1415)
    - REST API views (#1350)
    - ``get_project()`` helpers in ``TimelineEvent`` and ``TimelineEventObjectRef`` (#1350)
    - Optional pagination for REST API list views (#1313)
- **Userprofile**
    - Additional email address management and verification (#874)

Changed
-------

- **General**
    - Upgrade to Django v4.2 (#880)
    - Upgrade minimum PostgreSQL version to v12 (#1074)
    - Upgrade to PostgreSQL v16 in CI (#1074)
    - Upgrade general Python dependencies (#1374)
    - Reformat with black v24.3.0 (#1374)
    - Update download URL in ``get_chromedriver_url.py`` (#1385)
    - Add ``AUTH_LDAP_USER_SEARCH_BASE`` as a Django setting (#1410)
    - Change ``ATOMIC_REQUESTS`` recommendation and default to ``True`` (#1281)
    - Add OpenAPI dependencies (#1444)
    - Squash migrations (#1446)
- **Filesfolders**
    - Add migration required by Django v4.2 (#1396)
    - Add app specific media type and versioning (#1278)
- **Projectroles**
    - Rename ``AppSettingAPI`` ``app_name`` arguments to ``plugin_name`` (#1285)
    - Default password in ``createdevusers`` management command (#1390)
    - Deprecate ``local`` in app settings, use ``global`` instead (#1319)
    - Enforce optional handling of app settings ``global`` attributes (#1395)
    - Expect ``get_object_link()`` plugin methods to return ``PluginObjectLink`` (#1343)
    - Deprecate returning ``dict`` from ``get_object_link()`` (#1343)
    - Expect ``search()`` plugin methods to return list of ``PluginSearchResult`` objects (#1399)
    - Deprecate returning ``dict`` from ``search()`` (#1399)
    - Update core API view media type and versioning (#1278, #1406)
    - Separate projectroles and remote sync API media types and versioning (#1278)
    - Rename base test classes for consistency (#1259)
    - Prevent setting global user app settings on target site in ``AppSettingAPI`` (#1329)
    - Move project app link logic in ``AppLinkContent`` (#1380)
    - Move user dropdown link logic in ``AppLinkContent`` (#1381, #1413)
    - Do not recreate ``AppSetting`` objects on remote sync update (#1409)
    - Enforce project and site uniqueness in ``RemoteProject`` model (#1433)
    - Remove redundant permission check in ``project_detail.html`` (#1438)
    - Move sidebar, project dropdown and user dropdown creation to ``utils`` (#1366)
    - Refactor ``ProjectInviteProcessMixin.get_invite_type()`` into ``ProjectInvite.is_ldap()`` (#1367)
- **Sodarcache**
    - Rewrite REST API views (#498, #1389)
    - Raise ``update_cache()`` exception for ``synccache`` in debug mode (#1375)
- **Timeline**
    - Update ``get_object_link()`` usage for ``PluginObjectLink`` return data (#1343)
    - Rename ``ProjectEvent*`` models to ``TimelineEvent*`` (#1414)
    - Move event name from separate column into badge (#1370)
    - Use constants for event status types (#973)
- **Userprofile**
    - Disable global user settings on target site in ``UserSettingsForm`` (#1329)

Fixed
-----

- **General**
    - ``README.rst`` badge rendering (#1402)
- **Filesfolders**
    - OpenAPI ``generateschema`` errors and warnings (#1442)
- **Projectroles**
    - ``SODARUser.update_full_name()`` not working with existing name (#1371)
    - Legacy public guest access in child category breaks category updating (#1404)
    - Incorrect DAL widget highlight colour after upgrade (#1412)
    - ``ProjectStarringAjaxView`` creating redundant database objects (#1416)
    - ``addremotesite`` crash in ``TimelineAPI.add_event()`` (#1425)
    - ``addremotesite`` allows creation of site with mode identical to host (#1426)
    - Public guest access field not correctly hidden in project form (#1429)
    - Revoked remote projects displayed in project detail view (#1432)
    - Invalid URLs for remote peer projects in project detail view (#1435)
    - Redundant ``Project.get_source_site()`` calls in project detail view (#1436)
    - ``RemoteSite.get_access_date()`` invalid date sorting (#1437)
    - OpenAPI ``generateschema`` compatibility (#1440, #1442)
    - ``ProjectCreateView`` allows ``POST`` with disabled target project creation (#1448)
    - Plugin existence not explicitly checked in ``AppSettingAPI.set()`` update query (#1452)
    - ``search_advanced.html`` header layout (#1453)
- **Sodarcache**
    - REST API set view ``app_name`` incorrectly set (#1405)
- **Timeline**
    - OpenAPI ``generateschema`` warnings (#1442)

Removed
-------

- **General**
    - SAML support (#1368)
    - Python v3.8 support (#1382)
- **Projectroles**
    - ``PROJECTROLES_HIDE_APP_LINKS`` setting (#1143)
    - ``CORE_API_*`` Django settings (#1278)
    - Project starring timeline event creation (#1294)
    - ``user_email_additional`` app setting (#874)
    - ``get_visible_projects()`` template tag (#1432)
    - App setting value max length limit (#1443)
    - Redundant project permission in ``UserSettingRetrieveAPIView`` (#1449)


v0.13.4 (2024-02-16)
====================

Added
-----

- **Projectroles**
    - ``LoggedInPermissionMixin`` login message customization (#1360)
    - Base UI classses in Django API documentation (#1363)
- **Siteinfo**
    - Missing LDAP Django settings (#1347)

Changed
-------

- **General**
    - Upgrade minimum Django version to v3.2.24 (#1348)
    - Upgrade LDAP dependencies (#1348)
- **Projectroles**
    - Improve remote site deletion UI text labels (#1349)
    - Store remote sync app setting foreign key UUIDs as strings (#1356)
    - Do not create timeline event for re-accepting project invite (#1352)
    - Improve user message for re-accepting project invite (#1354)
    - Redirect to ``ProjectDetailView`` from re-accepting project invite (#1361)
    - Do not display login error on invite accept (#1360)
    - Clarify login error message for unauthenticated user (#1362)

Fixed
-----

- **General**
    - Invalid env var retrieval for ``AUTH_LDAP*_START_TLS`` (#1351)
    - Versioneer version not available in CI (#1357)
- **Projectroles**
    - Remote sync ``user_name`` crash with <0.13.3 target sites (#1355)

Removed
-------

- **Timeline**
    - Unused ``collect_extra_data()`` template tag (#1359)


v0.13.3 (2023-12-06)
====================

Added
-----

- **General**
    - LDAP settings for TLS and user filter (#1340)
    - ``LDAP_DEBUG`` Django setting
- **Projectroles**
    - ``_project_badge.html`` template (#1300)
    - ``InvalidFormMixin`` helper mixin (#1310)
    - Temporary ``user_name`` param in remote sync app settings (#1320)
    - User login/logout logging signals (#1326)
    - ``createdevusers`` management command (#1339)

Changed
-------

- **General**
    - Upgrade minimum Django version to v3.2.23 (#1312)
    - Upgrade general Python dependencies (#1312)
- **Appalerts**
    - Use projectroles project badge templage (#1300)
- **Bgjobs**
    - Provide correct URL patterns to plugins (#1331)
    - Rename ``bgjobs_site`` plugin (#1332)
- **Projectroles**
    - Prevent updating global settings for remote projects in ``AppSettingAPI`` (#1318)
    - Change ``project_star`` app setting to ``local`` (#1321)
- **Timeline**
    - Truncate long project titles in badge (#1299)
    - Use projectroles project badge templage (#1300)
    - Provide correct URL patterns to plugins (#1331)
- **Tokens**
    - Rename ``tokens`` plugin (#1334)

Fixed
-----

- **Appalerts**
    - Missing URL patterns in app plugin (#1331)
- **Projectroles**
    - Browser-specific ``sodar-btn-submit-once`` spinner padding (#1291)
    - Hidden JSON app settings reset on non-superuser project update (#1295)
    - Request object not provided to ``perform_project_modify()`` on create (#1301)
    - ``validate_form_app_settings()`` not called in ``ProjectForm`` (#1305)
    - Unhandled exceptions in ``validate_form_app_settings()`` calls (#1306)
    - ``validate_form_app_settings()`` results handling crash in ``ProjectForm`` (#1307)
    - ``RoleAssignment`` provided to ``validate_form_app_settings()`` in ``ProjectForm`` (#1308)
    - ``PROJECT_USER`` app settings remote sync failure (#1315)
    - Local app settings overridden by remote sync (#1324)
    - Local app setting value comparison failing in remote sync (#1330)
    - Active app highlight failing for multi-plugin apps (#1331)
    - Active app highlight failing for remote site views (#1331)
- **Timeline**
    - ``get_timestamp()`` template tag crash from missing ``ProjectEventStatus`` (#1297)
    - Empty object reference name handling in ``add_object()`` (#1338, #1341)
- **Tokens**
    - Missing URL patterns in app plugin (#1331)
- **Userprofile**
    - Unhandled exceptions in ``validate_form_app_settings()`` calls (#1306)
    - ``validate_form_app_settings()`` results handling crash in ``UserSettingForm`` (#1307)

Removed
-------

- **Timeline**
    - ``_project_badge.html`` template (#1300)


v0.13.2 (2023-09-21)
====================

Added
-----

- **General**
    - Release cleanup issue template (#1289)
    - Use ``sodar-btn-submit-once`` in object create forms (#1233)
- **Projectroles**
    - ``queryset_project_field`` override in ``APIProjectContextMixin`` (#1273)
    - ``sodar-btn-submit-once`` class for forms (#1233)

Changed
-------

- **General**
    - Refactor and cleanup permission tests (#1267)
    - Enable setting ``ADMINS`` Django setting via env (#1280)
- **Timeline**
    - Update column width and responsiveness handling (#1721)
    - View icon display for site views (#1720)

Fixed
-----

- **Projectroles**
    - User account update signals not triggered on login (#1274)
    - Project list rendering failure with finder role (#1276)
    - Crash in ``email`` module with empty ``ADMINS`` setting (#1287)
- **Timeline**
    - Ajax view permission test issues (#1267)


v0.13.1 (2023-08-30)
====================

Added
-----

- **General**
    - ``get_chromedriver_url.sh`` utility helper (#1255)
- **Projectroles**
    - ``TestSiteAppPermissionBase`` base test class (#1236)
    - ``full_title`` arg in ``Project.get_log_title()`` (#1238)
    - ``MultipleFileInput`` and ``MultipleFileField`` form helpers (#1226)
    - ``syncmodifyapi`` project limiting option (#1263)

Changed
-------

- **General**
    - Update ``django-plugins`` and ``drf-keyed-list`` dev dependencies to PyPI packages (#1241)
    - Upgrade general Python dependencies (#1239)
    - Update tour help (#1102)
    - Template refactoring (#1102, #1249)
- **Projectroles**
    - Move ``setup_ip_allowing()`` to ``IPAllowMixin`` (#1237)
    - Improve ``syncmodifyapi`` project logging (#1228)
    - Do not exit ``syncmodifyapi`` on failure (#1229)
    - Simplify ``syncmodifyapi`` project querying (#1264)
    - Update ``get_role_display_name()`` to receive ``Role`` as first argument (#1265)
    - Improve member invite templates (#1246, #1247, #1248)
- **Timeline**
    - Handle app plugin exceptions in ``get_object_link()`` (#1232)

Fixed
-----

- **General**
    - Search in Sphinx docs build (#1245)
    - All utility scripts not set as executable (#1254)
    - Local Chromedriver install failure (#1255)
- **Projectroles**
    - Hardcoded ``appalerts`` dependency in ``test_views`` (#1252)
    - Remote sync crash in ``_add_parent_categories()`` (#1258)
    - Remote sync timeline event description notation (#1260)
    - Django settings not working in login view (#1250)
    - Template extension not working in login view (#1250)
- **Userprofile**
    - Template padding (#1244)


v0.13.0 (2023-06-01)
====================

Added
-----

- **General**
    - Separate Chromedriver install script (#1127)
    - Custom include path with ``PROJECTROLES_TEMPLATE_INCLUDE_PATH`` (#1049)
    - Celery setup (#1198)
- **Appalerts**
    - Dismissed alerts list view (#711)
    - ``add_alerts()`` API method (#1101)
- **Projectroles**
    - ``project_star`` app setting (#321)
    - Search app omitting with ``PROJECTROLES_SEARCH_OMIT_APPS`` (#1119)
    - Inherited roles in project list and retrieve REST API views (#1121)
    - App settings validation by plugin method (#860)
    - App settings callable default value and options support (#1050)
    - Full role inheritance (#638, #1103, #1172, #1173)
    - ``Project.get_roles_by_rank()`` helper (#638)
    - ``RoleMixin`` with ``init_roles()`` for tests
    - App settings project type restriction (#1169, #1170)
    - Validation for category delimiter in ``Project.title`` (#1163)
    - ``SODARUser.update_full_name()`` and ``update_ldap_username()`` helpers (#1056)
    - Project app alert dismissal on role assignment deletion (#703)
    - Project finder role (#1011)
    - ``is_project_finder()`` rule predicate (#1011)
    - Site-wide timeline events for remote site operations (#746, #1209)
    - Display app icon for settings in project and user forms (#947, #1187)
    - Cleanup for ``PROJECT_USER`` scope app settings (#1128, #1129)
    - ``SITE`` scope for app settings (#1184)
    - Periodic remote project sync (#813)
- **Siteinfo**
    - Add ``LDAP_ALT_DOMAINS`` to displayed settings (#1123)
- **Sodarcache**
    - ``delete_cache_item()`` method (#1068)
- **Timeline**
    - Search result limiting with ``TIMELINE_SEARCH_LIMIT`` (#1124)

Changed
-------

- **General**
    - Use path instead of regex for URL patterns (#1116)
    - Upgrade minimum Django version to v3.2.19 (#1117, #1122)
    - Upgrade general Python dependencies (#1117)
    - Update ``env.example`` (#1065)
- **Appalerts**
    - Handle alerts with no project access in UI (#1177)
- **Filesfolders**
    - Change app display name to "Files" (#828)
- **Projectroles**
    - Display full user name in role update form (#1147)
    - Make email optional in ``SODARUser.get_form_label()`` (#1148)
    - Move user model tests to projectroles model tests (#1149)
    - Replace ``ProjectUserTag`` project starring with app setting (#321)
    - Prevent sending invites to local users with local users disabled (#616)
    - Implement advanced search with POST (#712)
    - Remove category project list scrolling (#1141)
    - Move sidebar template tags to context processor (#969)
    - Update ``Project`` model API methods (#638, #710, #1045, #1178, #1201, #1222)
    - Update permission and UI test setup (#638)
    - Display roles consistently in member/owner update UI (#1027)
    - Reduce site app view top margin (#866)
    - Rename ``RoleAssignment.project`` related name to ``local_roles`` (#1175)
    - Replace ``PROJECTROLES_HIDE_APP_LINKS`` with ``PROJECTROLES_HIDE_PROJECT_APPS`` (#1142)
    - Deprecate ``PROJECTROLES_HIDE_APP_LINKS`` (#1142)
    - Move Django signals to ``signals.py`` (#1056)
    - Disallow public guest access for categories (#897)
    - Refactor ``AppSettingAPI`` (#1190, #1213)
- **Timeline**
    - Display event extra data to superusers, owners and delegates (#1171)

Fixed
-----

- **General**
    - ``django-autocomplete-light==3.9.5`` crash with ``whitenoise`` (#1224)
    - Readthedocs build failing from using Python <3.8 (#1227)
- **Appalerts**
    - ``AppAlert.__repr__()`` crash if project not set (#1150)
- **Bgjobs**
    - Non-standard URL paths (#1139)
- **Projectroles**
    - ``get_form_label()`` displaying user without full name in parenthesis (#1140)
    - Project and user update form JSON error handling (#1151)
    - ``Project`` API methods returning unexpected multiple ``RoleAssignment`` objects for user (#710)
    - ``ProjectListAPIView`` failure with inheritance and public guest access (#1176)
    - Incorrect icon displayed in ``remoteproject_update.html`` (#1179)
    - Long ``Project.full_title`` breaking ``remoteproject_update.html`` layout (#1188)
    - ``LDAP_ALT_DOMAINS`` check not working in ``get_invite_type()`` (#1217)

Removed
-------

- **General**
    - User model tests from ``example_site`` (#1149)
- **Projectroles**
    - Deprecated ``AppSettingAPI`` methods (#1039)
    - ``ProjectUserTag`` model (#321)
    - ``RoleAssignmentManager`` (#638)
    - ``Project.get_all_roles()`` method (#638, #710)
    - ``is_inherited_owner()`` template tag (#1172)


v0.12.0 (2023-02-03)
====================

Added
-----

- **General**
    - Path URL examples and tests in ``example_project_app`` (#1047)
- **Filesfolders**
    - Project archiving support (#1086)
- **Projectroles**
    - App settings management via REST API (#521)
    - App setting update methods in ``ProjectModifyPluginMixin`` (#521)
    - Role ranking (#666)
    - Project archiving (#369, #1098, #1099, #1100)
    - ``Project.set_archive()`` helper (#369)
    - ``can_modify_project_data`` predicate in rules (#369)
    - ``cleanup_kwargs`` in ``assert_response_api()`` API test helper (#1088)
    - ``is_superuser`` in ``SODARUserSerializer`` (#1052)
    - Ajax view ``CurrentUserRetrieveAjaxView`` (#1053)
- **Timeline**
    - Admin view for all timeline events (#873)
    - Search functionality (#1095)
    - Back button in site event list object view (#1097)
    - ``sodar_uuid`` field in ``ProjectEventStatus`` (#1112)

Changed
-------

- **General**
    - Rename incorrectly protected mixin methods (#1020)
    - Upgrade ``checkout`` and ``setup-python`` GitHub actions (#1091)
    - Upgrade minimum Django version to v3.2.17 (#1113)
- **Projectroles**
    - Rename ``AppSettingAPI`` methods (#539, #1040)
    - Deprecate old ``AppSettingAPI`` method names (#539, #1039)
    - Hide apps in ``PROJECTROLES_HIDE_APP_LINKS`` from superusers (#1042)
    - Close Django admin warning modal on continue (#1114)
- **Siteinfo**
    - Use project type display names in stats view (#1107)
- **Timeline**
    - Display status extra data in event details modal (#1096)

Fixed
-----

- **Projectroles**
    - Crash from path URLs in ``get_project()`` (#1047)
    - Initial owner user name in project create form not following convention (#1059)
- **Timeline**
    - Project references in ``timeline_site.html`` (#1058)

Removed
-------

- **Projectroles**
    - Unused ``taskflow_testcase`` module (#1041)
- **Timeline**
    - Deprecated get_current_status() method (#1015)


v0.11.1 (2023-01-09)
====================

Added
-----

- **Projectroles**
    - Allow enabling project breadcrumb scrolling (#1037)
    - ``PROJECTROLES_BREADCRUMB_STICKY`` Django setting (#1037)
    - ``ProjectAccessMixin`` external app model support (#1067)
    - ``Project.get_log_title()`` helper (#1071)

Changed
-------

- **General**
    - Upgrade minimum Django version to v3.2.16 (#1035)
    - Upgrade Python dependencies (#1073)
- **Timeline**
    - Extra data loading using Ajax view (#1055)

Fixed
-----

- **General**
    - Use ``apt-get`` instead of ``apt`` in CI (#1030)
    - Incorrect branch in ``README.rst`` Coveralls link (#1031)
    - Postgres role errors in GitHub Actions CI (#1033)
    - ``install_postgres.sh`` breaking with unsupported Ubuntu versions (#1061)
- **Timeline**
    - Extra data not displayed after viewing event details (#1055)
    - Crash in ``get_app_icon_html()`` with project event from site app (#1057)
    - Crash from missing ``plugin_lookup`` in ``timeline_site.html`` (#1076)

Removed
-------

- **General**
    - Unused ``about.html`` template (#1029)
- **Projectroles**
    - Unused ``taskflow_testcase`` module (#1041)
- **Timeline**
    - Deprecated ``get_current_status()`` method (#1015)


v0.11.0 (2022-09-23)
====================

Added
-----

- **General**
    - Coverage reporting with Coveralls (#1026)
- **Projectroles**
    - Project modifying API in ``ProjectModifyPluginMixin`` (#387)
    - ``PROJECTROLES_ENABLE_MODIFY_API`` Django setting (#387)
    - ``PROJECTROLES_MODIFY_API_APPS`` Django setting (#387)
    - ``syncmodifyapi`` management command (#387)
    - ``SODARBaseAjaxMixin`` with ``SODARBaseAjaxView`` functionality (#994)
    - Custom login view content via ``include/_login_extend.html`` (#982)

Changed
-------

- **General**
    - Upgrade minimum PostgreSQL version to v11 (#303)
    - Upgrade minimum Django version to v3.2.15 (#1003)
    - Upgrade to black v22.6.0 (#1003)
    - Upgrade general Python dependencies (#1003, #1019)
- **Filesfolders**
    - Change ``public_url`` form label (#1016)
- **Projectroles**
    - Replace Taskflow specific code with project modifying API calls (#387)
    - Rename ``revoke_failed_invite()`` to ``revoke_invite()``
    - Do not return ``submit_status`` from project API views (#971)
    - Remove required ``owner`` argument for ``ProjectUpdateAPIView`` (#1007)
    - Remove unused owner operations from ``ProjectModifyMixin`` (#1008)
    - Refactor and cleanup ``AppSettingAPI`` (#1024)
- **Timeline**
    - Deprecate ``ProjectEvent.get_current_status()``, use ``get_status()`` (#322)

Fixed
-----

- **Projectroles**
    - Crash at exception handling in ``clean_new_owner()`` (#981)
    - Incorrect button icon in remote site form (#1001)
    - Case-sensitive project list sorting (#1006)
    - Project list filtering not trimmed (#1021)
- **Timeline**
    - Uncaught exceptions in ``get_plugin_lookup()`` (#979)

Removed
-------

- **General**
    - Codacy support (#1022)
- **Projectroles**
    - Taskflow specific views, tests and API calls (#387)
    - ``get_taskflow_sync_data()`` method from ``ProjectAppPluginPoint`` (#387)
    - ``Project.submit_status`` field and usages in code (#971)
- **Taskflowbackend**
    - Remove app and implement in SODAR (#387)
- **Timeline**
    - Taskflow API views (#387)


v0.10.13 (2022-07-15)
=====================

Added
-----

- **General**
    - GitHub issue templates (#995)
- **Projectoles**
    - Taskflow access from a different host for tests (#986)
    - ``TASKFLOW_TEST_SODAR_HOST`` to set host name for tests (#986)

Changed
-------

- **General**
    - Update development and contributing documentation (#988, #989, #992, #996)
    - Update Actions and Codacy badges for new GitHub repository (#990, #991)
    - Upgrade minimum Django version to v3.2.14 (#993)

Fixed
-----

- **Projectroles**
    - Project list role column fails if only categories are visible (#985)


v0.10.12 (2022-04-19)
=====================

Added
-----

- **Timeline**
    - Support for specifying plugin for events (#975)

Changed
-------

- **General**
    - Upgrade to black v22.3.0 (#972)
    - Upgrade minimum Django version to v3.2.13 (#976)
- **Projectroles**
    - Update sidebar icon padding on resize (#967)
    - Batch loading for project list columns (#968)
    - Optimize ``ProjectListRoleAjaxView``
    - Refactor sidebar toggling (#970)
    - Make ``request`` optional for ``send_generic_mail()`` and ``send_mail()``


v0.10.11 (2022-03-22)
=====================

Added
-----

- **Projectroles**
    - Sidebar icon scaling using ``PROJECTROLES_SIDEBAR_ICON_SIZE`` (#843)

Changed
-------

- **General**
    - Upgrade to setuptools v59.6.0 (#948)
    - Unify Django messages in UI (#961)
- **Projectroles**
    - Refactor ``ProjectSearchResultsView`` and ``search_results.html`` (#955, #958)
    - Force user to select type in project create form (#963)
    - Optimize parent queries in project update form (#965)

Fixed
-----

- **General**
    - Incorrect version for ipdb dependency (#951)
- **Filesfolders**
    - Template crashes from missing ``FileData`` (#962)
- **Projectroles**
    - App search results template included if no results found (#958)
    - Inconsistent sidebar icon size (#960)
    - ``get_display_name()`` use in Django messages and forms (#952)
    - Projects not displayed in project list for inherited owner (#966)

Removed
-------

- **Projectroles**
    - ``get_not_found_alert()`` template tag (#955)


v0.10.10 (2022-03-03)
=====================

Added
-----

- **Tokens**
    - Success messages for token creation and deletion (#935)
- **Userprofile**
    - Success message for user settings update (#936)

Changed
-------

- **Projectroles**
    - Improve project list loading layout (#937)
    - Make project list responsive when under category (#938)
    - Enable testing knox auth for REST API views without a token

Fixed
-----

- **Projectroles**
    - Duplicate terms not removed in advanced search (#943)
    - ``ProjectSearchResultsView.get_context_data()`` called twice (#944)
    - Redundant backend API initialization in ``check_backend()`` (#946)


v0.10.9 (2022-02-16)
====================

Added
-----

- **Projectroles**
    - ``req_kwargs`` arg for ``TestPermissionMixin.assert_response()`` (#909)
    - Starring and filtering controls for category subproject list (#56)
    - Enable anonymous access for Ajax views with ``allow_anonymous`` (#916)

Changed
-------

- **General**
    - Use ``LATEST_RELEASE`` in Chromedriver install (#906)
- **Projectroles**
    - Project list client side loading (#825, #908, #913, #933)
    - Optimize project list queries (#922, #923)
    - Move project starring JQuery into ``project_star.js`` (#930)
- **Timeline**
    - Display event details as a modal (#910, #912)
    - Make ``description`` optional for ``_make_event_status()`` (#890)

Fixed
-----

- **Projectroles**
    - Project list JQuery loaded in project detail view (#914)
    - ``sodar-modal-wait`` layout (#931)
    - Redundant project starring JQuery includes (#930)
- **Timeline**
    - Event status layout overflowing (#911)

Removed
-------

- **Projectroles**
    - Unused project list templates and template tags (#913)
- **Timeline**
    - Unused ``get_event_details()`` template tag


v0.10.8 (2022-02-02)
====================

Added
-----

- **Projectroles**
    - Disabling ``ManagementCommandLogger`` with ``LOGGING_DISABLE_CMD_OUTPUT`` (#894)
- **Siteinfo**
    - Missing site settings in ``CORE_SETTINGS`` (#877)
- **Timeline**
    - ``get_plugin_lookup()`` and ``get_app_icon_html()`` template tags (#888)
    - Template tag tests (#891)

Changed
-------

- **General**
    - Upgrade minimum Python version to v3.8, add v3.10 support (#885)
    - Upgrade minimum Django version to v3.2.12 (#879, #902)
    - Upgrade Python dependencies (#884, #893, #901)
    - Upgrade to Chromedriver v97 (#905)
- **Projectroles**
    - Display admin icon in user dropdown (#886)
    - Refactor UI tests (#882)
- **Timeline**
    - Improve event list layout responsivity (#887)
    - Replace event list app column with app icon (#888)
    - Set default kwarg values for model test helpers (#890)
    - Move ``get_request()`` to ``TimelineAPIMixin``
    - Display recent events regardless of status in details card (#899)
    - Optimize ``get_details_events()`` (#899)

Fixed
-----

- **Projectroles**
    - Parent owner set as owner in project create form for non-owner category members (#878)
    - Project header icon tooltip alignment (#895)
    - Redundant public access icon display for categories (#896)
    - Icon size syntax (#875)
    - Content of ``sodar-code-input`` partially hidden in Chrome (#904)
- **Siteinfo**
    - Layout responsivity issues with long labels (#883)
- **Timeline**
    - Redundant app plugin queries in event list (#889, #900)

Removed
-------

- **Projectroles**
    - ``_add_remote_association()`` helper from UI tests (#882)
- **Timeline**
    - Unused ``get_app_url()`` template tag (#888)


v0.10.7 (2021-12-14)
====================

Added
-----

- **Adminalerts**
    - UI documentation (#865)
- **Siteinfo**
    - UI documentation (#865)

Changed
-------

- **General**
    - Upgrade minimum Django version to v3.2.10 (#869)
    - Upgrade to python-ldap v3.4.0 (#871)
- **Projectroles**
    - HTTP 403 raised instead of 400 if project type disallowed by API view (#872)
    - Update role list media rules (#863)
    - Add line break for custom email footer (#864)

Fixed
-----

- **Projectroles**
    - ``ManagementCommandLogger`` crash by unset ``LOGGING_LEVEL`` (#862)
    - ``highlight_search_term()`` crash on invalid term input (#867)
    - Search bar allowing invalid input (#868)
    - Wrong project type displayed in project type restriction API response (#872)


v0.10.6 (2021-11-19)
====================

Added
-----

- **General**
    - ``LOGGING_LEVEL`` setting in example configs (#822)
    - ``ProfilingMiddleware`` for cProfile profiling in debug more (#839)
    - ``PROJECTROLES_ENABLE_PROFILING`` setting for profiling (#839)
- **Projectroles**
    - ``cleanup_method`` arg for ``assert_response()`` (#823)
    - Timeline object and data helpers in site and backend plugins (#832)
    - ``ManagementCommandLogger`` helper (#844)
    - ``get_email_user()`` helper (#845)
    - Project type restriction in API views with ``project_type`` attribute (#850)
    - ``Project.has_public_children`` field (#851)
    - Email sending for additional user emails (#861)
    - ``user_email_additional`` app setting (#861)
    - ``email.get_user_addr()`` helper (#861)

Changed
-------

- **General**
    - Upgrade to Chromedriver v96 (#818, #847, #852)
    - Use ``LOGGING_LEVEL`` in example ``set_logging()`` (#822)
    - Upgrade minimum Django version to v3.2.9 (#835, #848)
    - Improve management command output and logging (#844)
    - Optimize project list queries (#851)
- **Filesfolders**
    - Refactor ``checkAll()`` helper (#816)
    - Restrict project type in API views (#850)
- **Projectroles**
    - Upgrade DataTables includes on search results page (#841, #856)
    - Improve email subject prefix formatting (#829)
    - Update user representations in emails (#845)
- **Timeline**
    - Refactor ``TimelineAPI``

Fixed
-----

- **General**
    - Github Actions CI failure by old package version (#821)
    - Codacy code quality badge in README (#815)
- **Appalerts**
    - Random crashes in ``TestTitlebarBadge.test_alert_dismiss_all`` (#811)
- **Projectroles**
    - ``sodar-overflow-container`` failing with certain tables (#830)
    - Sort icons not displayed on search results page (#841)
    - App alert badge content wrapping (#846)
    - Nested categories with public children not displayed correctly for anon users (#853, #855)
    - Public and remote icons breaking project title bar layout (#859)
- **Timeline**
    - Crash from invalid plugin name in ``get_event_description()`` (#831)
    - Redundant database queries in ``get_event_description()`` (#834)
    - Site and backend plugins not supported in ``get_event_description()`` (#832)

Removed
-------

- **Projectroles**
    - ``get_star()`` template tag (#851)
    - ``Project.has_public_children()`` method: use ``has_public_children`` instead (#851)


v0.10.5 (2021-09-20)
====================

Added
-----

- **Appalerts**
    - Display project badge in alert (#790, #801)
    - Dismiss all link in title bar badge (#802)
- **Projectroles**
    - ``exact`` kwarg for ``assert_element_count()`` in UI tests (#798)
    - Custom email header and footer (#789)
    - ``PROJECTROLES_EMAIL_HEADER`` and ``PROJECTROLES_EMAIL_FOOTER`` settings (#789)
    - ``get_all_defs()`` helper in ``AppSettingAPI`` (#808)

Changed
-------

- **General**
    - Unify app settings label notation (#793)
    - Upgrade minimum Django version to v3.2.7 (#800)
- **Appalerts**
    - Improve alert list layout (#790)
- **Projectroles**
    - Improve login button locating in ``login_and_redirect_with_ui()`` (#796)
    - Hide skipped app settings from target remote sync view (#785)
    - Improve app settings layout in target remote sync view (#804)
    - Minor remote sync refactoring (#721, #785, #807)
    - Refactor ``_get_projectroles_settings()`` into ``get_projectroles_defs()`` (#803)

Fixed
-----

- **Appalerts**
    - Redundant HTML anchor in Dismiss All button (#788)
- **Projectroles**
    - Sidebar notch position (#787)
    - ``sodar-overflow-container`` misalignment (#791)
    - App settings recreated if value is identical (#785)
    - Line separators in ``remoteproject_sync.html`` (#805)
    - App settings remote sync only supporting projectroles (#806, #809)
    - Plugin name incorrectly displayed in target remote sync view (#810)
    - Active link check for projectroles URLs ignoring app name (#814)

Removed
-------

- **Projectroles**
    - ``get_plugin_name_by_id()`` template tag (#812)


v0.10.4 (2021-08-19)
====================

Added
-----

- **General**
    - ``LOGGING_APPS`` and ``LOGGING_FILE_PATH`` settings in example site (#762)
    - Siteinfo app to logged apps in base config (#767)
- **Appalerts**
    - "Dismiss All" button in alert list (#770, #781)
    - Update list view with reload link on added alerts (#780)
- **Siteinfo**
    - ``ENABLED_BACKEND_PLUGINS`` in ``CORE_SETTINGS`` (#766)

Changed
-------

- **General**
    - Upgrade to Chromedriver v92 (#772)
    - Upgrade minimum Django version to v3.2.6 (#773)
- **Appalerts**
    - Display no alerts element after clearing list (#779)
- **Projectroles**
    - Refactor view test setup (#769)
- **Siteinfo**
    - UI improvements for empty and unset values

Fixed
-----

- **General**
    - SAML attribute map example in config (#760)
    - Docs layout broken by ``docutils>=0.17`` (#763)
    - Logging level not correctly set for all loggers (#771)
- **Projectroles**
    - HTTP 403 raised instead of 404 in API and UI views if object not found (#774)
    - Incorrect message on ownership transfer email notifications (#778)
    - Project update view loading slowed down by large number of child categories (#765)
- **Siteinfo**
    - Plugin settings not read if ``get_statistics()`` raises exception (#767)
    - List layout broken by empty string values (#768)


v0.10.3 (2021-07-01)
====================

Changed
-------

- **General**
    - Upgrade minimum Django version to v3.2.5 (#744)
    - Upgrade Python dependencies (#744)
- **Userprofile**
    - Hide user update button for non-local users (#748)

Fixed
-----

- **Projectroles**
    - False errors from app settings sync if app not installed on target site (#757)
- **Timeline**
    - Uncaught exceptions in ``get_event_description()`` (#749)
- **Tokens**
    - Expiry date incorrectly displayed in token list (#747)
    - Missing query set ordering in token list (#754)

Removed
-------

- **Tokens**
    - Unused ``admin`` and ``models`` modules


v0.10.2 (2021-06-03)
====================

Changed
-------

- **General**
    - Upgrade to Chromedriver v90 (#731)
    - Rename example site adminalerts URL include (#730)
    - Update documentation screenshots (#734)
    - Reorganize static files in documentation (#734)
    - Rename example ``django-db-file-storage`` URL pattern (#732)
    - Upgrade minimum Django version to v3.2.4 (#727)
    - Upgrade Python dependencies (#727)
    - Reformat with Black v21.5b2
- **Projectroles**
    - Display anonymous icon in titlebar dropdown if not logged in (#726)

Fixed
-----

- **General**
    - Figure aspect ratios in documentation (#735)
- **Projectroles**
    - Unhandled exceptions and missing data in project list extra columns (#733)
    - Project star icon alignment (#736)
    - Project list layout broken by ``FILESFOLDERS_SHOW_LIST_COLUMNS`` setting (#737)
    - Public guest access role not displayed in project list (#739)
- **Timeline**
    - Crash in ``add_event()`` if called with ``AnonymousUser`` (#740)


v0.10.1 (2021-05-06)
====================

Added
-----

- **General**
    - Installation via PyPI (#293)
- **Appalerts**
    - Update alerts in JQuery without page reloading (#701, #723)
    - ``APPALERTS_STATUS_INTERVAL`` setting (#701)

Changed
-------

- **General**
    - Upgrade minimum Django version to v3.2.1 (#696)
    - Upgrade django-debug-toolbar to v3.2.1 (#706)
- **Appalerts**
    - Tweak alert layout (#716)
- **Projectroles**
    - Enforce 3 character minimum limit for terms in multi-term search (#715)
    - Improve remote sync stability

Fixed
-----

- **General**
    - Add ``build/`` to ``.gitignore`` (#707)
    - Invalid operating system qualifier in ``setup.py`` (#708)
- **Projectroles**
    - Uncaught exceptions in app plugin ``search()`` (#713)
    - Broken project icon on search results page (#714)
    - Empty search terms not sanitized (#715)
    - Hardcoded optional ``PROJECTROLES_DISABLE_CATEGORIES`` setting in forms (#719)
    - Remote sync objects referred by database ID instead of ``sodar_uuid`` (#720)
    - Uncaught exceptions in app settings remote sync (#720)
    - Assumed ``sodar_uuid`` match for target app settings in remote sync (#722)


v0.10.0 (2021-04-28)
====================

Added
-----

- **Adminalerts**
    - ``get_statistics()`` implementation
- **Appalerts**
    - Add site app and backend for app alerts (#642)
- **Projectroles**
    - ``geticons`` management command for retrieving Iconify icons (#54)
    - ``spin`` class in ``projectroles.css`` for spinning icon support (#54)
    - Optional public guest access for projects (#574)
    - ``public_guest_access`` and ``set_public()`` in ``Project`` model (#574)
    - Enable allowing anonymous access to site (#574)
    - ``PROJECTROLES_ALLOW_ANONYMOUS`` site setting (#574)
    - ``is_allowed_anonymous`` predicate in ``rules`` (#574)
    - ``site_app_processor`` in ``context_processors`` (#574)
    - ``get_statistics()`` in ``SiteAppPluginPoint``
    - ``info_settings`` in app plugins (#671)
    - ``plugin_type`` argument in ``get_app_plugin()`` (#309)
    - ``handle_project_update()`` in ``ProjectAppPlugin`` (#387, #675)
    - App alerts for project and role updates (#642, #692)
- **Siteinfo**
    - Display selected Django settings in UI (#671)
- **Timeline**
    - Permission tests (#144)
    - Site app plugin for site-wide events (#668)
- **Tokens**
    - Permission tests

Changed
-------

- **General**
    - Upgrade project to Django v3.2 (#194, #695)
    - Upgrade Python dependencies (#194, #678, #685)
    - Rename GitHub repo to ``sodar-core`` (#699)
    - Rename ``master`` branch to ``main``
    - Use Iconify for icons (#54)
    - Use Material Design Icons as default icon set (#54)
    - Bump minimum Python version requirement to v3.7 (#121)
    - Upgraded versioneer (#656)
    - Update views, mixins and tags for anonymous user access (#574)
    - Upgrade recommended development OS version to Ubuntu v20.04 (#640)
    - Do not send redundant emails to users initiating updates (#693)
    - Get all app settings from environment
- **Projectroles**
    - Set parent owner as initial owner in project form (#667)
    - Always show Django admin warning (#677)
    - Modify signature of ``get_history_dropdown()`` template tag (#668)
    - Add default ``superuser`` value to ``LiveUserMixin._make_user()``
    - Include ``select2`` CSS locally (#457)
    - Refactor ``cleanappsettings`` (#673)
- **Siteinfo**
    - Tabbed layout in site info view
- **Timeline**
    - Make ``project`` and ``user`` fields in ``ProjectEvent`` optional (#119, #668)
    - Modify signatures of ``get_object_url()`` and ``get_object_link()`` helpers (#668)
    - Allow custom ``INIT`` status data (#700)
- **Tokens**
    - Refactor view tests

Fixed
-----

- **General**
    - All app settings not properly frozen in test config (#688)
- **Adminalerts**
    - Pagedown widget breaking CSS layout in Firefox (#659)
- **Bgjobs**
    - Plugin queries in template tag module root (#653)
- **Projectroles**
    - Description line spacing in project header (#632)
    - Pagedown widget breaking CSS layout in Firefox (#659)
    - Crash by missing optional ``PROJECTROLES_DELEGATE_LIMIT`` setting (#676)
    - ``cleanappsettings`` deleting defined app settings (#673)
- **Timeline**
    - Double status added when calling ``add_event()`` with ``INIT`` type (#700)

Removed
-------

- **General**
    - Font Awesome support without Iconify (#54)
- **Projectroles**
    - ``get_site_app()`` template tag (#574)
    - Deprecated search functionality with a single ``search_term`` (#618)
    - Deprecated ``get_full_title()`` method from ``Project`` model (#620)


v0.9.1 (2021-03-05)
===================

Added
-----

- **Projectroles**
    - Inline head include from environment variables in base template (#639)
    - ``req_kwargs`` argument in ``SODARAPIPermissionTestMixin.assert_response_api()`` (#662)
    - Display inherited owner note in remote project sync UI (#643)
    - ``is_inherited_owner()`` template tag

Changed
-------

- **General**
    - Improve Codacy support in GitHub Actions
    - Upgrade to Chromedriver v89 (#657)
- **Projectroles**
    - Duplicate ``sodar_uuid`` in ``SODARNestedListSerializer`` (#633)
    - Rename and refactor ``LocalUserForm`` and ``user_form.html`` (#651)

Fixed
-----

- **Filesfolders**
    - File list breadcrumb icon alignment (#660)
    - Cancel link in batch edit view (#647)
    - Batch move folders not displayed in UI (#648)
    - Batch moving objects to project root failing (#661)
- **Projectroles**
    - Login redirect URLs with query strings not properly handled by ``assert_response()`` (#635)
    - Remote project icons in project list not displayed (#664)
    - Version ``0.8.4`` missing from ``CORE_API_ALLOWED_VERSIONS``
- **Userprofile**
    - User update link and template not working as expected (#650)

Removed
-------

- **Userprofile**
    - Unused template ``user_update.html`` (#651)


v0.9.0 (2021-02-03)
===================

Added
-----

- **General**
    - SAML SSO authentication support (#588)
    - REST API example ``HelloExampleProjectAPIView`` in ``example_project_app`` (#518)
- **Projectroles**
    - Projectroles app settings (#532)
    - Remote sync for projectroles app setting (#533, #586)
    - IP address based access restriction for projects (#531)
    - ``is_delegate()`` and ``is_owner_or_delegate()`` helpers for ``Project`` model
    - Remote sync for non-owner category members (#502)
    - ``setting_delete()`` function to ``AppSettingAPI`` (#538)
    - ``cleanappsettings`` management command (#374)
    - ``exclude_inherited`` argument in ``Project.get_delegates()`` (#595)
    - Value options for app settings of type ``STRING`` and ``INTEGER`` (#592)
    - Display placeholders for app setting form fields (#584)
    - Support for local user invites (#548, #613, #615, #621)
    - Local user account creation and updating (#547)
    - ``batchupdateroles`` management command (#15, #602)
    - Project invite REST API views (#15, #598)
    - Advanced search with multiple terms (#609)
    - Search result pagination control (#610)
    - REST API endpoint for retrieving current user info (#626)

Changed
-------

- **General**
    - Replace development helper scripts with ``Makefile`` (#135)
    - Upgrade to Bootstrap v4.5.3 and jQuery v3.5.1 (#563)
    - Upgrade to Chromedriver v87
    - Upgrade general Python requirements (#576)
    - Migrate GitHub CI from Travis to GitHub actions (#577)
    - Refactor example ``PROJECT_USER`` scope app settings (#599)
    - Set logging level in test configurations to ``CRITICAL`` (#604)
- **Filesfolders**
    - Update ``search()`` and ``find()`` for multiple search terms (#609)
- **Projectroles**
    - Allow updating local app settings on a ``TARGET`` site (#545)
    - Refactor project list filtering (#566)
    - Move project list javascript to ``project_list.js`` (#566)
    - Rename owner role transfer URL pattern and timeline event (#590)
    - Add ``sodar_url`` override to ``modify_assignment()``
    - Rename ``ProjectSearchResultsView`` and its template (#609)
    - Implement ``get_full_title()`` as ``Project.full_title`` field (#93)
    - Clarify invite accepting procedure in invite email (#627)
    - Redirect to home view when reusing accepted invite link (#628)
- **Userprofile**
    - Cosmetic updates for user detail template (#600)

Fixed
-----

- **Projectroles**
    - Invite redirect not working in Add Member view (#589)
    - Wrong role label displayed for category owner/delegate in member list (#593)
    - Django settings access in ``forms`` and ``serializers``
    - Delegate limit check broken by existing delegate roles of inherited owners (#595)
    - Crash in project invite if multiple users exist with the same email (#614)
    - Project delegate able to revoke invite for another delegate (#617)
    - Column alignment in invite list (#606)
    - ``get_not_found_alert()`` fails if called with app plugin search type (#624)
- **Taskflowbackend**
    - Django settings access in ``api`` (#605)
    - ``sodar_url`` override not working if ``request`` object is present (#605)

Removed
-------

- **General**
    - Travis CI setup in ``.travis.yml`` (#577)
- **Projectroles**
    - Template ``_project_filter_item.html`` (#566)
    - Template tag ``get_project_list()`` (#566)
    - Deprecate old implementation of ``ProjectAppPluginPoint.search()`` (#609, #618)
    - Deprecate ``Project.get_full_title()`` (#93)


v0.8.4 (2020-11-12)
===================

Changed
-------

- **General**
    - Documentation updates for JOSS submission


v0.8.3 (2020-09-28)
===================

Added
-----

- **General**
    - Missing migration for the ``SODARUser`` model (#581)

Changed
-------

- **General**
    - Upgrade to Chromedriver v85 (#569)
- **Projectroles**
    - Improve project list header legend (#571)
    - Make ``sync_source_data()`` atomic
    - Prevent creation of local projects under remote categories (#583)
- **Siteinfo**
    - Refactor app plugin statistics retrieval (#573)

Fixed
-----

- **General**
    - Invalid statement in ``setup_database.sh`` (#580)
- **Projectroles**
    - Missing exception handling for ``sync_source_data()`` calls (#582)
    - Crash from conflicting local category structure (#582)
- **Siteinfo**
    - Crash from exceptions raised by app plugin ``get_statistics()`` (#572)
- **Timeline**
    - CSS for ``sodar-tl-link-detail`` links (#578)

Removed
-------

- **General**
    - Unused ``Pillow`` dependency (#575)


v0.8.2 (2020-07-22)
===================

Added
-----

- **Bgjobs**
    - Enable site-wide background jobs (#544)
    - Site app plugin for site-wide background jobs (#544)
- **Projectroles**
    - ``sodar-header-button`` CSS class (#550)
    - Logging for ``AppSettingAPI`` (#559)

Changed
-------

- **Projectroles**
    - Upgrade to Chromedriver v83 (#543)
    - Rename ``is_app_link_visible()`` template tag into ``is_app_visible()`` (#546)
    - Refactor project list to reduce queries and template tag use (#551, #567)

Fixed
-----

- **Projectroles**
    - Transferring project ownership to inherited owner not allowed (#534)
    - Uniqueness constraint in ``AppSetting`` incompatible with ``PROJECT_USER`` scope settings (#542)
    - Inherited owner email address not displayed in project member list (#541)
    - App visibility check broken in ``project_detail.html`` (#546)
    - Invite accept for a category invoking Taskflow and causing a crash (#552)
    - Project form ``parent`` forced to wrong value if user lacks role in parent category (#558)
    - Invalid ``app_name`` not handled in ``AppSettingAPI.get_default_setting()`` (#560)
    - Empty JSON and false boolean app settings not set in project form (#557)
    - Minor Javascript errors thrown by ``projectroles.js`` (#536)
    - Long lines breaking email preview layout (#564)


v0.8.1 (2020-04-24)
===================

Added
-----

- **Projectroles**
    - CSS class ``sodar-pr-project-list-custom`` for custom project list items (#525)

Fixed
-----

- **Projectroles**
    - CSS padding issue with ``sodar-list-btn`` and Chrome (#529, sodar#844)
    - Crash from missing optional setting ``PROJECTROLES_DISABLE_CATEGORIES`` (#524)
    - Remote project editing not prevented in REST API views (#523)

Removed
-------

- **Projectroles**
    - Deprecated ``SODARAPIObjectInProjectPermissions`` base class (#527)


v0.8.0 (2020-04-08)
===================

Added
-----

- **General**
    - "For the Impatient" section in docs
- **Filesfolders**
    - API views for file, folder and hyperlink management (#443)
- **Projectroles**
    - Import new REST API view base classes from SODAR (#48, #461)
    - Import base serializers from SODAR (#462)
    - API views for project and role management (#48, #450)
    - ``projectroles.tests.test_views_api.TestAPIViewsBase`` for API view testing (#48)
    - ``SODARAPIPermissionTestMixin`` for API view permission tests
    - New helper methods in ``SODARAPIViewTestMixin``
    - Provide live server URL for Taskflow in ``TestTaskflowBase.request_data`` (#479)
    - ``TestTaskflowAPIBase`` for testing API views with SODAR Taskflow (#488)
    - Permission tests using Knox tokens (#476)
    - Base Ajax view classes in ``projectroles.views_ajax`` (#465)
    - Allow assigning roles for categories (#463)
    - Allow displaying project apps in categories with ``category_enable`` (#447)
    - Allow category delegates and owners to create sub-categories and projects (#464)
    - ``get_role_display_name()`` helper in ``projectroles_common_tags`` (#505)
    - ``get_owners()``, ``is_owner()`` and ``get_all_roles()`` helpers for ``Project`` (#464)
    - Allow using legacy UI test login method with ``PROJECTROLES_TEST_UI_LEGACY_LOGIN`` (#509)
    - Allow moving categories and projects under different categories (#512)
    - ``SODARForm`` and ``SODARModelForm`` base classes for forms
    - Enable retrieving flat recursive list of children objects in ``Project.get_children()``
    - Support for ``data`` in permission test ``assert_response()`` method (#155)
- **Taskflowbackend**
    - ``get_inherited_roles()`` helper (#464)
- **Timeline**
    - ``get_models()`` helper
- **Tokens**
    - Add app from varfish-web (#452)

Changed
-------

- **General**
    - Upgrade minimum Django version to v1.11.29 (#520)
    - Upgrade JQuery to v3.4.1 (#519)
    - Upgrade Bootstrap to v4.4.1 (#460)
    - General upgrade for Python package requirements (#124, #459)
    - Reorganize view classes and URL patterns (#480)
    - Refactor Ajax views (#465, #475)
    - Update ``CONTRIBUTING.rst``
    - Use ``SODARForm`` and ``SODARModelForm`` base classes in forms
- **Projectroles**
    - Suppress peer site removal logging if nothing was removed (#478)
    - Refactor ``SODARCoreAPIBaseView`` into ``SODARCoreAPIBaseMixin`` (#461)
    - Allow providing single user to ``assert_response()`` in permission tests (#474)
    - Move ``SODARAPIViewTestMixin`` into ``test_views_api`` and rename (#471)
    - Move ``KnoxAuthMixin`` functionality into ``SODARAPIViewTestMixin``
    - ``get_accept_header()`` in API tests returns header as dict
    - Refactor base permission test classes (#490)
    - Move ``utils.set_user_group()`` to ``SODARUser.set_group()`` (#483)
    - Call ``set_group()`` in ``SODARUser.save()`` (#483)
    - Replace ``projectroles_tags.is_app_hidden()`` with ``is_app_link_visible()``
    - Inherit owner permissions from parent categories (#464)
    - Refactor project roles template (#505)
    - Disable owner updating in project update form (#508)
    - Allow updating project parent via SODAR Taskflow (#512)
- **Taskflowbackend**
    - Refactor ``synctaskflow`` management command and add logging
- **Timeline**
    - Display app for categories (#447)

Fixed
-----

- **General**
    - Duplicate ``contributing.rst`` redirection file in docs (#481)
    - ``.tox`` not ignored in ``black.sh``
    - Coverage checks in Travis-CI (#507)
- **Projectroles**
    - Swapping owner and delegate roles not allowed if at delegate limit (#477)
    - Remote sync for owner role failing with specific user order in data (#439)
    - Redundant updating of ``Project.submit_status`` during project creation
    - Make ``test_widget_user_options()`` more reliable (#253)
    - Missing permission check by role type in ``RoleAssignmentDeleteView.post()`` (#492)
    - Unordered queryset warnings from the ``User`` model (#494)
    - Incorrect user iteration in ``test_user_autocomplete_ajax()`` (#469)
    - Redundant input validation preventing search with valid characters (#472)
    - Local users disabled in local development configuration (#500)
    - Member link not visible in responsive project dropdown (#466)
    - CSS issues with Bootstrap 4.4.1 in search pagination (#372, #460)
    - Raise ``ImproperlyConfigured`` for missing parameters in ``ProjectAccessMixin`` (#516)
- **Timeline**
    - CSS issues with Bootstrap 4.4.1 (#460)

Removed
-------

- **Projectroles**
    - ``SODARAPIBaseView`` base class, replaced by API view mixins (#461)
    - ``KnoxAuthMixin`` from view tests
    - ``get_selectable_users()`` from ``forms``
    - Redundant render/redirect helpers from ``TestPermissionBase``: use ``assert_response()`` instead (#484)
    - ``APIPermissionMixin`` for API views: use base API/Ajax view classes instead (#467)
    - ``is_app_hidden()`` from ``projectroles_tags``


v0.7.2 (2020-01-31)
===================

Added
-----

- **Projectroles**
    - ``custom_order`` argument in ``get_active_plugins()`` (#431)
    - Enable ordering custom project list columns in project app plugin (#427)
    - ``SODARCoreAPIBaseView`` base API view class for internal SODAR Core apps (#442)
    - API version enforcing in ``RemoteProjectsSyncView`` and ``syncremote.py`` (#444)
    - Allow extra keyword arguments in ``get_backend_api()`` (#397)
    - Example usage of ``get_backend_api()`` extra kwargs in ``example_backend_app`` (#397)
    - ``SODARUserChoiceField`` and ``get_user_widget()`` for user selection in forms (#455)
    - Setting ``reply-to`` headers for role change and invite emails (#446)
    - No reply note and related ``PROJECTROLES_EMAIL_SENDER_REPLY`` setting (#446)
    - Display hidden project app settings to superusers (#424)
- **Sodarcache**
    - Allow limiting ``deletecache`` to a specific project (#448)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.27
    - Base ``RemoteProjectGetAPIView`` on ``SODARCoreAPIBaseView`` (#442)
    - Upgrade to Chromedriver v80 (#510)
- **Bgjobs**
    - Make ``specialize_job()`` more robust (#456)
- **Projectroles**
    - Accept null value for ``AppSetting.value_json`` (#426)
    - Use ``PluginContextMixin`` in ``ProjectContextMixin`` (#430)
    - Move ``get_accept_header()`` to ``SODARAPIViewMixin`` (#445)
    - Allow exceptions to be raised by ``get_backend_plugin()`` (#451)
    - Improve tour help CSS (#438)
    - Field order in ``RoleAssignmentOwnerTransferView`` (#441)
    - Redesign user autocomplete handling in forms (#455)
    - Rename ``SODARUserAutocompleteWidget`` and ``SODARUserRedirectWidget`` (#455)
    - Disable ownership transfer link if owner is the only project user (#454)

Fixed
-----

- **Projectroles**
    - Potential crash in ``_project_header.html`` with ownerless kiosk mode category (#422)
    - Form crash when saving a JSON app setting with ``user_modifiable=False`` (#426)
    - Inconsistent plugin ordering in custom project list columns (#428)
    - Project app plugins included twice in ``HomeView`` (#432)
    - ``ProjectPermissionMixin`` query set override with ``get_project_filter_key()``
    - Search disabled with unchanged input value on search page load (#436)
    - Subprojects queried for non-categories in ``project_detail.html`` (#434)
    - Current owner selectable in ownership transfer form (#440)
- **Taskflowbackend**
    - Potential crash in ``TaskflowAPI`` initialization

Removed
-------

- **Projectroles**
    - Unused backend plugins queried for context data in ``HomeView`` (#433)
    - Unneeded ``UserAutocompleteExcludeMembersAPIView`` (#455)


v0.7.1 (2019-12-18)
===================

Added
-----

- **General**
    - Include CHANGELOG in documentation (#379)
- **Projectroles**
    - ``widget_attrs`` parameter for project and user settings (#404)
    - Remote project member management link for target projects (#382)
    - Current user in ``get_project_list_value()`` arguments (#413)
    - Display category owner in page header (#414)
    - Configuring UI test settings via Django settings or ``TestUIBase`` vars (#417)
    - Initial support for deploying site in kiosk mode (#406)
    - Optional disabling of default CDN Javascript and CSS includes (#418)
    - Defining custom global JS/CSS includes in Django settings (#418)

Changed
-------

- **General**
    - Change "Breaking Changes" doc into "Major Changes" (#201)
    - Refactor and rename ownership transfer classes and template
    - Use RTD theme in documentation (#384)
    - Upgrade to Chromedriver v79
- **Adminalerts**
    - Rename ``INACTIVE`` alert state in UI (#396)
    - Rename URL name and pattern for activation API view (#378)
    - Improve alert detail page layout (#385)
- **Projectroles**
    - Improve unsupported browser warning (#405)
    - Move project list description into tooltip (#388)
- **Siteinfo**
    - Improve page title and heading (#402)
- **Sodarcache**
    - Clarify management command logging (#403)
- **Timeline**
    - Improve extra data status tab legend (#380)

Fixed
-----

- **General**
    - PPA used for Python 3.6 installs no longer available (#416)
- **Filesfolders**
    - Invalid HTML in project list extra columns
- **Projectroles**
    - Dismissing login error alert in ``login.html`` not working (#377)
    - Current owner queries incorrectly filtered in ``RoleAssignmentOwnerTransferView`` (#393)
    - Hardcoded project type display name in sent emails (#398)
    - Silent failing of invalid app setting type in plugin definition (#390)
    - Exception raised by hidden sidebar in sidebar height calculation (#407)
    - Crash in ``get_default_setting()`` if default JSON value was not set (#389)
    - Owner widget hidden in category update view (#394)
    - Project list extra column header alignment not set (#412)
    - ``get_project_list_value()`` template tag displaying "None" on null value (#411)


v0.7.0 (2019-10-09)
===================

Added
-----

- **General**
    - Development env file example ``env.example`` (#297)
    - Postgres database development setup script (#302)
    - ``ENABLE_DEBUG_TOOLBAR`` setting for local development (#349)
    - ``local_target2.py`` config for peer remote site development (#200)
- **Adminalerts**
    - Activate/suspend button in alert list (#42)
- **Bgjobs**
    - Pagination for background job list (#335)
    - ``BGJOBS_PAGINATION`` Django setting (#335)
- **Projectroles**
    - ``get_backend_include()`` common template tag (#261)
    - ``css_url`` member variable in ``BackendPluginPoint`` (#261)
    - Example of on-demand Javascript/CSS inclusion in example apps (#261)
    - Remote project link display toggle for target sites (#276)
    - Project UUID clipboard copying button (#290)
    - Support for app settings in site apps (#308)
    - Initial implemenetation for common clipboard copying visualization (#333)
    - Send email for owner role assignment (#325)
    - Common pagination include template ``_pagination.html`` (#334)
    - Synchronization and display of ``PEER`` sites in remote site management (#200)
    - Link for copying remote site secret token in remote site list (#332)
    - Project ownership transfer from member list (#287)
    - UI notification for disabled member management on target sites (#301)
    - Management command ``addremotesite`` for adding remote sites (#314)
    - JSON support for app settings (#268)
    - ``get_setting_def()`` in app settings API
    - Timeline logging of app settings in project creation (#359)
    - "Project and user" scope for app settings (#266)
    - ``REVOKED`` status for remote projects with revoked access (#327)
    - ``Project.is_revoked()`` helper (#327)
    - Disabling access for non-owner/delegate for revoked projects in ``ProjectPermissionMixin`` (#350)
- **Timeline**
    - Display event extra data as JSON (#6)
- **Userprofile**
    - User setting for project UUID clipboard copying (#290, #308)

Changed
-------

- **General**
    - Upgrade Chromedriver to version 77.0.3865.40
    - Use ``CurrentUserFormMixin`` instead of repeated code (#12)
    - Run tests in parallel where applicable
    - Upgrade minimum Django version to 1.11.25 (#346)
    - General upgrade for Python package requirements (#282)
- **Adminalerts**
    - Use common pagination template
- **Projectroles**
    - Improve user name placeholder in ``login.html`` (#294)
    - Backend app Javascript and CSS included on-demand instead of for all templates (#261)
    - Make sidebar hiding dynamic by content height (#316)
    - Replace ``login_and_redirect()`` in UI tests with a faster cookie based function (#323)
    - Refactor remote project display on details page (#196)
    - Refactor AppSettingAPI (#268)
    - Enable calling ``AppSettingAPI.get_setting_defs()`` with app name instead of plugin object
    - Use ``ProjectPermissionMixin`` on project detail page (#350)
- **Timeline**
    - Use common pagination template (#336)

Fixed
-----

- **Projectroles**
    - Output of template tag ``get_project_link()``
    - Redundant inheritance in ``CurrentUserFormMixin`` (#12)
    - Trailing slashes not parsed correctly in remote project URLs (#319)
    - Crash in ``get_project_column_count()`` with no active project app plugins (#320)
    - UI test helper ``build_selenium_url()`` refactored to work with Chrome v77 (#337)
    - Disallow empty values in ``RemoteSite.name``
    - Remote sync of parent category roles could fail with multiple subprojects
    - ``RemoteProject`` modifications not saved during sync update
    - Timeline events not created in remote project sync (#370)
    - DAL select modifying HTML body width (#365)
    - Footer overflow breaking layout (#367, #375)
- **Timeline**
    - Crash from exception raised by ``get_object_link()`` in a plugin (#328)

Removed
-------

- **Projectroles**
    - Duplicate database indexes from ``RoleAssignment`` (#285)
    - Deprecated ``get_setting()`` tag from ``projectroles_common_tags`` (#283)
    - Project owner change from project updating form (#287)
    - ``ProjectSettingMixin`` from ``projectoles.tests.test_views`` (#357)


v0.6.2 (2019-06-21)
===================

Added
-----

- **General**
    - Badges for Readthedocs documentation and Zenodo DOI (#274)
- **Bgjobs**
    - ``BackgroundJobFactory`` for tests from Varfish-web
- **Projectroles**
    - Unit test to assure owner user creation during project update when using SODAR Taskflow (sodar_taskflow#49)
    - Common template tag ``get_app_setting()`` (#281)
    - Hiding app settings from forms with ``user_modifiable`` (#267)
    - ``AppSetting.value_json`` field (#268)
- **Sodarcache**
    - Logging in ``delete_cache()`` (#279)
- **Userprofile**
    - Support for ``AppSetting.user_modifiable`` (#267)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.21 (#278)
- **Projectroles**
    - ``get_setting()`` template tag renamed into ``get_django_setting()`` (#281)
    - Implement project app descriptions on details page with ``get_info_link()`` (#277)

Fixed
-----

- **General**
    - Documentation sections for Readthedocs


v0.6.1 (2019-06-05)
===================

Added
-----

- **Filesfolders**
    - Example project list columns (#265)
    - Setting ``FILESFOLDERS_SHOW_LIST_COLUMNS`` to manage example project list columns (#265)
- **Projectroles**
    - Optional project list columns for project apps (#265)
- **Sodarcache**
    - ``delete_cache()`` API function (#257)

Changed
-------

- **Projectroles**
    - Refactor ``RemoteProject.get_project()`` (#262)
    - Use ``get_info_link()`` in remote site list (#264)
    - Define ``SYSTEM_USER_GROUP`` in ``SODAR_CONSTANTS`` (#251)
    - Make pagedown textarea element resizeable and increase minimum height (#273)
- **Sodarcache**
    - Handle and log raised exceptions in ``synccache`` management command (#272)
- **Userprofile**
    - Disable user settings link if no settings are available (#260)

Fixed
-----

- **General**
    - Chrome and Chromedriver version mismatch in Travis-CI config (#254)
- **Projectroles**
    - Remove redundant ``get_project_list()`` call from ``project_detail.html``

Removed
-------

- **Projectroles**
    - Unused project statistics in the home view (#269)
    - App settings deprecation protection (#245)
- **Sodarcache**
    - Unused ``TaskflowCacheUpdateAPIView`` (#205)


v0.6.0 (2019-05-10)
===================

Added
-----

- **Filesfolders**
    - Provide app statistics for siteinfo (#18)
- **Projectroles**
    - User settings for settings linked to users instead of projects (#16)
    - ``user_settings`` field in project plugins (#16)
    - Optional ``label`` key for settings
    - Optional "wait for element" args in UI test helpers to ease Javascript testing (#230)
    - ``get_info_link()`` template tag (#239)
    - ``get_setting_defs()`` API function for retrieving project and user setting definitions (#225)
    - ``get_all_defaults()`` API function for retrieving all default setting values (#225)
    - Human readable labels for app settings (#9)
- **Siteinfo**
    - Add app for site info and statistics (#18)
- **Sodarcache**
    - Optional ``--project`` argument for the ``synccache`` command (#232)
- **Timeline**
    - Provide app statistics for siteinfo (#18)
- **Userprofiles**
    - View and form for displaying and updating user settings (#16)

Changed
-------

- **General**
    - Upgrade to ChromeDriver v74 (#221)
- **Bgjobs**
    - Job order to match downstream Varfish
- **Filesfolders**
    - Update app settings (#246)
- **Projectroles**
    - Rename ``project_settings`` module to ``app_settings`` (#225)
    - App settings API updated to support project and user settings (#225)
    - Write an empty dict for ``app_settings`` by default

Fixed
-----

- **Bgjobs**
    - Date formatting in templates (#220)
- **Sodarcache**
    - Crash from ``__repr__()`` if project not set (#223)
    - Broken backend plugin icon (#250)

Removed
-------

- **Timeline**
    - Unused and deprecated project settings (#246)


v0.5.1 (2019-04-16)
===================

Added
-----

- **General**
    - Bgjobs/Celery updates from Kiosc (#175)
    - Default error templates in ``projectroles/error/*.html`` (#210)
- **Projectroles**
    - Optional ``user`` argument in ``ProjectAppPlugin.update_cache()`` (#203)
    - Migration for missing ``RemoteProject`` foreign keys (#197)
- **Sodarcache**
    - API logging (#207)
    - Indexing of identifying fields (#218)

Changed
-------

- **General**
    - Extend ``projectroles/base.html`` for all site app templates, update docs (#217)
    - Use projectroles error templates on the example site (#210)
- **Sodarcache**
    - Make ``user`` field optional in models and API (#204)
    - Rename app configuration into ``SodarcacheConfig`` to follow naming conventions (#202)
    - Rename ``updatecache`` management command to ``synccache`` (#208)

Fixed
-----

- **General**
    - Add missing curl dependency in ``install_os_dependencies.sh`` (#211)
    - Django debug toolbar not displayed when using local configuration (#213)
- **Projectroles**
    - Nested app names not properly returned by ``utils.get_app_names()`` (#206)
    - Forced width set for all Bootstrap modals in ``projectroles.css`` (#209)
    - Long category paths breaking remote project list (#84)
    - Incorrect table rows displayed during project list initialization (#212)
    - Field ``project`` not set for source site ``RemoteProject`` objects (#197)
    - Crash from ``project_base.html`` in site app if not overriding title block (#216)

Removed
-------

- **General**
    - Django debug toolbar workarounds from ``project.css`` and ``project.scss`` (#215)
- **Projectroles**
    - ``PROJECTROLES_ADMIN_OWNER`` deprecation protection: use ``PROJECTROLES_DEFAULT_ADMIN`` (#190)


v0.5.0 (2019-04-03)
===================

Added
-----

- **Projectroles**
    - Warning when using an unsupported browser (#176)
    - Setting ``PROJECTROLES_BROWSER_WARNING`` for unsupported browser warning (#176)
    - Javascript-safe toggle for ``get_setting()`` template tag
    - ID attributes in site containers (#173)
    - Setting ``PROJECTROLES_ALLOW_LOCAL_USERS`` for showing and syncing non-LDAP users (#193)
    - Allow synchronizing existing local target users for remote projects (#192)
    - Allow selecting local users if in local user mode (#192)
    - ``RemoteSite.get_url()`` helper
    - Simple display of links to project on external sites in details page (#182)
- **Sodarcache**
    - Create app (#169)

Changed
-------

- **General**
    - Upgrade to Bootstrap 4.3.1 and Popper 1.14.7 (#181)
- **Projectroles**
    - Improve remote project sync logging (#184, #185)
    - Rename ``PROJECTROLES_ADMIN_OWNER`` into ``PROJECTROLES_DEFAULT_ADMIN`` (#187)
    - Update login template and ``get_login_info()`` to support local user mode (#192)

Fixed
-----

- **Projectroles**
    - Crash in ``get_assignment()`` if called with AnonymousUser (#174)
    - Line breaks in templates breaking ``badge-group`` elements (#180)
    - User autocomplete for users with no group (#199)

Removed
-------

- **General**
    - Deprecated Bootstrap 4 workaround from ``project.js`` (#178)


v0.4.5 (2019-03-06)
===================

Added
-----

- **Projectroles**
    - User autocomplete widgets (#51)
    - Logging in ``syncgroups`` and ``syncremote`` management commands
    - ``PROJECTROLES_DELEGATE_LIMIT`` setting (#21)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.20 (#152)
    - Use user autocomplete in forms in place of standard widget (#51)
- **Filesfolders**
    - Hide parent folder widgets in item creation forms (#159)
- **Projectroles**
    - Enable allowing multiple delegates per project (#21)

Fixed
-----

- **Filesfolders**
    - File upload wiget error not displayed without Bootstrap 4 workarounds (#164)
- **Projectroles**
    - Potential crash in ``syncremote`` if run as Celery job (#160)

Removed
-------

- **General**
    - Old Bootstrap 4 workarounds for django-crispy-forms (#157)


v0.4.4 (2019-02-19)
===================

Changed
-------

- **Projectroles**
    - Modify ``modifyCellOverflow()`` to work with non-table containers (#149)
    - Non-Pagedown form textarea height no longer adjusted automatically (#151)

Fixed
-----

- **Projectroles**
    - Crash in remote project sync caused by typo in ``remoteproject_sync.html`` (#148)
    - Textarea element CSS override breaking layout in third party components (#151)


v0.4.3 (2019-01-31)
===================

Added
-----

- **General**
    - Codacy badge in ``README.rst`` (#140)
- **Projectroles**
    - Category and project display name configuration via ``SODAR_CONSTANTS`` (#141)
    - ``get_display_name()`` utils function and template tag to retrieve ``DISPLAY_NAMES`` (#141)
    - Django admin link warning if taskflowbackend is enabled

Changed
-------

- **General**
    - Use ``get_display_name()`` to display category/project type (#141)
- **Projectroles**
    - Hide immutable fields in forms (#142)
    - Rename Django admin link in user dropdown

Fixed
-----

- **Projectroles**
    - View access control for categories (#143)

Removed
-------

- **General**
    - Redundant ``rules.is_superuser`` predicates from rules (#138)
- **Projectroles**
    - ``get_project_type()`` template tag (use ``get_display_name()`` instead)
    - Unused template ``_roleassignment_import.html``
    - ``PROJECT_TYPE_CHOICES`` from ``SODAR_CONSTANTS``
    - ``force_select_value()`` helper no longer used in forms (#142)


v0.4.2 (2019-01-25)
===================

Added
-----

- **General**
    - Flake8 and Codacy coverage in Travis-CI (#122)
    - Flake8 in GitLab-CI (#127)
- **Projectroles**
    - Automatically pass CSRF token to unsafe Ajax HTTP methods (#116)
    - Queryset filtering in ``ProjectPermissionMixin`` from digestiflow-web (#134)
    - Check for ``get_project_filter_key()`` from digestiflow-web (#134)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.18 (#120)
    - Upgrade Python dependencies (#123)
    - Update .coveragerc
    - Upgrade to Bootstrap 4.2.1 (#23)
    - Upgrade to JQuery 3.3.1 (#23)
    - General code cleanup
    - Code formatting with Black (#133)
- **Filesfolders**
    - Refactor ``BatchEditView`` and ``FileForm.clean()`` (#128)
- **Projectroles**
    - Use ``alert-dismissable`` to dismiss alerts (#13, #130)
    - Update DataTables dependency in ``search.html`` template
    - Refactor ``ProjectModifyMixin`` and ``RemoteProjectAPI`` (#128)
    - Disable ``USE_I18N`` in example site settings (#117)
    - Refactor ``ProjectAccessMixin._get_project()`` into ``get_project()`` (#134)
    - Rename ``BaseAPIView`` into ``SODARAPIBaseView``
- **Timeline**
    - Refactor ``get_event_description()`` (#30, #128)

Fixed
-----

- **General**
    - Django docs references (#131)
- **Projectroles**
    - ``sodar-list-dropdown`` layout broke down with Bootstrap 4.2.1 (#23)
    - ``TASKFLOW_TEST_MODE`` not checked for allowing SODAR Taskflow tests (#126)
    - Typo in ``update_remote`` timeline event description (#129)
    - Textarea height modification (#125)
    - Text wrapping in ``sodar-list-btn`` and ``sodar-list-dropdown`` with Bootstrap 4.2.1 (#132)
- **Taskflowbackend**
    - ``TASKFLOW_TEST_MODE`` not checked for allowing ``cleanup()`` (#126)
    - ``FlowSubmitException`` raised instead of ``CleanupException`` in ``cleanup()``

Removed
-------

- **General**
    - Legacy Python2 ``super()`` calls (#118)
- **Projectroles**
    - Custom alert dismissal script (#13)
- **Example Site App**
    - Example file ``test.py``


v0.4.1 (2019-01-11)
===================

Added
-----

- **General**
    - Travis-CI configuration (#90)
- **Adminalerts**
    - Option to display alert to unauthenticated users with ``require_auth`` (#105)
- **Projectroles**
    - ``TaskflowAPIAuthentication`` for handling Taskflow API auth (#47)
    - Handle ``GET`` requests for Taskflow API views (#47)
    - API version settings ``SODAR_API_ALLOWED_VERSIONS`` and ``SODAR_API_MEDIA_TYPE`` (#111)
    - Site app support in ``change_plugin_status()``
    - ``get_sodar_constants()`` helper (#112)
- **Taskflowbackend**
    - API logging

Changed
-------

- **General**
    - Upgrade minimum Python version requirement to 3.6 (#102)
    - Update and cleanup Gitlab-CI setup (#85)
    - Update Chrome Driver for UI tests
    - Cleanup Chrome setup
    - Enable site message display in login view (#105)
    - Cleanup and refactoring for public GitHub release (#90)
    - Drop support for Ubuntu Jessie and Trusty
    - Update installation utility scripts (#90)
- **Filesfolders**
    - Move inline javascript into ``filesfolders.js``
- **Projectroles**
    - Refactor ``BaseTaskflowAPIView`` (#47)
    - Rename Taskflow specific API views (#104)
    - Unify template tag names in ``projectroles_tags``
    - Change default SODAR API media type into ``application/vnd.bihealth.sodar-core+json`` (#111)
    - Allow importing ``SODAR_CONSTANTS`` into settings for modification (#112)
    - Move ``SODAR_CONSTANTS`` to ``constants.py`` (#112)
- **Timeline**
    - Rename Taskflow specific API views (#104)

Fixed
-----

- **Filesfolders**
    - Overwrite check for zip archive upload if unarchiving was unset (#113)
- **Projectroles**
    - Potential Django crash from auth failure in Taskflow API views
    - Timeline description for updating a remote project
    - Project update with Taskflow failure if description not set (#110)
- **Timeline**
    - ``TaskflowEventStatusSetAPIView`` skipping ``sodar_token`` check (#109)

Removed
-------

- **Filesfolders**
    - Unused dropup app buttons mode in templates (#108)
- **Projectroles**
    - Unused arguments in ``email`` API
    - Unused static file ``shepherd-theme-default.css``
    - Disabled role importing functionality (#61, pending #17)
    - Unused dropup app buttons mode in templates (#108)
- **Timeline**
    - ``ProjectEventStatus.get_timestamp()`` helper


v0.4.0 (2018-12-19)
===================

Added
-----

- **General**
    - ``SODAR_API_DEFAULT_HOST`` setting for server host for API View URLs (sodar#396)
- **Bgjobs**
    - Add app from varfish-web (#95)
- **Filesfolders**
    - Add app from sodar v0.4.0 (#86)
- **Projectroles**
    - Setting ``PROJECTROLES_ENABLE_SEARCH`` (#70)
    - Re-enable "home" link in project breadcrumb (#80)
    - ``get_extra_data_link()`` in ProjectAppPluginPoint for timeline extra data (#6)
    - Allow overriding project class in ProjectAccessMixin
    - Optional disabling of categories and nesting with ``PROJECTROLES_DISABLE_CATEGORIES`` (#87)
    - Optional hiding of apps from project menus using ``PROJECTROLES_HIDE_APP_LINKS`` (#92)
    - Secure SODAR Taskflow API views with ``TASKFLOW_SODAR_SECRET`` (#46)
- **Taskflowbackend**
    - ``test_mode`` flag configured with ``TASKFLOW_TEST_MODE`` in settings (#67)
    - Submit ``sodar_secret`` for securing Taskflow API views (#46)
- **Timeline**
    - Display of extra data using ``{extra-NAME}`` (see documentation) (#6)

Changed
-------

- **General**
    - Improve list button and dropdown styles (#72)
    - Move pagedown CSS overrrides into ``projectroles.css``
    - Reduce default textarea height (#96)
- **Projectroles**
    - Make sidebar resizeable in CSS (#71)
    - Disable search if ``PROJECTROLES_ENABLE_SEARCH`` is set False (#70)
    - Allow appending custom items in project breadcrumb with ``nav_sub_project_extend`` block (#78)
    - Allow replacing project breadcrumb with ``nav_sub_project`` block (#79)
    - Disable remote site access if ``PROJECTROLES_DISABLE_CATEGORIES`` is set (#87), pending #76
    - Disable access to invite views for remote projects (#89)
    - Set "project guest" as the default role for new members (#94)
    - Make noncritical settings variables optional (#14)

Fixed
-----

- **General**
    - Potential inheritance issues in test classes (#74)
    - LDAP dependency script execution (#75)
- **Projectroles**
    - Long words in app names breaking sidebar (#71)
    - Member modification buttons visible for superuser in remote projects (#73)
    - Breadcrumb project detail link display issue in ``base.html`` (#77)
    - "None" string displayed for empty project description (#91)
    - Crash in search from empty project description


v0.3.0 (2018-10-26)
===================

Added
-----

- **General**
    - Test config and script for SODAR Taskflow testing
- **Adminalerts**
    - Add app based on SODAR v0.3.3 (#27)
    - ``TASKFLOW_TARGETS`` setting
- **Projectroles**
    - ``RemoteSite`` and ``RemoteProject`` models (#3)
    - ``RemoteSiteAppPlugin`` site plugin (#3)
    - ``PROJECTROLES_SITE_MODE`` and ``PROJECTROLES_TARGET_CREATE`` settings (#3)
    - Remote site and project management site app (#3)
    - Remote project API (#3)
    - Generic SODAR API base classes
    - ``SodarUserMixin`` for SODAR user helpers in tests
    - Optional ``readme`` and ``sodar_uuid`` args for ``_make_project()`` in tests
    - ``syncremote`` management command for calling ``RemoteProjectAPI.sync_source_data()``
    - ``get_project_by_uuid()`` and ``get_user_by_username()`` template tags
    - ``get_remote_icon()`` template tag (#3)
    - Predicates in rules for handling remote projects (#3)
    - ``ProjectModifyPermissionMixin`` for access control for remote projects (#3)
    - ``is_remote()`` and ``get_source_site()`` helpers in the ``Project`` model (#3)
    - Include template ``_titlebar_nav.html`` for additional title bar links
- **Taskflowbackend**
    - Add app based on SODAR v0.3.3 (#38)
- **Timeline**
    - ``RemoteSite`` model in ``api.get_event_description()`` (#3)

Changed
-------

- **General**
    - Update documentation for v0.3 changes, projectroles usage and fixes to v0.2 docs (#26)
- **Adminalerts**
    - Make ``ADMINALERTS_PAGINATION`` setting optional
- **Projectroles**
    - Allow ``LoggedInPermissionMixin`` to work without a permission object for superusers
    - Enable short/full title selection and remote project icon in ``get_project_link()`` template tag
    - Refactor rules
    - Disable Taskflow API views if Taskflow backend is not enabled (#37)
    - DataTables CSS and JS includes loaded in the search template (#45)
- **Timeline**
    - Minor refactoring of ``api.get_event_description()`` (#30)

Fixed
-----

- **General**
    - Pillow dependency typo in ``requirements/base.txt`` (#33)
    - Login page crash if ``AUTH_LDAP*_DOMAIN_PRINTABLE`` not found (#43)
- **Projectroles**
    - Sidebar create project visible for site apps if URL name was "create" (#36)
    - Enabling LDAP without a secondary backend caused a crash (#39)

Removed
-------

- **General**
    - iRODS specific CSS classes from ``projectroles.css``
    - App content width limit in ``projectroles.css``
    - Domain-specific Login JQuery
    - DataTables CSS and JS includes from base template (#45)


v0.2.1 (2018-09-20)
===================

Changed
-------

- **General**
    - Change ``omics_uuid`` field in all apps' models to ``sodar_uuid`` (sodar#166)
- **Projectroles**
    - Rename abstract ``OmicsUser`` model into ``SODARUser`` (sodar#166)
    - Rename ``OMICS_CONSTANTS`` into ``SODAR_CONSTANTS`` (sodar#166)
    - Rename the ``omics_constant()`` template tag into ``sodar_constant()`` (sodar#166)
    - Rename ``omics_url`` in sodar_taskflow tests to ``sodar_url`` (see sodar_taskflow#36)
    - Rename ``shepherd-theme-omics.css`` to ``shepherd-theme-sodar.css`` (sodar#166)


v0.2.0 (2018-09-19)
===================

Added
-----

- **General**
    - ``example_backend_app`` for a minimal backend app example
    - Backend app usage example in ``example_project_app``
- **Timeline**
    - Add timeline app based on SODAR v0.3.2 (#2)
    - App documentation

Changed
-------

- **General**
    - Update integration documentation (#1)
    - Restructure documentation files and filenames for clarity
- **Timeline**
    - Update CSS classes and overrides
    - Rename list views to ``list_project`` and ``list_objects``
    - Rename list template to ``timeline.html``
    - Refactor ``api.get_event_description()``
    - Make ``TIMELINE_PAGINATION`` optional
    - Improve exception messages in ``api.add_event()``

Fixed
-----

- **Timeline**
    - User model access in ``timeline.api``
    - Misaligned back button (#4)
    - Deprecated CSS in main list
- **Projectroles**
    - Third party apps not correctly recognized in ``get_app_names()``


v0.1.0 (2018-09-12)
===================

Added
-----

- **General**
    - Create app package for Projectroles and other reusable apps based on SODAR release v0.3.1
    - ``example_project_app`` to aid testing and work as a minimal example
    - ``example_site_app`` for demonstrating site apps
    - ``SITE_TITLE`` and ``SITE_INSTANCE_TITLE`` settings
    - ``SITE_PACKAGE`` setting for explicitly declaring site path for code
    - Documentation for integration and development
    - Separate LDAP config in ``install_ldap_dependencies.sh`` and ``requirements/ldap.txt``

- **Projectroles**
    - ``static_file_exists()`` and ``template_exists()`` helpers in common template tags
    - Abstract ``OmicsUser`` model
    - ``get_full_name()`` in abstract OmicsUser model
    - ``auth_backends.py`` file for LDAP backends (sodar#132)
    - Versioneer versioning
    - ``core_version()`` in common template tags
    - Check for footer content in ``include/_footer.html``
    - Example of the site base template in ``projectroles/base_site.html``
    - Example of project footer in ``projectroles/_footer.html``

- **Userprofile**
    - Add site app ``userprofile`` with user details
    - Display user UUID in user profile

Changed
-------

- **Projectroles**
    - Move custom modal into ``projectroles/_modal.html``
    - Check for user.name in user dropdown
    - Move content block structure and sidebar inside ``projectroles/base.html``
    - Move site title bar into optional include template ``projectroles/_site_titlebar.html``
    - Move search form into optional include template ``projectroles/_site_titlebar_search.html``
    - Make title bar dropdown inclueable as ``_site_titlebar_dropdown.html``
    - Title bar CSS and layout tweaks
    - Move ``search.js`` under projectroles
    - Move projectroles specific javascript into ``projectroles.js``
    - Move ``site_version()`` into common template tags
    - Move title bar admin and site app links to user dropdown (sodar#342)
    - Move project specific CSS into optionally includable ``projectroles.css``
    - Refactor and cleanup CSS
    - Move ``set_user_group()`` into ``projectroles.utils``
    - Move ``syncgroups`` management command into projectroles
    - Copy improved multi LDAP backend setup from flowcelltool (sodar#132)
    - Move LDAP authentication backends into projectroles (sodar#132)
    - Move ``login.html`` into projectroles
    - Display ``SITE_INSTANCE_TITLE`` in email instead of a hardcoded string
    - Display the first contact in ``settings.ADMINS`` in email footer
    - Use ``get_full_name()`` in email sending
    - Get site version using ``SITE_PACKAGE``
    - Get LDAP domain names to login template from settings
    - Rename custom CSS classes and HTML IDs from ``omics-*`` into ``sodar-*`` (sodar#166)
    - Move Shepherd theme CSS files into projectroles

Fixed
-----

- **Projectroles**
    - Tests referring to the ``filesfolders`` app not included in this project
    - ``TestHomeView.test_render()`` assumed extra SODAR system user was present (see sodar#367)
    - Tour link setup placing

- **Userprofile**
    - Missing user name if ``name`` field not filled in ``user_detail.html``

Removed
-------

- **Projectroles**
    - Deprecated Javascript variables ``popupWaitHtml`` and ``popupNoFilesHtml``
    - Unused template ``irods_info.html``
