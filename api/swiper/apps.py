from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class SwiperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'swiper'

    def ready(self):
        try:
            from .services.firehose import FirehoseService
            FirehoseService.get_instance()
            logger.info("FirehoseService initialized in app startup")
        except Exception as e:
            logger.error(f"Error initializing FirehoseService: {e}") 