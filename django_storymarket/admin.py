from __future__ import absolute_import

import storymarket

from django import template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.util import model_ngettext
from django.contrib.contenttypes import generic
from django.shortcuts import render_to_response, redirect
from django.utils.translation import ugettext as _

from . import converters
from .forms import StorymarketSyncForm, StorymarketOptionalSyncForm
from .models import SyncedObject, AutoSyncedModel, AutoSyncRule

# TODO: reorganize this module into public/private stuff

def attrs(**kwargs):
    """
    Helper decorator to function attributes to a function.
    """
    def _decorator(func):
        for k, v in kwargs.items():
            setattr(func, k, v)
        return func
    return _decorator
    
@attrs(short_description='Upload selected %(verbose_name_plural)s to Storymarket')
def upload_to_storymarket(modeladmin, request, queryset):
    """
    Admin action to upload selected objects to storymarket.
    """
    opts = modeladmin.model._meta
    post_data = request.POST if request.POST.get('post') else None
    
    # Gather forms, converted data, and other options for later.
    object_info = {}
    for obj in queryset:
        converted_data = converters.convert(obj)
        storymarket_type = converted_data.pop('type')
        form = StorymarketSyncForm(post_data, prefix='sm-%s' % obj.pk, initial=converted_data.copy())
        object_info[obj.pk] = {
            'object': obj,
            'form': form,
            'storymarket_type': storymarket_type,
            'converted_data': converted_data}
    
    if request.POST.get('post') and all(i['form'].is_valid() for i in object_info.values()):
        # The user has confirmed the uploading and has selected valid info.
        num_uploaded = 0
        for obj in queryset:
            info = object_info[obj.pk]
            data = info['converted_data']
            data.update(info['form'].cleaned_data)
            _save_to_storymarket(obj, info['storymarket_type'], data)
            num_uploaded += 1
            
        modeladmin.message_user(request, 
            _("Successfully uploaded %(count)d %(items)s to Storymarket.") % {
                "count": num_uploaded, "items": model_ngettext(modeladmin.opts, num_uploaded)
        })
        return redirect('.')
    
    context = template.RequestContext(request, {
        "app_label": opts.app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        "opts": opts,
        "root_path": modeladmin.admin_site.root_path,
        "objects": object_info,
    })
    
    template_names = [
        "storymarket/confirm_%s_%s_upload.html" % (opts.app_label, opts.object_name.lower()),
        "storymarket/confirm_upload.html"
    ]
    if hasattr(modeladmin, "storymarket_upload_confirmation_template"):
        template_names.insert(0, modeladmin.storymarket_upload_confirmation_template)
        
    return render_to_response(template_names, context_instance=context)
        
@attrs(short_description='Synced?', boolean=True)
def is_synced_to_storymarket(obj):
    """
    Admin field callback to display storymarket sync status.
    """
    return SyncedObject.objects.for_model(obj).exists()
    
def _save_to_storymarket(obj, storymarket_type, data):
    """
    Helper: push an object o Storymarket.
    
    Called from the various parts of the admin that need to upload
    objects -- ``save_model``, the ``upload_to_storymarket`` action,
    etc.
    """
    # TODO: should figure out how to do an update if the object already exists.
    api = storymarket.Storymarket(settings.STORYMARKET_API_KEY)
    manager = getattr(api, storymarket_type)
    blob = data.pop('blob', None)
    sm_obj = manager.create(data)

    # TODO: Is this the right spot to be handling binary data?
    if blob:
        sm_obj.upload_blob(blob)

    return SyncedObject.objects.mark_synced(obj, sm_obj)

# TODO: figure out how (if at all) to get converted data into form.intial

class StorymarketUploaderInlineFormset(generic.BaseGenericInlineFormSet):
    def save(self):
        # TODO: only do an update if the object already exists on SM
        
        self.changed_objects = []
        self.deleted_objects = []
        self.new_objects = []

        assert len(self.forms) == 1
        
        form = self.forms[0]
        if form.cleaned_data.pop('sync', False):
            sm_data = converters.convert(self.instance)
            sm_type = sm_data.pop('type')
            sm_data.update(form.cleaned_data)
            so, created = _save_to_storymarket(self.instance, sm_type, sm_data)
            if created:
                self.new_objects.append(so)
            else:
                self.changed_objects.append(so)
            
        return self.new_objects + self.changed_objects

class StorymarketUploaderInline(generic.GenericStackedInline):
    model = SyncedObject
    ct_field = "content_type"
    ct_fk_field = "object_pk"
    max_num = 1
    can_delete = False
    form = StorymarketOptionalSyncForm
    formset = StorymarketUploaderInlineFormset
    fields = ['sync', 'org', 'category', 'tags']
    template = 'storymarket/uploader_inline.html'

class AutosyncRuleInline(admin.TabularInline):
    model = AutoSyncRule
    extra = 1

class AutoSyncedModelAdmin(admin.ModelAdmin):
    inlines = [AutosyncRuleInline]
    
admin.site.register(AutoSyncedModel, AutoSyncedModelAdmin)
