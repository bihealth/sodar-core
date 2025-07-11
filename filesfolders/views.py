"""UI views for the filesfolders app"""

import logging

from typing import Optional, Union
from wsgiref.util import FileWrapper  # For db files
from zipfile import ZipFile

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import (
    TemplateView,
    UpdateView,
    CreateView,
    DeleteView,
    View,
)
from django.views.generic.edit import ModelFormMixin, DeletionMixin

from db_file_storage.storage import DatabaseFileStorage

# Projectroles dependency
from projectroles.models import Project, SODAR_CONSTANTS
from projectroles.plugins import PluginAPI
from projectroles.app_settings import AppSettingAPI
from projectroles.utils import build_secret, get_display_name
from projectroles.views import (
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    HTTPRefererMixin,
    ProjectPermissionMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    PROJECT_BLOCK_MSG,
)

from filesfolders.forms import FolderForm, FileForm, HyperLinkForm
from filesfolders.models import Folder, File, FileData, HyperLink
from filesfolders.utils import build_public_url


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
plugin_api = PluginAPI()
storage = DatabaseFileStorage()


# Local constants
APP_NAME = 'filesfolders'
APP_NAME_PR = 'projectroles'
TL_OBJ_TYPES = {'Folder': 'folder', 'File': 'file', 'HyperLink': 'hyperlink'}
DEFAULT_UPDATE_ATTRS = ['name', 'folder', 'description', 'flag']
LINK_BAD_REQUEST_MSG = settings.FILESFOLDERS_LINK_BAD_REQUEST_MSG
SERVE_AS_ATTACHMENT = settings.FILESFOLDERS_SERVE_AS_ATTACHMENT


# Mixins -----------------------------------------------------------------


class ObjectPermissionMixin(LoggedInPermissionMixin):
    """Mixin to ensure owner permission for different filesfolders objects"""

    def has_permission(self):
        """Override has_permission to check perms depending on owner"""
        try:
            obj = type(self.get_object()).objects.get(
                sodar_uuid=self.kwargs['item']
            )
        except type(self.get_object()).DoesNotExist:
            return False
        # Fail if project is blocked
        if not self.request.user.is_superuser and app_settings.get(
            APP_NAME_PR, 'project_access_block', project=obj.project
        ):
            messages.error(
                self.request,
                PROJECT_BLOCK_MSG.format(
                    project_type=get_display_name(obj.project.type)
                )
                + '.',
            )
            return False
        if obj.owner == self.request.user:
            return self.request.user.has_perm(
                'filesfolders.update_data_own', self.get_permission_object()
            )
        return self.request.user.has_perm(
            'filesfolders.update_data_all', self.get_permission_object()
        )

    def get_permission_object(self):
        """Override get_permission_object for checking Project permission"""
        if self.get_object():
            return self.get_object().project
        return None


class FilesfoldersTimelineMixin:
    """Mixin for filesfolders specific timeline helpers"""

    @classmethod
    def add_item_modify_event(
        cls,
        obj: Union[File, Folder, HyperLink],
        request: HttpRequest,
        view_action: str,
        update_attrs: list = DEFAULT_UPDATE_ATTRS,
        old_data: Optional[dict] = None,
    ):
        """
        Add filesfolders item create/update event to timeline.

        :param obj: Filesfolders object being created or updated
        :param request: Request object
        :param view_action: "create" or "update" (string)
        :param update_attrs: List of attribute names to include in extra_data
        :param old_data: Data from existing object in case of update (dict)
        """
        timeline = plugin_api.get_backend_api('timeline_backend')
        if not timeline:
            return

        obj_type = TL_OBJ_TYPES[obj.__class__.__name__]
        extra_data = {}
        tl_desc = f'{view_action} {obj_type} {{{obj_type}}}'

        if view_action == 'create':
            for a in update_attrs:
                extra_data[a] = str(getattr(obj, a))

        elif old_data:  # Update
            for a in update_attrs:
                if old_data[a] != getattr(obj, a):
                    extra_data[a] = str(getattr(obj, a))
            tl_desc += ' (' + ', '.join(a for a in extra_data) + ')'

        tl_event = timeline.add_event(
            project=obj.project,
            app_name=APP_NAME,
            user=request.user,
            event_name=f'{obj_type}_{view_action}',
            description=tl_desc,
            extra_data=extra_data,
            status_type=timeline.TL_STATUS_OK,
        )
        tl_event.add_object(
            obj=obj,
            label=obj_type,
            name=obj.get_path() if isinstance(obj, Folder) else obj.name,
        )


