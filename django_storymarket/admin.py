from __future__ import absolute_import

import storymarket

from django import template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.util import model_ngettext
from django.shortcuts import render_to_response, redirect
from django.utils.translation import ugettext as _

from . import converters
from .forms import StorymarketSyncForm
from .models import SyncedObject, AutoSyncedModel, AutoSyncRule

def attrs(**kwargs):
    """
    Helper decorator to function attributes to a function.
    """
    def _decorator(func):
        for k, v in kwargs.items():
            setattr(func, k, v)
        return func
    return _decorator

class AutosyncRuleInline(admin.TabularInline):
    model = AutoSyncRule
    extra = 1

class AutoSyncedModelAdmin(admin.ModelAdmin):
    inlines = [AutosyncRuleInline]
    
admin.site.register(AutoSyncedModel, AutoSyncedModelAdmin)
    
@attrs(short_description='Upload selected %(verbose_name_plural)s to Storymarket')
def upload_to_storymarket(modeladmin, request, queryset):
    """
    Admin action to upload selected objects to storymarket.
    """
    opts = modeladmin.model._meta
            
    if request.POST.get('post'):
        # The user has confirumed the uploading.
        num_uploaded = 0
        for obj in queryset:
            _save_to_storymarket(obj)
            num_uploaded += 1
            
        modeladmin.message_user(request, 
            _("Successfully uploaded %(count)d %(items)s to Storymarket.") % {
                "count": num_uploaded, "items": model_ngettext(modeladmin.opts, num_uploaded)
        })
        return redirect('.')
    
    # Generate a list of converted objects to "preview" as an upload.
    # These is a list-of-dicts for template convienience
    previewed_objects = [
        {'object': obj, 'preview': converters.convert(obj)}
        for obj in queryset
    ]
    
    context = template.RequestContext(request, {
        "app_label": opts.app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        "opts": opts,
        "root_path": modeladmin.admin_site.root_path,
        "objects": previewed_objects,
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
    
def _save_to_storymarket(obj):
    """
    Helper: push an object o Storymarket.
    
    Called from the various parts of the admin that need to upload
    objects -- ``save_model``, the ``upload_to_storymarket`` action,
    etc.
    """
    api = storymarket.Storymarket(settings.STORYMARKET_API_KEY)
    sm_data = converters.convert(obj)
    sm_type = sm_data.pop('type')
    manager = getattr(api, sm_type)
    sm_obj = manager.create(sm_data)
    SyncedObject.objects.mark_synced(obj, sm_obj)