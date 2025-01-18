from django.db import models
from django.contrib.auth.models import User

class PostInteraction(models.Model):
    # The post's unique identifiers
    post_cid = models.CharField(max_length=255)  # The CID of the post
    post_uri = models.CharField(max_length=255)  # Full at:// URI
    author_did = models.CharField(max_length=255)  # The author's DID
    
    # The post content (optional, if you want to cache it)
    post_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    
    # The interaction
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    liked = models.BooleanField()
    interaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a user can only interact once with each post
        unique_together = ['user', 'post_cid'] 