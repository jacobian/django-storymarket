import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

STORYMARKET_TYPES = ("audio", "data", "photo", "text", "video")
STORYMARKET_TYPE_CHOICES = [(t, t) for t in STORYMARKET_TYPES]

class SyncedObjectManager(models.Manager):
    def for_model(self, obj):
        return self.filter(
            content_type = ContentType.objects.get_for_model(obj),
            object_pk = obj.pk,
        )
        
    def mark_synced(self, django_obj, storymarket_obj):
        defaults = dict(
            storymarket_type = storymarket_obj.__class__.__name__.lower(),
            storymarket_id = storymarket_obj.id,
        )
        so, created = self.get_or_create(
            content_type = ContentType.objects.get_for_model(obj),
            object_pk = obj.pk,
            defaults = defaults,
        )
        if not created:
            so.storymarket_type = defaults['storymarket_type']
            so.storymarket_id = defaults['storymarket_id']
            so.last_updated = datetime.datetime.now()
            so.save()

class SyncedObject(models.Model):
    """
    Tracks an object that's been synced to Storymarket.
    """
    content_type = models.ForeignKey(ContentType)
    object_pk = models.TextField()
    object = GenericForeignKey('content_type', 'object_pk')
    storymarket_type = models.CharField(max_length=50, choices=STORYMARKET_TYPE_CHOICES)
    storymarket_id = models.PositiveIntegerField()
    last_updated = models.DateTimeField(default=datetime.datetime.now)
    
    objects = SyncedObjectManager()
    
    def __unicode__(self):
        return "%s synced as %s ID=%s" % (self.object, self.storymarket_type, self.storymarket_id)