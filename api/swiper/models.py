from django.db import models
from django.contrib.auth.models import User

class PostInteraction(models.Model):
    # The post's unique identifiers
    post_cid = models.CharField(max_length=255)  # The CID of the post
    post_uri = models.CharField(max_length=255, null=True, blank=True)  # Full at:// URI
    author_did = models.CharField(max_length=255, null=True, blank=True)  # The author's DID
    
    # The post content (optional, if you want to cache it)
    post_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    
    # The interaction
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    liked = models.BooleanField(null=True)
    double_dislike = models.BooleanField(default=False)  # New field for double dislike
    interaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Since user is now nullable, we only want unique constraint when user exists
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post_cid'],
                condition=models.Q(user__isnull=False),
                name='unique_user_post'
            )
        ] 