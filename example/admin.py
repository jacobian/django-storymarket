from __future__ import absolute_import

from django.contrib import admin
from django_storymarket.admin import StorymarketAdmin
from .models import ExampleStory

class ExampleStoryAdmin(StorymarketAdmin, admin.ModelAdmin):
    def to_storymarket(self, obj):
        return {
            "type": "text",
            "title": obj.headline,
            "author": "jacobian",
            "org": self.storymarket.orgs.get(12),
            "category": self.storymarket.subcategories.get(12),
            "content": obj.body
        }

admin.site.register(ExampleStory, ExampleStoryAdmin)
