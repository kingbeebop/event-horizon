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
        """Get the next post to show"""
        logger.info("=== Starting GET request for next post ===")
        try:
            # Add timeout to prevent hanging
            logger.info("Getting FirehoseService instance...")
            service = FirehoseService.get_instance()
            logger.info("Got service instance, fetching post...")
            
            # Add timeout to the get_latest_post call
            try:
                event = await asyncio.wait_for(service.get_latest_post(), timeout=10.0)
                logger.info(f"Got response from get_latest_post: {event}")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for post")
                return JsonResponse({
                    'success': False,
                    'message': 'Request timed out'
                }, status=504)
            
            if event:
                logger.info(f"Successfully got post from repo: {event.repo}")
                return JsonResponse({
                    'success': True,
                    'event': event.post_content if hasattr(event, 'post_content') else {
                        'repo': event.repo,
                        'ops': event.ops,
                        'seq': event.seq,
                        'commit': event.commit,
                        'timestamp': event.timestamp
                    }
                })
            else:
                logger.warning("No posts available")
                return JsonResponse({
                    'success': False,
                    'message': 'No posts available'
                })
        except Exception as e:
            logger.error(f"Error getting next post: {str(e)}", exc_info=True)
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': 'Internal server error'
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