class ViewActionMixin(object):
    """Mixin for retrieving form action type"""

    @property
    def view_action(self):
        raise ImproperlyConfigured('Property "view_action" missing!')

    def get_view_action(self) -> Optional[str]:
        return self.view_action if self.view_action else None


class FormValidMixin(ModelFormMixin, FilesfoldersTimelineMixin):
    """Mixin for overriding form_valid in form views for creation/updating"""

    def form_valid(self, form):
        view_action = self.get_view_action()
        old_data = {}
        update_attrs = ['name', 'folder', 'description', 'flag']
        if view_action == 'update':
            old_item = self.get_object()
            if old_item.__class__.__name__ == 'HyperLink':
                update_attrs.append('url')
            elif old_item.__class__.__name__ == 'File':
                update_attrs.append('public_url')
            # Get old fields
            for a in update_attrs:
                old_data[a] = getattr(old_item, a)
        self.object = form.save()

        # Add event in Timeline
        self.add_item_modify_event(
            obj=self.object,
            request=self.request,
            view_action=view_action,
            update_attrs=update_attrs,
            old_data=old_data,
        )
        messages.success(
            self.request,
            f'{self.object.__class__.__name__} "{self.object.name}" '
            f'successfully {view_action}d.',
        )
        # TODO: Repetition, put this in a mixin?
        if self.object.folder:
            re_kwargs = {'folder': self.object.folder.sodar_uuid}
        else:
            re_kwargs = {'project': self.object.project.sodar_uuid}
        return redirect(reverse('filesfolders:list', kwargs=re_kwargs))


class DeleteSuccessMixin(DeletionMixin):
    """Mixin for overriding get_success_url in deletion form views"""

    def get_success_url(self):
        timeline = plugin_api.get_backend_api('timeline_backend')
        # Add event in Timeline
        if timeline:
            obj_type = TL_OBJ_TYPES[self.object.__class__.__name__]
            # Add event in Timeline
            tl_event = timeline.add_event(
                project=self.object.project,
                app_name=APP_NAME,
                user=self.request.user,
                event_name=f'{obj_type}_delete',
                description=f'delete {obj_type} {{{obj_type}}}',
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=self.object,
                label=obj_type,
                name=(
                    self.object.get_path()
                    if isinstance(self.object, Folder)
                    else self.object.name
                ),
            )

        messages.success(
            self.request,
            f'{self.object.__class__.__name__} "{self.object.name}" deleted.',
        )
        # TODO: Repetition, put this in a mixin?
        if self.object.folder:
            re_kwargs = {'folder': self.object.folder.sodar_uuid}
        else:
            re_kwargs = {'project': self.object.project.sodar_uuid}
        return reverse('filesfolders:list', kwargs=re_kwargs)


