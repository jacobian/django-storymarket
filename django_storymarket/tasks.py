"""
Celery task defintions.

Queuing uploads with Celery is optional, but high recommended.
"""

from celery.decorators import task

@task
def upload_blob_task(sm_obj, blob):
    sm_obj.upload_blob(blob)