from django.db import models

class PostSwipe(models.Model):
    post_id = models.CharField(max_length=255)
    liked = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    repo = models.CharField(max_length=255)
    commit = models.CharField(max_length=255, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['post_id']),
            models.Index(fields=['timestamp']),
        ] 