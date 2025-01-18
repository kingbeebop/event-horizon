import asyncio
import websockets
import cbor2
from datetime import datetime
from typing import Optional, Dict, List
import logging
import json

logger = logging.getLogger(__name__)

class RepoEvent:
    def __init__(self, repo: str, ops: List[Dict], seq: Optional[int] = None, commit: Optional[str] = None):
        self.repo = repo
        self.ops = ops
        self.seq = seq
        self.commit = commit
        self.timestamp = datetime.now().isoformat()

    @staticmethod
    def is_post_creation(ops: List[Dict]) -> bool:
        """Check if any operation is creating a post"""
        for op in ops:
            logger.debug(f"Checking operation: {json.dumps(op, indent=2)}")
            if (op.get('action') == 'create' and 
                isinstance(op.get('path'), str) and
                op.get('path').startswith('app.bsky.feed.post')):
                logger.info(f"Found post creation: {json.dumps(op, indent=2)}")
                return True
        return False

    def extract_post_content(self) -> Optional[Dict]:
        """Extract the post content from the operations"""
        try:
            for op in self.ops:
                if (op.get('action') == 'create' and 
                    isinstance(op.get('path'), str) and
                    op.get('path').startswith('app.bsky.feed.post')):
                    
                    record = op.get('record', {})
                    logger.info(f"Extracted post content: {json.dumps(record, indent=2)}")
                    
                    return {
                        'uri': f"at://{self.repo}/{op.get('path')}",
                        'cid': op.get('cid'),
                        'author': self.repo,
                        'record': record,
                        'timestamp': self.timestamp
                    }
            return None
        except Exception as e:
            logger.error(f"Error extracting post content: {e}")
            return None

class FirehoseService:
    _instance = None
    _initialized = False

    def __init__(self):
        self.uri = "wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos"
        self.current_post = None

    @classmethod
    def get_instance(cls) -> 'FirehoseService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def fetch_single_post(self) -> Optional[RepoEvent]:
        """Get a single post from the firehose and disconnect"""
        logger.info("=== Starting fetch_single_post ===")
        try:
            logger.info("Attempting to connect to websocket...")
            async with websockets.connect(self.uri) as websocket:
                logger.info("Connected to Bluesky firehose")
                
                start_time = datetime.now()
                while (datetime.now() - start_time).seconds < 10:
                    try:
                        logger.info("Waiting for message...")
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        logger.info(f"Received message of length: {len(message)}")
                        
                        try:
                            # First byte is frame type (0x0 for frame, 0x1 for control)
                            frame_type = message[0]
                            logger.debug(f"Frame type: {hex(frame_type)}")
                            
                            if frame_type not in (0x0, 0x1):
                                logger.warning(f"Unknown frame type: {hex(frame_type)}")
                                continue
                            
                            # Decode CBOR data (rest of message after frame type)
                            decoded_data = cbor2.loads(message[1:])
                            logger.debug(f"Message type: {decoded_data.get('#commit', 'operation')}")
                            logger.debug(f"Available keys: {list(decoded_data.keys())}")
                            
                            # Handle commit message
                            if '#commit' in decoded_data:
                                logger.debug("Skipping commit message")
                                continue
                            
                            if 'ops' in decoded_data:
                                ops = decoded_data.get('ops', [])
                                if ops:
                                    logger.debug(f"Found {len(ops)} operations")
                                    
                                    # Check if this is a post creation
                                    if RepoEvent.is_post_creation(ops):
                                        logger.info("Found post creation event")
                                        event = RepoEvent(
                                            repo=decoded_data.get('repo'),
                                            ops=ops,
                                            seq=decoded_data.get('seq'),
                                            commit=decoded_data.get('commit')
                                        )
                                        
                                        # Extract post content
                                        post_content = event.extract_post_content()
                                        if post_content:
                                            logger.info("Successfully extracted post content")
                                            event.post_content = post_content
                                            self.current_post = event
                                            return event
                                        else:
                                            logger.warning("Failed to extract post content")
                                            continue
                                    else:
                                        logger.debug("Not a post creation operation")
                                        continue
                                else:
                                    logger.debug("Empty ops list")
                                    continue
                                    
                        except cbor2.CBORDecodeError as e:
                            logger.error(f"CBOR decode error: {e}")
                            continue
                            
                    except asyncio.TimeoutError:
                        logger.debug("Individual message timeout, continuing...")
                        continue
                        
                logger.warning("Timed out waiting for a post creation event")
                return None
                    
        except Exception as e:
            logger.error(f"Error in fetch_single_post: {str(e)}", exc_info=True)
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    async def get_latest_post(self) -> Optional[RepoEvent]:
        """Get the next post, either cached or fetch new"""
        try:
            if self.current_post:
                logger.info("Returning cached post")
                post = self.current_post
                self.current_post = None
                return post
            
            logger.info("No cached post, fetching new one")
            return await self.fetch_single_post()
            
        except Exception as e:
            logger.error(f"Error in get_latest_post: {e}")
            return None 