class FileServeMixin:
    """Mixin for file download serving"""

    def get(self, *args, **kwargs):
        """GET request to return the file as attachment"""
        timeline = plugin_api.get_backend_api('timeline_backend')
        if kwargs.get('project'):
            redirect_url = reverse(
                'filesfolders:list', kwargs={'project': kwargs['project']}
            )
        else:
            redirect_url = reverse('home')

        # Get File object
        try:
            file = File.objects.get(sodar_uuid=kwargs['file'])
        except File.DoesNotExist:
            messages.error(self.request, 'File object not found.')
            return redirect(redirect_url)
        # Get corresponding FileData object with file content
        try:
            file_data = FileData.objects.get(file_name=file.file.name)
        except FileData.DoesNotExist:
            messages.error(self.request, 'File data not found.')
            return redirect(redirect_url)
        # Open file for serving
        try:
            file_content = storage.open(file_data.file_name)
        except Exception:
            messages.error(self.request, 'Error opening file.')
            return redirect(redirect_url)

        # Return file as attachment
        response = HttpResponse(
            FileWrapper(file_content), content_type=file_data.content_type
        )
        if SERVE_AS_ATTACHMENT:
            response['Content-Disposition'] = (
                f'attachment; filename={file.name}'
            )
        if self.request.user.is_authenticated:
            # Add event in Timeline
            if timeline:
                tl_event = timeline.add_event(
                    project=file.project,
                    app_name=APP_NAME,
                    user=self.request.user,
                    event_name='file_serve',
                    description='serve file {file}',
                    classified=True,
                    status_type=timeline.TL_STATUS_INFO,
                )
                tl_event.add_object(file, 'file', file.name)
        return response


# Base Views -------------------------------------------------------------


