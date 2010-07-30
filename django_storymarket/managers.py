import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType

class SyncedObjectManager(models.Manager):
    def for_model(self, obj):
        """
        Look up the sycned record for a given model.
        
        Returns a QuerySet, not the original instance. That's so that you
        can do either::
        
            >>> SyncedObject.objects.for_model(obj).exists()
            True
            
        Or::
        
            >>> SyncedObject.objects.for_model(obj).get()
            <SyncedObject: ...>
            
        Depending on what information you need.
        """
        return self.filter(
            content_type = ContentType.objects.get_for_model(obj),
            object_pk = obj.pk,
        )
        
    def mark_synced(self, django_obj, storymarket_obj):
        """
        Mark ``django_obj`` as having been synced to ``storymarket_obj``.
        
        Returns ``(SyncedObject, created)``, just like ``get_or_create()``.
        """
        defaults = dict(
            storymarket_type = storymarket_obj.__class__.__name__.lower(),
            storymarket_id = storymarket_obj.id,
            org_id = storymarket_obj.org.id,
            category_id = storymarket_obj.category.id,
            pricing_id = storymarket_obj.pricing.id,
            rights_id = storymarket_obj.rights.id,
            last_updated = datetime.datetime.now(),
        )
        so, created = self.get_or_create(
            content_type = ContentType.objects.get_for_model(django_obj),
            object_pk = django_obj.pk,
            defaults = defaults,
        )
        if not created:
            so.__dict__.update(defaults)
            so.save()
        
        return so, created