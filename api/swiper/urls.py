from django.urls import path
from .views import FirehoseView, LeaderboardView

urlpatterns = [
    # GET /api/posts/next/
    # Returns the next available post from the Bluesky firehose
    # Response: {
    #   "success": true,
    #   "post": {
    #     "cid": "bafyreid...",
    #     "uri": "at://did:plc:...",
    #     "author_did": "did:plc:...",
    #     "text": "Post content...",
    #     "created_at": "2024-01-18T..."
    #   }
    # }
    path('posts/next/', FirehoseView.as_view(), name='next-post'),

    # POST /api/posts/interact/
    # Record a user's like/dislike interaction with a post
    # Requires authentication
    # Request body: {
    #   "post_cid": "bafyreid...",
    #   "post_uri": "at://did:plc:...",
    #   "author_did": "did:plc:...",
    #   "liked": true/false,
    #   "post_text": "Optional post content...",
    #   "created_at": "Optional timestamp..."
    # }
    path('posts/interact/', FirehoseView.as_view(), name='post-interaction'),

    # GET /api/posts/leaderboard/
    # Get the top posts sorted by likes/dislikes
    path('posts/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
] 