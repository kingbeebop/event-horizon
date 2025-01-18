from django.core.management.base import BaseCommand
import asyncio
from ...firehose_service import FirehoseService

class Command(BaseCommand):
    help = 'Starts the Bluesky firehose service'

    def handle(self, *args, **options):
        async def run():
            service = await FirehoseService.create_and_start()
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass

        asyncio.run(run()) 