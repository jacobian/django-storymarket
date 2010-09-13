import storymarket
from django.conf import settings

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
    manager = getattr(api, storymarket_type)
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
