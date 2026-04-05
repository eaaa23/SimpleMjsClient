import asyncio
import logging
import ssl
from typing import Any, Callable, Coroutine

import websockets

from .protocol_pb2 import Wrapper

EXTRA_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                               'Chrome/71.0.3578.98 Safari/537.36'}

ONCE_HOOK = -1


class MSRPCChannel:
    def __init__(self, endpoint: str):
        self._endpoint = endpoint
        self._req_events = {}
        self._new_req_idx = 1
        self._res = {}
        self._hook_fields: dict[int, dict[str, list[Callable[[Any], Coroutine]]]] \
            = {0: {}, ONCE_HOOK: {}}
        self._is_active = False

        self._ws = None
        self._msg_dispatcher = None

    def add_hook(self, msg_type: str, hook: Callable[[Any], Coroutine], field_id: int = 0):
        field = self._hook_fields[field_id]
        if msg_type not in field:
            field[msg_type] = []
        field[msg_type].append(hook)

    def create_hook_field(self, field_id: int):
        self._hook_fields[field_id] = {}

    def destroy_hook_field(self, field_id: int):
        if field_id in self._hook_fields:
            self._hook_fields.pop(field_id)

    def unwrap(self, wrapped):
        wrapper = Wrapper()
        wrapper.ParseFromString(wrapped)
        return wrapper

    def wrap(self, name, data):
        wrapper = Wrapper()
        wrapper.name = name
        wrapper.data = data
        return wrapper.SerializeToString()

    async def connect(self, ms_host, do_ssl=False):
        self._is_active = True
        if do_ssl:
            self._ws = await websockets.connect(self._endpoint, origin=ms_host, additional_headers=EXTRA_HEADERS)
        else:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self._ws = await websockets.connect(self._endpoint, origin=ms_host, ssl=ssl_context,
                                                additional_headers=EXTRA_HEADERS)
        self._msg_dispatcher = asyncio.create_task(self.dispatch_msg())

    def is_active(self):
        return self._is_active

    async def close(self):
        self._msg_dispatcher.cancel()
        try:
            await self._msg_dispatcher
        except asyncio.CancelledError:
            pass
        finally:
            await self._ws.close()

    async def dispatch_msg(self):
        while True:
            msg = await self._ws.recv()
            logging.info(f"Debug-Recv: {msg}")
            type_byte = msg[0]
            if type_byte == 1:  # NOTIFY
                wrapper = self.unwrap(msg[1:])
                self._trigger_hooks(wrapper)
            elif type_byte == 2:  # REQUEST
                wrapper = self.unwrap(msg[3:])
                self._trigger_hooks(wrapper)
            elif type_byte == 3:  # RESPONSE
                idx = int.from_bytes(msg[1:3], 'little')
                if idx not in self._req_events:
                    continue
                self._res[idx] = msg
                self._req_events[idx].set()

    def _trigger_hooks(self, wrapper):
        for field_id, field in self._hook_fields.items():
            for hook in field.get(wrapper.name, []):
                asyncio.create_task(hook(wrapper.data))
            if field_id == ONCE_HOOK:
                field[wrapper.name] = []

    async def send_request(self, name, msg):
        idx = self._new_req_idx
        self._new_req_idx = (self._new_req_idx + 1) % 60007

        wrapped = self.wrap(name, msg)
        pkt = b'\x02' + idx.to_bytes(2, 'little') + wrapped

        evt = asyncio.Event()
        self._req_events[idx] = evt
        logging.info(f"Debug-Send: {pkt}")
        await self._ws.send(pkt)
        await evt.wait()

        if idx not in self._res:
            return None
        res = self._res[idx]
        del self._res[idx]

        if idx in self._req_events:
            del self._req_events[idx]

        body = self.unwrap(res[3:])

        return body.data


class MSRPCService:

    def __init__(self, channel):
        self._channel = channel

    def get_package_name(self):
        raise NotImplementedError

    def get_service_name(self):
        raise NotImplementedError

    def get_req_class(self, method):
        raise NotImplementedError

    def get_res_class(self, method):
        raise NotImplementedError

    async def call_method(self, method, req):
        msg = req.SerializeToString()
        name = '.{}.{}.{}'.format(self.get_package_name(), self.get_service_name(), method)
        res_msg = await self._channel.send_request(name, msg)
        res_class = self.get_res_class(method)
        res = res_class()
        res.ParseFromString(res_msg)
        return res
