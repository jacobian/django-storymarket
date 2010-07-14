from django.db import models

class ExampleStory(models.Model):
    """
    (ExampleStory description)
    """
    headline = models.CharField(max_length=200)
    body = models.TextField()
    
    class Meta:
        verbose_name_plural = 'example stories'
    
    def __unicode__(self):
        return self.headline