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
    
@attrs(short_description='Upload selected %(verbose_name_plural)s to Storymarket')
def upload_to_storymarket(modeladmin, request, queryset):
    """
    Admin action to upload selected objects to storymarket.
    """
    opts = modeladmin.model._meta
    post_data = request.POST if request.POST.get('post') else None
    
    # Generate a list of converted objects and forms for chosing options.
    forms = {}
    object_forms = []
    for obj in queryset:
        initial = converters.convert(obj)
        storymarket_type = initial.pop('type')
        form = StorymarketSyncForm(post_data, 
                                   prefix = 'sm-%s' % obj.pk,
                                   initial = initial,
                                   type = storymarket_type,)
        object_forms.append({'object': obj, 'form': form})
        forms[obj.pk] = form
    
    if request.POST.get('post') and all(f.is_valid() for f in forms.values()):
        # The user has confirmed the uploading and has selected valid info.
        num_uploaded = 0
        for obj in queryset:
            form = forms[obj.pk]
            _save_to_storymarket(obj, form.storymarket_type, form.cleaned_data)
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
        "objects": object_forms,
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
    api = storymarket.Storymarket(settings.STORYMARKET_API_KEY)
    manager = getattr(api, storymarket_type)
    sm_obj = manager.create(data)
    SyncedObject.objects.mark_synced(obj, sm_obj)
    
class AutosyncRuleInline(admin.TabularInline):
    model = AutoSyncRule
    extra = 1

class AutoSyncedModelAdmin(admin.ModelAdmin):
    inlines = [AutosyncRuleInline]
    
admin.site.register(AutoSyncedModel, AutoSyncedModelAdmin)
