"""
Celery task defintions.

Queuing uploads with Celery is optional, but high recommended.
"""

# Nose tries to auto-import this module, which of course
# fails if Celery isn't installed. Doing this lets the
# tests run.
try:
    from celery.decorators import task
except ImportError:
    def task(func): return func

@task
def upload_blob_task(sm_obj, blob):
    sm_obj.upload_blob(blob)