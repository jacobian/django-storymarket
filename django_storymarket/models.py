import datetime
import operator
import storymarket
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from . import converters 
from . import managers

STORYMARKET_TYPES = ("audio", "data", "photo", "text", "video")
STORYMARKET_TYPE_CHOICES = [(t, t) for t in STORYMARKET_TYPES]

def _ct(model):
    """Shortcut for getting a content type for a model."""
    return ContentType.objects.get_for_model(model)

class SyncedObject(models.Model):
    """
    Tracks an object that's been synced to Storymarket.
    """
    # The Django object that's been synced.
    content_type = models.ForeignKey(ContentType, related_name='storymarket_synced_objects')
    object_pk    = models.TextField()
    object       = GenericForeignKey('content_type', 'object_pk')
    
    # The Storymarket content object that's been synced to.
    storymarket_type = models.CharField(max_length=50, choices=STORYMARKET_TYPE_CHOICES)
    storymarket_id   = models.PositiveIntegerField()
    
    # For ease of local reference, the IDs of the related org/category/etc.
    org_id      = models.PositiveIntegerField()
    category_id = models.PositiveIntegerField()
    pricing_id  = models.PositiveIntegerField(blank=True, null=True)
    rights_id   = models.PositiveIntegerField(blank=True, null=True)
    
    # When we last did a sync.
    last_updated = models.DateTimeField(default=datetime.datetime.now)
    
    objects = managers.SyncedObjectManager()
    
    def __unicode__(self):
        return "%s synced as %s ID=%s" % (self.object, self.storymarket_type, self.storymarket_id)
    
    def _storymarket_property(id_attr, manager_name):
        """
        Helper to construct related Storymarket object properties.
        """
        api = storymarket.Storymarket(settings.STORYMARKET_API_KEY)
        manager = getattr(api, manager_name)
        def _getter(self):
            return manager.get(id=getattr(self, id_attr))
        def _setter(self, val):
            setattr(self, id_attr, val.id)
        return property(_getter, _setter)
        
    # Properties for accessing the property storymarket objects
    org      = _storymarket_property('org_id', 'orgs')
    category = _storymarket_property('category_id', 'subcategories')
    pricing  = _storymarket_property('pricing_id', 'pricing')
    rights   = _storymarket_property('rights_id', 'rights')
    
class AutoSyncedModel(models.Model):
    """
    A model that should be auto-synced to Storymarket, perhaps upon
    matching some associated sync rules.
    """
    content_type = models.ForeignKey(ContentType, 
                                     related_name='storymarket_autosynced_models',
                                     limit_choices_to=models.Q(
                                        id__in=[_ct(m).id for m in converters.registered_models()]
                                     ))
    enabled = models.BooleanField(default=False)
    
    def __unicode__(self):
        return "Autosync for %s%s" % (self.content_type, "" if self.enabled else " (disabled)")

    def should_sync(self, instance):
        """
        Returns True if the given instance should be synced.
        """
        if not self.enabled or _ct(instance) != self.content_type:
            return False
        
        for rule in self.rules.all():
            rule_opinion = rule.should_sync(instance)
            if rule_opinion is False:
                return False
            
        return True

AUTO_SYNC_INCLUDE_CHOICES = (
    (True,  'include'),
    (False, 'exclude'),
)

# The stored values here are the function names in the `operator` module or
# names of string methods. They're prefixed by ! to negate the results. The
# human-readable names are stolen from iTunes' "smart playlists" -- I don't
# have money for HCI research, but Apple (hopefully) already did it for me.
AUTO_SYNC_OP_CHOICES = (
    ('eq',          'is'),
    ('ne',          'is not'),
    ('lt',          'is less than'),
    ('lte',         'is less than or equal to'),
    ('gt',          'is greater than'),
    ('gte',         'is greater than or equal to'),
    ('contains',    'contains'),
    ('!contains',   'does not contain'),
    ('startswith',  'starts with'),
    ('!startswith', 'does not start with'),
    ('endswith',    'ends with'),
    ('!endswith',   'does not end with')
)

class AutoSyncRule(models.Model):
    """
    An individual rule conditionally syncing models.
    
    This generates rules of the form::
    
        <include/exclude> instances where <field> <op> <value>
        
    e.g.::
    
        include instances where name contains 'joe'
        exclude instances where photographer_id == 14
        
    etc.
    
    Right now this only "ands" together all the rules -- there's not
    special nested rule logic. For more complicated uses, you'll need to
    listen to the model's save signal and do the sync manually.
    """
    sync_model = models.ForeignKey(AutoSyncedModel, related_name='rules')
    
    # Whether to include (True) or exclude (False) models matching this rule.
    include = models.BooleanField("Include?", default=True, choices=AUTO_SYNC_INCLUDE_CHOICES)
    
    # The field name
    # TODO: would be nice to support object traversal via dots.
    field = models.CharField("Where this field...", max_length=500)
    
    # The operator (contains, lessthan, etc.)
    op = models.CharField("is/is not/...", max_length=50, choices=AUTO_SYNC_OP_CHOICES)
    
    # The value to compare against.
    value = models.CharField("this value", max_length=250)
    
    def __unicode__(self):
        return "%s.%s %s '%s'" % (self.sync_model.content_type, self.field, self.op, self.value)
        
    def should_sync(self, instance):
        """
        Does this rule think we should sync the given instance?
        
        Returns ``True`` for a "yes", ``False`` for a "no", and ``None`` if
        this rule has no opinion or something went wrong.
        """
        # Try to get the value named by self.field.
        try:
            field_val = getattr(instance, self.field)
        except AttributeError:
            return None
        
        # Try to look up the operator function, first as a member
        # of the operator library, and then as a str method
        op_func_name = self.op.lstrip('!')
        try:
            op_func = getattr(operator, op_func_name)
        except AttributeError:
            try:
                op_func = getattr(str, op_func_name)
            except AttributeError:
                return None 
        
        # If the op was a negative one, negate the op.
        if self.op.startswith('!'):
            op_func = lambda lhs, rhs: not op_func(lhs, rhs)
        
        # Try to check for a match.
        try:
            match = op_func(field_val, value)
        except (ValueError, TypeError):
            return None
        
        # Negate the match if self.include is False (and thus this is an
        # exclude rule).
        return match if self.include else not match
        