class BaseCreateView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    FormValidMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
    CurrentUserFormMixin,
    InvalidFormMixin,
    CreateView,
):
    """Base File/Folder/HyperLink creation view"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if 'folder' in self.kwargs:
            context['folder'] = Folder.objects.filter(
                sodar_uuid=self.kwargs['folder']
            ).first()
        return context

    def get_form_kwargs(self):
        """Pass current user and URL kwargs to form"""
        kwargs = super().get_form_kwargs()
        if 'folder' in self.kwargs:
            kwargs.update({'folder': self.kwargs['folder']})
        elif 'project' in self.kwargs:
            kwargs.update({'project': self.kwargs['project']})
        return kwargs


# File List View ---------------------------------------------------------


class ProjectFileView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectPermissionMixin,
    ProjectContextMixin,
    TemplateView,
):
    """View for displaying files and folders for a project"""

    # Projectroles dependency
    permission_required = 'filesfolders.view_data'
    template_name = 'filesfolders/project_files.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project = self.get_project(self.request, self.kwargs)
        context['project'] = project
        # Get folder and file data
        root_folder = None

        if 'folder' in self.kwargs:
            root_folder = Folder.objects.filter(
                sodar_uuid=self.kwargs['folder']
            ).first()
            if root_folder:
                context['folder'] = root_folder
                # Build breadcrumb
                f = root_folder
                breadcrumb = [f]
                while f.folder:
                    breadcrumb.insert(0, f.folder)
                    f = f.folder
                context['folder_breadcrumb'] = breadcrumb
        context['folders'] = Folder.objects.filter(
            project=project, folder=root_folder
        )
        context['files'] = File.objects.filter(
            project=project, folder=root_folder
        )
        context['links'] = HyperLink.objects.filter(
            project=project, folder=root_folder
        )
        context['allow_public_links'] = app_settings.get(
            APP_NAME, 'allow_public_links', project=project
        )

        # Get folder ReadMe
        folder_pk = (
            Folder.objects.get(sodar_uuid=self.kwargs['folder']).pk
            if 'folder' in self.kwargs
            else None
        )
        readme_md = File.objects.get_folder_readme(
            project_pk=project.pk, folder_pk=folder_pk, mimetype='text/markdown'
        )
        # If the markdown version is not found, try to get a plaintext version
        readme_txt = File.objects.get_folder_readme(
            project_pk=project.pk, folder_pk=folder_pk, mimetype='text/plain'
        )
        readme_file = readme_md if readme_md else readme_txt
        if readme_file:
            try:
                context['readme_name'] = readme_file.name
                context['readme_mime'] = readme_file.file.file.mimetype
                if context['readme_mime'] == 'text/markdown':
                    context['readme_data'] = readme_file.file.read().decode(
                        'utf-8'
                    )
                    if readme_txt:
                        context['readme_alt'] = readme_txt.name
                else:
                    context['readme_data'] = readme_file.file.read()
            except Exception as ex:
                if settings.DEBUG:
                    raise ex
                logger.error(
                    f'Exception in accessing readme file data '
                    f'(UUID={readme_file.sodar_uuid}): {ex}'
                )
        return context


# Folder Views -----------------------------------------------------------


class FolderCreateView(ViewActionMixin, BaseCreateView):
    """Folder creation view"""

    permission_required = 'filesfolders.add_data'
    model = Folder
    form_class = FolderForm
    view_action = 'create'


class FolderUpdateView(
    LoginRequiredMixin,
    ObjectPermissionMixin,
    FormValidMixin,
    ViewActionMixin,
    ProjectContextMixin,
    InvalidFormMixin,
    UpdateView,
):
    """Folder updating view"""

    model = Folder
    form_class = FolderForm
    view_action = 'update'
    slug_url_kwarg = 'item'
    slug_field = 'sodar_uuid'


class FolderDeleteView(
    LoginRequiredMixin,
    ObjectPermissionMixin,
    DeleteSuccessMixin,
    ProjectContextMixin,
    DeleteView,
):
    """Folder deletion view"""

    model = Folder
    slug_url_kwarg = 'item'
    slug_field = 'sodar_uuid'


# File Views -------------------------------------------------------------


class FileCreateView(ViewActionMixin, BaseCreateView):
    """File creation view"""

    permission_required = 'filesfolders.add_data'
    model = File
    form_class = FileForm
    view_action = 'create'

    def form_valid(self, form):
        """Override form_valid() for zip file unpacking"""
        timeline = plugin_api.get_backend_api('timeline_backend')

        # Regular file upload
        if not form.cleaned_data.get('unpack_archive'):
            return super().form_valid(form)

        # Zip file unpacking
        file = form.cleaned_data.get('file')
        folder = form.cleaned_data.get('folder')
        project = self.get_project(self.request, self.kwargs)

        # Build redirect URL
        # TODO: Repetition, put this in a mixin?
        if folder:
            re_kwargs = {'folder': folder.sodar_uuid}
        else:
            re_kwargs = {'project': project.sodar_uuid}
        redirect_url = reverse('filesfolders:list', kwargs=re_kwargs)

        try:
            zip_file = ZipFile(file)
        except Exception as ex:
            messages.error(self.request, f'Unable to extract zip file: {ex}')
            return redirect(redirect_url)

        new_folders = []
        new_files = []

        with transaction.atomic():
            for f in [f for f in zip_file.infolist() if not f.is_dir()]:
                # Create subfolders if any
                current_folder = folder
                for zip_folder in f.filename.split('/')[:-1]:
                    try:
                        current_folder = Folder.objects.get(
                            name=zip_folder,
                            project=project,
                            folder=current_folder,
                        )
                    except Folder.DoesNotExist:
                        current_folder = Folder.objects.create(
                            name=zip_folder,
                            project=project,
                            folder=current_folder,
                            owner=self.request.user,
                        )
                        new_folders.append(current_folder)

                # Save file
                file_name_nopath = f.filename.split('/')[-1]
                unpacked_file = File(
                    name=file_name_nopath,
                    project=project,
                    folder=current_folder,
                    owner=self.request.user,
                    secret=build_secret(),
                )
                content_file = ContentFile(zip_file.read(f.filename))
                unpacked_file.file.save(file_name_nopath, content_file)
                unpacked_file.save()
                new_files.append(unpacked_file)

        # Add timeline events
        for new_folder in new_folders:
            self.add_item_modify_event(
                obj=new_folder, request=self.request, view_action='create'
            )
        for new_file in new_files:
            self.add_item_modify_event(
                obj=new_file, request=self.request, view_action='create'
            )
        if timeline:
            timeline.add_event(
                project=project,
                app_name=APP_NAME,
                user=self.request.user,
                event_name='archive_extract',
                description=f'Extract from archive "{file.name}", create '
                f'{len(new_folders)} folders and {len(new_files)} files',
                extra_data={
                    'new_folders': [f.name for f in new_folders],
                    'new_files': [f.name for f in new_files],
                },
                status_type=timeline.TL_STATUS_OK,
            )

        messages.success(
            self.request,
            'Extracted {} files in folder "{}" from archive "{}".'.format(
                len([f for f in zip_file.infolist() if not f.is_dir()]),
                folder.name if folder else 'root',
                file.name,
            ),
        )
        return redirect(redirect_url)


class FileUpdateView(
    LoginRequiredMixin,
    ObjectPermissionMixin,
    FormValidMixin,
    ViewActionMixin,
    ProjectContextMixin,
    InvalidFormMixin,
    UpdateView,
):
    """File updating view"""

    model = File
    form_class = FileForm
    view_action = 'update'
    slug_url_kwarg = 'item'
    slug_field = 'sodar_uuid'


class FileDeleteView(
    LoginRequiredMixin,
    ObjectPermissionMixin,
    DeleteSuccessMixin,
    ProjectContextMixin,
    DeleteView,
):
    """File deletion view"""

    model = File
    slug_url_kwarg = 'item'
    slug_field = 'sodar_uuid'


class FileServeView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    FileServeMixin,
    ProjectPermissionMixin,
    View,
):
    """View for serving file to a logged in user with permissions"""

    permission_required = 'filesfolders.view_data'


class FileServePublicView(FileServeMixin, View):
    """View for serving file to a public user with secure link"""

    def get(self, request, *args, **kwargs):
        """Override of GET for checking request URL"""
        try:
            file = File.objects.get(secret=kwargs['secret'])
            # Check if sharing public files is not allowed in project settings
            if not app_settings.get(
                APP_NAME, 'allow_public_links', file.project
            ):
                return HttpResponseBadRequest(LINK_BAD_REQUEST_MSG)
        except File.DoesNotExist:
            return HttpResponseBadRequest(LINK_BAD_REQUEST_MSG)

        # If public URL serving is disabled, don't serve file
        if not file.public_url:
            return HttpResponseBadRequest(LINK_BAD_REQUEST_MSG)
        # If related project is locked, refuse to serve
        if not request.user.is_superuser and app_settings.get(
            APP_NAME_PR, 'project_access_block', project=file.project
        ):
            return HttpResponseForbidden(
                PROJECT_BLOCK_MSG.format(
                    project_type=get_display_name(file.project.type)
                )
            )
        # Update kwargs with file and project uuid:s
        kwargs.update(
            {'file': file.sodar_uuid, 'project': file.project.sodar_uuid}
        )
        # If successful, return get() from FileServeMixin
        return super().get(*args, **kwargs)


class FilePublicLinkView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    ProjectContextMixin,
    ProjectPermissionMixin,
    TemplateView,
):
    """View for generating a public secure link to a file"""

    permission_required = 'filesfolders.share_public_link'
    template_name = 'filesfolders/public_link.html'

    def get(self, *args, **kwargs):
        """Override of GET for checking project settings"""
        try:
            file = File.objects.get(sodar_uuid=self.kwargs['file'])
        except File.DoesNotExist:
            messages.error(self.request, 'File not found.')
            return redirect(reverse('home'))
        if not app_settings.get(APP_NAME, 'allow_public_links', file.project):
            messages.error(
                self.request,
                'Sharing public links not allowed for this {}.'.format(
                    get_display_name(SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'])
                ),
            )
            return redirect(
                reverse(
                    'filesfolders:list',
                    kwargs={'project': file.project.sodar_uuid},
                )
            )
        return super().get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Provide URL to context"""
        context = super().get_context_data(*args, **kwargs)
        try:
            file = File.objects.get(sodar_uuid=self.kwargs['file'])
        except File.DoesNotExist:
            messages.error(self.request, 'File not found.')
            return redirect(reverse('home'))
        if not file.public_url:
            messages.error(self.request, 'Public URL for file not enabled.')
            return redirect(
                reverse(
                    'filesfolders:list',
                    kwargs={'project': file.project.sodar_uuid},
                )
            )
        context['file'] = file
        context['public_url'] = build_public_url(file, self.request)
        return context


