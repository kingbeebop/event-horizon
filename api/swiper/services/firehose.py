from atproto import Client
import asyncio
import logging
import json
import cbor2
import websockets
import threading
from typing import Optional, Dict, Any, IO
from io import BytesIO
import struct
from base64 import b32encode

logger = logging.getLogger(__name__)

class JSONEncoderWithBytes(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        return super().default(obj)

class FirehoseService:
    _instance = None

    def __init__(self):
        self.uri = "wss://bsky.network/xrpc/com.atproto.sync.subscribeRepos"
        self.current_post: Optional[Dict] = None
        self.running = False
        self.start_listener()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def read_uvarint(self, stream: IO[bytes]) -> int:
        shift = 0
        result = 0
        while True:
            byte = stream.read(1)
            if not byte:
                raise ValueError("Unexpected end of input while parsing varint.")
            byte_val = byte[0]
            result |= (byte_val & 0x7F) << shift
            shift += 7
            if not (byte_val & 0x80):
                break
        return result

    def read_cbor_uint(self, stream: IO[bytes], additional_info: int) -> int:
        if additional_info < 24:
            return additional_info
        elif additional_info == 24:
            return struct.unpack(">B", stream.read(1))[0]
        elif additional_info == 25:
            return struct.unpack(">H", stream.read(2))[0]
        elif additional_info == 26:
            return struct.unpack(">I", stream.read(4))[0]
        elif additional_info == 27:
            return struct.unpack(">Q", stream.read(8))[0]
        else:
            raise ValueError(f"Unsupported additional info: {additional_info}")

    def read_dag_cbor(self, stream: IO[bytes]) -> Any:
        initial_byte = stream.read(1)
        if not initial_byte:
            raise ValueError("Unexpected end of input while decoding CBOR.")
        
        initial_value = initial_byte[0]
        major_type = initial_value >> 5
        additional_info = initial_value & 0x1F

        if major_type == 0:  # Unsigned integer
            return self.read_cbor_uint(stream, additional_info)
        elif major_type == 1:  # Negative integer
            return -1 - self.read_cbor_uint(stream, additional_info)
        elif major_type == 2:  # Byte string
            length = self.read_cbor_uint(stream, additional_info)
            return stream.read(length)
        elif major_type == 3:  # Text string
            length = self.read_cbor_uint(stream, additional_info)
            return stream.read(length).decode("utf-8")
        elif major_type == 4:  # Array
            length = self.read_cbor_uint(stream, additional_info)
            return [self.read_dag_cbor(stream) for _ in range(length)]
        elif major_type == 5:  # Map
            length = self.read_cbor_uint(stream, additional_info)
            return {self.read_dag_cbor(stream): self.read_dag_cbor(stream) for _ in range(length)}
        elif major_type == 6:  # Tagged item
            tag = self.read_cbor_uint(stream, additional_info)
            value = self.read_dag_cbor(stream)
            if tag == 42:  # CID
                return self.encode_dag_cbor_cid(value)
            return value
        elif major_type == 7:  # Simple values and floats
            if additional_info == 20:
                return False
            elif additional_info == 21:
                return True
            elif additional_info == 22:
                return None
            elif additional_info == 23:
                return None
            elif additional_info == 26:
                return struct.unpack(">f", stream.read(4))[0]
            elif additional_info == 27:
                return struct.unpack(">d", stream.read(8))[0]
        raise ValueError(f"Unsupported type: {major_type}")

    def encode_dag_cbor_cid(self, value: bytes) -> str:
        if len(value) != 37:
            return value.hex()
        cid_data = value[1:]
        b32_str = b32encode(cid_data).decode("ascii").replace("=", "").lower()
        return f"b{b32_str}"

    def read_car_node(self, stream: IO[bytes]) -> Dict:
        bytes_data = self.read_car_ld(stream)
        cid_bytes = bytes_data[:36]
        data_cbor = bytes_data[36:]
        data = self.read_dag_cbor(BytesIO(data_cbor))
        return {"cid": self.encode_dag_cbor_cid(b"\00" + cid_bytes), "data": data}

    def read_car_ld(self, stream: IO[bytes]) -> bytes:
        length = self.read_uvarint(stream)
        return stream.read(length)

    def read_carv1(self, stream: IO[bytes]) -> Dict:
        header_bytes = self.read_car_ld(stream)
        with BytesIO(header_bytes) as bio:
            header = self.read_dag_cbor(bio)
        
        blocks = []
        while True:
            try:
                node = self.read_car_node(stream)
                blocks.append(node)
            except:
                break
        
        return {"header": header, "blocks": blocks}

    def read_firehose_frame(self, frame: bytes) -> Dict:
        with BytesIO(frame) as bio:
            header = self.read_dag_cbor(bio)
            body = self.read_dag_cbor(bio)
            
            body_blocks = body.get("blocks")
            if isinstance(body_blocks, bytes):
                body["blocks"] = self.read_carv1(BytesIO(body_blocks))
            
            return {"header": header, "body": body}

    async def listen_to_firehose(self):
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    logger.info("Connected to Bluesky firehose")
                    
                    while self.running:
                        message = await websocket.recv()
                        frame = self.read_firehose_frame(message)
                        
                        # Log the decoded message
                        logger.info("\n=== Decoded Message ===")
                        logger.info(json.dumps(frame, indent=2, cls=JSONEncoderWithBytes))
                        
                        # Check for posts
                        if frame['header']['t'] == '#commit':
                            for op in frame['body'].get('ops', []):
                                if (op.get('action') == 'create' and 
                                    'app.bsky.feed.post' in str(op.get('path'))):
                                    for block in frame['body'].get('blocks', {}).get('blocks', []):
                                        if block['data'].get('$type') == 'app.bsky.feed.post':
                                            self.current_post = {
                                                'cid': block['cid'],
                                                'uri': f"at://{frame['body'].get('repo')}/{op.get('path')}",
                                                'author_did': frame['body'].get('repo'),
                                                'text': block['data'].get('text'),
                                                'created_at': block['data'].get('createdAt')
                                            }
                                            logger.info("\n🔥 NEW POST FOUND!")
                                            logger.info(json.dumps(self.current_post, indent=2))
                        
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)

    def start_listener(self):
        """Start the background listener thread"""
        if not self.running:
            self.running = True
            
            async def run_listener():
                await self.listen_to_firehose()
                
            def run_async_listener():
                asyncio.run(run_listener())
            
            thread = threading.Thread(target=run_async_listener, daemon=True)
            thread.start()
            logger.info("Started background listener")

    async def get_latest_post(self) -> str:
        """Get the currently cached post"""
        if self.current_post:
            post = self.current_post
            self.current_post = None  # Clear after returning
            return json.dumps({
                'success': True,
                'post': post
            }, indent=2)
        else:
            return json.dumps({
                'success': False,
                'message': 'No posts available, try again later'
            })

    def stop_listener(self):
        """Stop the background listener"""
        self.running = False
