"""Sodarcache API for adding and updating cache items"""

import logging

from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

# Projectroles dependency
from projectroles.models import Project, SODARUser
from projectroles.plugins import PluginAPI
from projectroles.utils import get_app_names

from sodarcache.models import JSONCacheItem


logger = logging.getLogger(__name__)
plugin_api = PluginAPI()
User = get_user_model()


# Local variables
APP_NAMES = get_app_names()
LABEL_MAX_WIDTH = 32
CACHE_TYPES = ['json']


class SODARCacheAPI:
    """SODARCache backend API to be used by Django apps."""

    # TODO: Make model selection dynamic once we introduce types other than JSON

    # Internal functions -------------------------------------------------------

    @classmethod
    def _check_app_name(cls, app_name: str):
        """Check if app_name is valid, raise ValueError if not"""
        if app_name not in APP_NAMES:
            raise ValueError(
                'Unknown app name "{}" (installed apps: {})'.format(
                    app_name, ', '.join(x for x in APP_NAMES)
                )
            )

    @classmethod
    def _check_data_type(cls, data_type: str):
        """Check if data_type is valid, raise ValueError if not"""
        if data_type not in CACHE_TYPES:
            raise ValueError(
                'Unknown data type "{}" for a cache item '
                '(allowed types: {})'.format(
                    data_type, ', '.join(x for x in CACHE_TYPES)
                )
            )

    # API functions ------------------------------------------------------------

    @classmethod
    def get_project_cache(
        cls, project: Project, data_type: str = 'json'
    ) -> QuerySet:
        """
        Return all cached data for a project.

        :param project: Project object
        :param data_type: String stating the data type of the cache items
        :return: QuerySet
        :raise: ValueError if data_type is invalid
        """
        cls._check_data_type(data_type)
        return JSONCacheItem.objects.filter(project=project)

    @classmethod
    def update_cache(
        cls,
        name: Optional[str] = None,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Update items by certain name within a project by calling implemented
        functions in project app plugins.

        :param name: Item name to limit update to (string, optional)
        :param project: Project object to limit update to (optional)
        :param user: User object to denote user triggering the update (optional)
        """
        plugins = plugin_api.get_active_plugins(plugin_type='project_app')
        for plugin in plugins:
            plugin.update_cache(name, project, user)

    @classmethod
    def delete_cache(
        cls, app_name: Optional[str] = None, project: Optional[Project] = None
    ) -> int:
        """
        Delete cache items. Optionallly limit to project and/or user.

        :param app_name: Name of the app which sets the item (string)
        :param project: Project object (optional)
        :return: Integer (deleted item count)
        :raise: ValueError if app_name is given but invalid
        """
        if app_name:
            cls._check_app_name(app_name)
        if not app_name and not project:
            items = JSONCacheItem.objects.all()
        else:
            query_params = {}
            if app_name:
                query_params['app_name'] = app_name
            if project:
                query_params['project'] = project
            items = JSONCacheItem.objects.filter(**query_params)

        if items:
            item_count = items.count()
            items.delete()
            logger.info(
                'Deleted {} item{} from cache(app={}, project={})'.format(
                    item_count,
                    's' if item_count != 1 else '',
                    app_name,
                    project.sodar_uuid if project else None,
                )
            )
            return item_count

        logger.info(
            'No items found for deletion (app={}, project={})'.format(
                app_name, project.sodar_uuid if project else None
            )
        )
        return 0

    @classmethod
    def get_cache_item(
        cls, app_name: str, name: str, project: Optional[Project] = None
    ) -> JSONCacheItem:
        """
        Return cached data by app_name, name (identifier) and optional project.
        Returns None if not found.

        :param name: Item name (string)
        :param app_name: Name of the app which sets the item (string)
        :param project: Project object (optional)
        :return: JSONCacheItem object
        :raise: ValueError if app_name is invalid
        """
        cls._check_app_name(app_name)
        query_string = {'app_name': app_name, 'name': name}
        if project:
            query_string['project'] = project
        return JSONCacheItem.objects.filter(**query_string).first()

    @classmethod
    def set_cache_item(
        cls,
        app_name: str,
        name: str,
        data: dict,
        data_type: str = 'json',
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ) -> JSONCacheItem:
        """
        Create or update and save a cache item.

        :param app_name: Name of the app which sets the item (string)
        :param name: Item name (string)
        :param data: Item data (dict)
        :param data_type: String stating the data type of the cache items
        :param project: Project object (optional)
        :param user: User object to denote user triggering the update (optional)
        :return: JSONCacheItem object
        :raise: ValueError if app_name is invalid
        :raise: ValueError if data_type is invalid
        """
        cls._check_app_name(app_name)
        cls._check_data_type(data_type)
        item = cls.get_cache_item(app_name, name, project)
        log_msg = f'Updated item "{app_name}:{name}"'
        if not item:
            if data_type == 'json':
                item = JSONCacheItem()
                item.name = name
                item.app_name = app_name
        item.data = data
        if project:
            item.project = project
            log_msg += f' in project {project.get_log_title()}'
        if user:
            item.user = user
            log_msg += f' by user "{user.username}"'
        item.save()
        logger.info(log_msg)
        return item

    @classmethod
    def delete_cache_item(
        cls, app_name: str, name: str, project: Optional[Project] = None
    ):
        """
        Method for deleting a cache item.

        :param app_name: Name of the app which sets the item (string)
        :param name: Item name (string)
        :param project: Project object (optional)
        """
        item = cls.get_cache_item(app_name, name, project)
        if item:
            item.delete()
            logger.info(f'Deleted item "{app_name}:{name}" from cache')

    @classmethod
    def get_update_time(
        cls, app_name: str, name: str, project: Optional[Project] = None
    ) -> float:
        """
        Return the time of the last update of a cache object as seconds since
        epoch.

        :param name: Item name (string)
        :param app_name: Name of the app which sets the item (string)
        :param project: Project object (optional)
        :return: Float
        """
        item = cls.get_cache_item(app_name, name, project)
        return item.date_modified.timestamp() if item else None
