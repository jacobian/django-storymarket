import operator
import storymarket
from django import forms
from django.core.cache import cache
from django.conf import settings
from .models import SyncedObject

# Timeout for choices cached from Storymarket. 5 minutes.
CHOICE_CACHE_TIMEOUT = 600

class StorymarketAPIChoiceField(forms.ChoiceField):
    """
    Helper base class for ChoiceFields that offer choices by calling a
    Storymarket API.
    
    For speed, the list of allowable items are stored in the cache.
    """
    
    def __init__(self, *args, **kwargs):
        # Skip ChoiceField's initializer since we're handling choices
        # via the property below.
        super(forms.ChoiceField, self).__init__(*args, **kwargs)
    
    @property
    def choices(self):
        # Return a list of choices sorted by name, along with an empty choice.
        cache_key = 'storymarket_choice_cache:%s' % self.__class__.__name__
        choices = cache.get(cache_key)
        if choices is None:
            objs = sorted(self._call_api(), key=operator.attrgetter('name'))
            
            # If there's only a single object, just select it -- don't offer
            # an empty choice. Otherwise, offer an empty.
            if len(objs) == 1:
                empty_choice = []
            else:
                empty_choice = [(u'', u'---------')]
            choices = empty_choice + [(o.id, o.name) for o in objs]
            cache.set(cache_key, choices, CHOICE_CACHE_TIMEOUT)
        return choices

    def _api(self):
        return storymarket.Storymarket(settings.STORYMARKET_API_KEY)

class OrgChoiceField(StorymarketAPIChoiceField):
    def _call_api(self):
        return self._api().orgs.all()
    
class CategoryChoiceField(StorymarketAPIChoiceField):
    def _call_api(self):
        return self._api().subcategories.all()

class PricingChoiceField(StorymarketAPIChoiceField):
    def _call_api(self):
        return self._api().pricing.all()        

class RightsChoiceField(StorymarketAPIChoiceField):
    def _call_api(self):
        return self._api().rights.all()        

class StorymarketSyncForm(forms.Form):
    """
    A form allowing the choice of sync options for a given model instance.
    """
    org = OrgChoiceField()
    category = CategoryChoiceField()
    pricing = PricingChoiceField()
    rights = RightsChoiceField()
    tags = forms.CharField()
    
    def __init__(self, *args, **kwargs):
        if 'type' in kwargs:
            self.storymarket_type = kwargs.pop('type')
        else:
            raise TypeError("__init__() missing required keyword argument 'type'")
        initial = kwargs.pop('initial', {})
        instance = kwargs.pop('instance', None)

        # If we've been given an object instance then look up initial data
        # from Storymarket. 
        if instance:
            try:
                sync_info = SyncedObject.objects.for_model(instance).get()
            except SyncedObject.DoesNotExist:
                pass
            else:
                initial.update({
                    'org': sync_info.org_id,
                    'category': sync_info.category_id,
                    'pricing': sync_info.pricing_id,
                    'rights': sync_info.rights_id,
                    'tags': sync_info.tags,
                })
        
        super(StorymarketSyncForm, self).__init__(initial=initial, *args, **kwargs)