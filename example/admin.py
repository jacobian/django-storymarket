from __future__ import absolute_import

from django.contrib import admin
from django_storymarket.admin import upload_to_storymarket, is_synced_to_storymarket
from .models import ExampleStory

class ExampleStoryAdmin(admin.ModelAdmin):
    actions = [upload_to_storymarket]
    list_display = ['headline', is_synced_to_storymarket]

admin.site.register(ExampleStory, ExampleStoryAdmin)
