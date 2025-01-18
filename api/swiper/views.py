import logging
from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .services.firehose import FirehoseService
from .models import PostSwipe
import json
import asyncio

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class FirehoseView(View):
    async def get(self, request):
        """Get the next post"""
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
        """Record a swipe decision"""
        logger.info("Received swipe decision")
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            liked = data.get('liked')
            repo = data.get('repo')
            commit = data.get('commit')

            logger.debug(f"Swipe data: post_id={post_id}, liked={liked}, repo={repo}, commit={commit}")

            if not all([post_id, liked is not None, repo]):
                logger.warning("Missing required fields in swipe request")
                return JsonResponse({
                    'success': False,
                    'message': 'Missing required fields'
                }, status=400)

            # Use sync_to_async for database operations
            create_post_swipe = sync_to_async(PostSwipe.objects.create)
            await create_post_swipe(
                post_id=post_id,
                liked=liked,
                repo=repo,
                commit=commit
            )
            logger.info(f"Successfully recorded swipe for post_id: {post_id}")

            return JsonResponse({'success': True})

        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing swipe: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500) 