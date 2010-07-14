from __future__ import absolute_import

from django import template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.util import model_ngettext
from django.shortcuts import render_to_response, redirect
from django.utils.translation import ugettext_lazy, ugettext as _

import storymarket

from . import converters
from .models import SyncedObject

def attrs(**kwargs):
    """
    Helper decorator to function attributes to a function.
    """
    def _decorator(func):
        for k, v in kwargs.items():
            setattr(func, k, v)
        return func
    return _decorator

class StorymarketAdmin(admin.ModelAdmin):
    """
    Abstract ModelAdmin base class for content that can be manually synced to
    Storymarket.
    """
    actions = ['upload_to_storymarket']

    def __init__(self, model, admin_site):
        super(StorymarketAdmin, self).__init__(model, admin_site)
        
        list_display = list(getattr(self, 'list_display', []))
        list_display.append('is_synced_to_storymarket')
        self.list_display = list_display
        
        self.storymarket = storymarket.Storymarket(settings.STORYMARKET_API_KEY)
        
        # FIXME: this should be elsewhere.
        converters.autodiscover()
    
    @attrs(short_description='Upload selected %(verbose_name_plural)s to Storymarket')
    def upload_to_storymarket(self, request, queryset):
        opts = self.model._meta
                
        if request.POST.get('post'):
            # The user has confirumed the uploading.
            num_uploaded = 0
            for obj in queryset:
                sm_data = converters.convert(self.storymarket, obj)
                sm_type = sm_data.pop('type')
                manager = getattr(self.storymarket, sm_type)
                sm_obj = manager.create(sm_data)
                SyncedObject.objects.mark_synced(obj, sm_obj)
                num_uploaded += 1
                
            self.message_user(request, _("Successfully uploaded %(count)d %(items)s to Storymarket.") % {
                "count": n, "items": model_ngettext(modeladmin.opts, n)
            })
            return redirect('.')
        
        # Generate a list of converted objects to "preview" as an upload.
        # These is a list-of-dicts for template convienience
        previewed_objects = [
            {'object': obj, 'preview': converters.convert(self.storymarket, obj)}
            for obj in queryset
        ]
        
        context = template.RequestContext(request, {
            "app_label": opts.app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            "opts": opts,
            "root_path": self.admin_site.root_path,
            "objects": previewed_objects,
        })
        
        template_names = [
            "storymarket/confirm_%s_%s_upload.html" % (opts.app_label, opts.object_name.lower()),
            "storymarket/confirm_upload.html"
        ]
        if hasattr(self, "storymarket_upload_confirmation_template"):
            template_names.insert(0, self.storymarket_upload_confirmation_template)
            
        return render_to_response(template_names, context_instance=context)
        
    @attrs(short_description='Synced', boolean=True)
    def is_synced_to_storymarket(self, obj):
        return SyncedObject.objects.for_model(obj).exists()