# HyperLink Views --------------------------------------------------------


class HyperLinkCreateView(ViewActionMixin, BaseCreateView):
    """HyperLink creation view"""

    permission_required = 'filesfolders.add_data'
    model = HyperLink
    form_class = HyperLinkForm
    view_action = 'create'


class HyperLinkUpdateView(
    LoginRequiredMixin,
    ObjectPermissionMixin,
    FormValidMixin,
    ViewActionMixin,
    ProjectContextMixin,
    InvalidFormMixin,
    UpdateView,
):
    """HyperLink updating view"""

    model = HyperLink
    form_class = HyperLinkForm
    view_action = 'update'
    slug_url_kwarg = 'item'
    slug_field = 'sodar_uuid'


class HyperLinkDeleteView(
    LoginRequiredMixin,
    ObjectPermissionMixin,
    DeleteSuccessMixin,
    ProjectContextMixin,
    DeleteView,
):
    """HyperLink deletion view"""

    model = HyperLink
    slug_url_kwarg = 'item'
    slug_field = 'sodar_uuid'


# Batch Edit Views --------------------------------------------------------


class BatchEditView(
    LoginRequiredMixin,
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    ProjectPermissionMixin,
    TemplateView,
):
    """Batch delete/move confirm view"""

    http_method_names = ['post']
    template_name = 'filesfolders/batch_edit_confirm.html'
    # NOTE: minimum perm, all checked files will be tested in post()
    permission_required = 'filesfolders.update_data_own'

    #: Items we will delete
    items = None

    #: Item IDs to be deleted (so we don't have to create them again)
    item_names = None

    #: Items which we can't delete
    failed = None

    #: Current action of view
    batch_action = None

    #: Project object
    project = None

    def _render_confirmation(self, **kwargs) -> HttpResponse:
        """Render user confirmation"""
        context = {
            'batch_action': self.batch_action,
            'items': self.items,
            'item_names': self.item_names,
            'failed': self.failed,
            'project': self.project,
            'folder_check': True,
        }
        if 'folder' in kwargs:
            context['folder'] = kwargs['folder']

        # NOTE: No modifications needed for "delete" action
        if self.batch_action == 'move':
            # Exclude folders to be moved
            exclude_list = [
                x.sodar_uuid for x in self.items if isinstance(x, Folder)
            ]
            # Exclude folders under folders to be moved
            for i in self.items:
                exclude_list += [
                    x.sodar_uuid
                    for x in Folder.objects.filter(
                        project__sodar_uuid=self.project.sodar_uuid
                    )
                    if x.has_in_path(i)
                ]
            # Exclude current folder
            if 'folder' in kwargs:
                exclude_list.append(kwargs['folder'])
            folder_choices = Folder.objects.filter(
                project=self.project
            ).exclude(sodar_uuid__in=exclude_list)
            context['folder_choices'] = folder_choices
            if folder_choices.count() == 0:
                context['folder_check'] = False
        return super().render_to_response(context)

    def _finalize_edit(
        self, edit_count: int, target_folder: Optional[Folder], **kwargs
    ) -> HttpResponseRedirect:
        """Finalize executed batch operation"""
        timeline = plugin_api.get_backend_api('timeline_backend')
        edit_suffix = 's' if edit_count != 1 else ''
        fail_suffix = 's' if len(self.failed) != 1 else ''

        if len(self.failed) > 0:
            messages.warning(
                self.request,
                'Unable to edit {} item{}, check '
                'permissions and target folder. Failed: {}'.format(
                    len(self.failed),
                    fail_suffix,
                    ', '.join(f.name for f in self.failed),
                ),
            )
        if edit_count > 0:
            messages.success(
                self.request,
                'Batch {} {} item{}.'.format(
                    'deleted' if self.batch_action == 'delete' else 'moved',
                    edit_count,
                    edit_suffix,
                ),
            )

        # Add event in Timeline
        if timeline:
            extra_data = {
                'items': [x.name for x in self.items],
                'failed': [x.name for x in self.failed],
            }
            tl_event = timeline.add_event(
                project=Project.objects.filter(
                    sodar_uuid=self.project.sodar_uuid
                ).first(),
                app_name=APP_NAME,
                user=self.request.user,
                event_name=f'batch_{self.batch_action}',
                description='batch {} {} item{} {} {}'.format(
                    self.batch_action,
                    edit_count,
                    edit_suffix,
                    (
                        '({} failed)'.format(len(self.failed))
                        if len(self.failed) > 0
                        else ''
                    ),
                    (
                        'to {target_folder}'
                        if self.batch_action == 'move' and target_folder
                        else ''
                    ),
                ),
                extra_data=extra_data,
                status_type=(
                    timeline.TL_STATUS_OK
                    if edit_count > 0
                    else timeline.TL_STATUS_FAILED
                ),
            )
            if self.batch_action == 'move' and target_folder:
                tl_event.add_object(
                    target_folder, 'target_folder', target_folder.get_path()
                )

        if 'folder' in kwargs:
            re_kwargs = {'folder': kwargs['folder']}
        else:
            re_kwargs = {'project': kwargs['project']}
        return redirect(reverse('filesfolders:list', kwargs=re_kwargs))

    def post(self, request, **kwargs):
        """Handle POST request for modifying items or user confirmation"""
        post_data = request.POST
        self.project = self.get_project(request, kwargs)
        self.batch_action = post_data['batch-action']
        self.items = []
        self.item_names = []
        self.failed = []
        can_update_all = request.user.has_perm(
            'filesfolders.update_data_all', self.get_permission_object()
        )
        user_confirmed = bool(int(post_data['user-confirmed']))
        edit_count = 0
        target_folder = None

        if (
            self.batch_action == 'move'
            and 'target-folder' in post_data
            and post_data['target-folder'] != '0'
        ):
            target_folder = Folder.objects.filter(
                sodar_uuid=post_data['target-folder']
            ).first()

        for key in [
            key
            for key, val in post_data.items()
            if key.startswith('batch_item') and val == '1'
        ]:
            cls = eval(key.split('_')[2])
            item = cls.objects.filter(sodar_uuid=key.split('_')[3]).first()
            #: Item permission
            perm_ok = can_update_all | (item.owner == request.user)

            # Checks
            # Perm check
            if not perm_ok:
                self.failed.append(item)
            # Moving checks (after user has selected target folder)
            elif self.batch_action == 'move' and user_confirmed:
                # Can't move if item with same name in target
                get_kwargs = {
                    'project': self.project,
                    'folder': target_folder if target_folder else None,
                    'name': item.name,
                }
                if cls.objects.filter(**get_kwargs):
                    self.failed.append(item)
            # Deletion checks
            elif self.batch_action == 'delete':
                # Can't delete a non-empty folder
                if isinstance(item, Folder) and not item.is_empty():
                    self.failed.append(item)

            # Modify item
            if perm_ok and item not in self.failed:
                if not user_confirmed:
                    self.items.append(item)
                    self.item_names.append(key)
                elif self.batch_action == 'move':
                    item.folder = target_folder
                    item.save()
                    edit_count += 1
                elif self.batch_action == 'delete':
                    item.delete()
                    edit_count += 1

        # Render/redirect
        # Confirmation needed
        if not user_confirmed:
            return self._render_confirmation(**kwargs)
        # User confirmed, batch operation done
        else:
            return self._finalize_edit(edit_count, target_folder, **kwargs)
