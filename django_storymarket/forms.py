import operator
import storymarket
from django import forms
from django.core.cache import cache
from django.conf import settings
from .models import SyncedObject

# Timeout for choices cached from Storymarket. 5 minutes.
CHOICE_CACHE_TIMEOUT = 600

class StorymarketSyncForm(forms.ModelForm):
    """
    A form allowing the choice of sync options for a given model instance.
    """    
    class Meta:
        model = SyncedObject
        fields = ['org', 'category', 'tags']
    
    def __init__(self, *args, **kwargs):
        super(StorymarketSyncForm, self).__init__(*args, **kwargs)

        # Override some fields. Tags is left alone; the default is fine.
        self.fields['org']      = forms.TypedChoiceField(label='Org', 
                                                         choices=self._choices('orgs'),
                                                         coerce=int)
        self.fields['category'] = forms.TypedChoiceField(label='Category',
                                                         choices=self._choices('subcategories'),
                                                         coerce=int)
        # self.fields['pricing']  = forms.ChoiceField(label='Pricing', choices=self._choices('pricing'))
        # self.fields['rights']   = forms.ChoiceField(label='Rights', choices=self._choices('rights'))
    
    def _choices(self, manager_name):
        """
        Generate a list of choices from a given storymarket manager type.
        
        These choices are cached to save API hits, sorted, and an empty
        choice is included.
        """
        cache_key = 'storymarket_choice_cache:%s' % manager_name
        choices = cache.get(cache_key)
        if choices is None:
            manager = getattr(self._api, manager_name)
            objs = sorted(manager.all(), key=operator.attrgetter('name'))
            
            # If there's only a single object, just select it -- don't offer
            # an empty choice. Otherwise, offer an empty.
            if len(objs) == 1:
                empty_choice = []
            else:
                empty_choice = [(u'', u'---------')]
            choices = empty_choice + [(o.id, o.name) for o in objs]
            cache.set(cache_key, choices, CHOICE_CACHE_TIMEOUT)
        return choices
        
    @property
    def _api(self):
        return storymarket.Storymarket(settings.STORYMARKET_API_KEY)