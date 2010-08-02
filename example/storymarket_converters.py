from __future__ import absolute_import

from .models import ExampleStory
import django_storymarket.converters

def story_to_storymarket(api, obj):
    return {
        "type": "text",
        "title": obj.headline,
        "author": "jacobian",
        "org": api.orgs.get(12),
        "category": api.subcategories.get(12),
        "content": obj.body,
        "tags": ["testing"],
    }

django_storymarket.converters.register(ExampleStory, story_to_storymarket)