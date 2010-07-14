from __future__ import absolute_import

from django.contrib import admin
from django_storymarket.admin import StorymarketAdmin
from .models import ExampleStory

class ExampleStoryAdmin(StorymarketAdmin, admin.ModelAdmin):
    pass

admin.site.register(ExampleStory, ExampleStoryAdmin)
