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

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class FirehoseView(View):
    async def get(self, request):
        """
        Get the next post from the firehose
        Endpoint: GET /api/posts/next/
        """
        try:
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
        Requires authentication
        """
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)

        try:
            data = json.loads(request.body)
            
            # Get required fields
            post_cid = data.get('post_cid')
            post_uri = data.get('post_uri')
            author_did = data.get('author_did')
            liked = data.get('liked')
            
            # Optional fields
            post_text = data.get('post_text')
            created_at = data.get('created_at')

            # Validate required fields
            if not all([post_cid, post_uri, author_did, liked is not None]):
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields: post_cid, post_uri, author_did, liked'
                }, status=400)

            # Create or update the interaction
            interaction, created = await PostInteraction.objects.aupdate_or_create(
                user=request.user,
                post_cid=post_cid,
                defaults={
                    'post_uri': post_uri,
                    'author_did': author_did,
                    'post_text': post_text,
                    'created_at': created_at,
                    'liked': liked
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