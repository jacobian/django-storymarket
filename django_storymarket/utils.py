import storymarket
from django.conf import settings
from django_storymarket.models import SyncedObject

QUEUE_UPLOADS = getattr(settings, 'STORYMARKET_QUEUE_UPLOADS', False)
if QUEUE_UPLOADS:
    from .tasks import upload_blob_task


def save_to_storymarket(obj, storymarket_type, data):
    """
    Push an object to Storymarket.
    
    Called from the various parts of the admin that need to upload
    objects -- ``save_model``, the ``upload_to_storymarket`` action,
    etc.
    """    
    # TODO: should figure out how to do an update if the object already exists.
    api = storymarket.Storymarket(settings.STORYMARKET_API_KEY)

    # Fix some field names mapping from local to storymarket names
    if 'pricing' in data:
        data['pricing_scheme'] = data.pop('pricing')
    if 'rights' in data:
        data['rights_scheme'] = data.pop('rights')

    # Packages are handled slightly different: each sub-item has to be
    # uploaded first, then the package needs to be created.
    if storymarket_type == 'package':
        package_items = data.pop('items')
        for subitem in package_items:
            subobj = subitem.pop('object')
            subtype = subitem.pop('type').rstrip('s')
            synced, created = save_to_storymarket(subobj, subtype, subitem)
            data.setdefault('%s_items' % subtype, []).append(synced.storymarket_id)
    
    # Grab the appropriate manager for the given storymarket type.
    # We want to "be liberal in what [we] accept," so try both with
    # and without a trailing "s" -- this allows "photo" as well
    # as "photos", for example.
    try:
        manager = getattr(api, storymarket_type)
    except AttributeError:
        try:
            manager = getattr(api, storymarket_type+'s')
        except AttributeError:
            raise ValueError("Invalid storymarket type: %r" % storymarket_type)
    
    # Pull out the blob from the data since it gets uploaded seperately.
    blob = data.pop('blob', None)
    
    sm_obj = manager.create(data)

    # Upload the blob. This queues nad backgrounds the task using
    # Celery if STORYMARKET_QUEUE_UPLOADS is True.
    if blob:
        if QUEUE_UPLOADS:
            upload_blob_task.delay(sm_obj, blob)
        else:
            sm_obj.upload_blob(blob)

    return SyncedObject.objects.mark_synced(obj, sm_obj)
