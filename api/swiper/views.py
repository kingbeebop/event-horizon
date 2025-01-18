import logging
from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .services.firehose import FirehoseService
from .models import PostInteraction
import json
import asyncio
from django.db.models import Count, Case, When, IntegerField, Q

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class FirehoseView(View):
    async def get(self, request):
        """
        Get the next post from the firehose
        First tries to find an unvoted post from the database,
        if none found, fetches a new post from the firehose
        Endpoint: GET /api/posts/next/
        """
        try:
            # First try to find a post that hasn't been voted on by this user
            if request.user.is_authenticated:
                # Get all post_cids that the user has already voted on
                voted_cids = await PostInteraction.objects.filter(
                    user=request.user
                ).values_list('post_cid', flat=True)
                
                # Find a post that hasn't been voted on
                unvoted_post = await PostInteraction.objects.exclude(
                    post_cid__in=voted_cids
                ).values(
                    'post_cid',
                    'post_uri',
                    'author_did',
                    'post_text',
                    'created_at'
                ).first()
                
                if unvoted_post:
                    return JsonResponse({
                        'success': True,
                        'post': unvoted_post
                    })

            # If no unvoted posts found or user not authenticated, fetch from firehose
            service = FirehoseService.get_instance()
            response = await service.get_latest_post()
            return JsonResponse(json.loads(response))
            
        except Exception as e:
            logger.error(f"Error getting next post: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

    async def post(self, request):
        """
        Record a user's interaction with a post
        Endpoint: POST /api/posts/interact/
        """
        try:
            data = json.loads(request.body)
            
            # Get required fields
            post_cid = data.get('post_cid')
            liked = data.get('liked')
            double_dislike = data.get('double_dislike', False)  # New field with default False
            
            # Validate required fields
            if not all([post_cid, liked is not None]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields: post_cid, liked'
                }, status=400)

            # Optional fields
            post_uri = data.get('post_uri')
            author_did = data.get('author_did')
            post_text = data.get('post_text')
            created_at = data.get('created_at')

            # Create or update the interaction
            interaction, created = await PostInteraction.objects.aupdate_or_create(
                post_cid=post_cid,
                defaults={
                    'post_uri': post_uri,
                    'author_did': author_did,
                    'post_text': post_text,
                    'created_at': created_at,
                    'liked': liked,
                    'double_dislike': double_dislike,
                    'user': request.user if request.user.is_authenticated else None
                }
            )

            logger.info(f"{'Created' if created else 'Updated'} interaction for post {post_cid}")
            
            return JsonResponse({
                'success': True,
                'action': 'created' if created else 'updated',
                'post_cid': post_cid
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing interaction: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500) 

@method_decorator(csrf_exempt, name='dispatch')
class LeaderboardView(View):
    def get(self, request):
        """
        Get the leaderboard of posts sorted by likes/dislikes
        Endpoint: GET /api/posts/leaderboard/
        """
        try:
            # Query posts with their like, dislike, and double dislike counts
            posts = PostInteraction.objects.values('post_cid', 'post_text', 'post_uri', 'author_did', 'created_at').annotate(
                likes=Count(Case(
                    When(liked=True, then=1),
                    output_field=IntegerField(),
                )),
                dislikes=Count(Case(
                    When(liked=False, double_dislike=False, then=1),
                    output_field=IntegerField(),
                )),
                double_dislikes=Count(Case(
                    When(liked=False, double_dislike=True, then=1),
                    output_field=IntegerField(),
                ))
            ).filter(
                # Only include posts that have at least one interaction
                Q(likes__gt=0) | Q(dislikes__gt=0) | Q(double_dislikes__gt=0)
            ).order_by('-likes', 'dislikes', 'double_dislikes')[:20]  # Get top 20 posts

            return JsonResponse({
                'success': True,
                'posts': list(posts)
            })
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500) 