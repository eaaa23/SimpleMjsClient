import asyncio
import logging
import queue
from functools import partial
from threading import Thread
from typing import Any, Callable

import culsans

from .client import MahjongSoulClient
from .exceptions import ClientError, ControllerError, MjsError


class UpdateEvent:
    pass


def _mirror(client_method):
    def retval(f):
        def func(self, *args, **kwargs):
            self._put_queue_upload((partial(client_method, self.client), args, kwargs))
        return func
    return retval


class ClientController:
    def __init__(self, client: MahjongSoulClient):
        self.client = client
        self._update_trigger: Callable[[], Any] | None = None
        self._error_trigger: Callable[[MjsError], Any] | None = None
        self._queue_upload: culsans.Queue = culsans.Queue()
        self._queue_download: queue.Queue[UpdateEvent] = queue.Queue()
        self._controller_thread = None
        self.started = False

    def set_update_trigger(self, f: Callable[[], Any]):
        self._update_trigger = f

    def set_error_hook(self, f: Callable[[MjsError], Any]):
        self._error_trigger = f

    async def _update_event_checker(self):
        while True:
            await self.client.update_event.wait()
            self._update_trigger()
            self.client.update_event.clear()

    async def _run(self):
        asyncio.create_task(self._update_event_checker())
        while True:
            func, args, kwargs = await self._queue_upload.async_q.get()
            logging.info("Get task")
            try:
                await func(*args, **kwargs)
            except ClientError as e:
                #logging.error(e)
                self._error_trigger(e)

    def start(self):
        self._controller_thread = Thread(target=asyncio.run, args=(self._run(), ), daemon=True)
        self._controller_thread.start()
        self.started = True

    def _put_queue_upload(self, item: tuple[Callable, tuple, dict]):
        if not self.started:
            raise ControllerError("Controller not started")
        logging.info(f"_put_queue_upload {item}")
        #self._queue_upload.put(item)
        self._queue_upload.sync_q.put(item)

    @_mirror(MahjongSoulClient.connect)
    def connect(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.login)
    def login(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.start_unified_match)
    def start_unified_match(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.create_room)
    def create_room(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.room_add_bot)
    def room_add_bot(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.join_room)
    def join_room(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.room_start)
    def room_start(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.room_kick)
    def room_kick(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.room_ready)
    def room_ready(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.leave_room)
    def leave_room(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.game_put_operation)
    def game_put_operation(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.game_confirm_new_round)
    def game_confirm_new_round(self, *args, **kwargs):
        pass

    @_mirror(MahjongSoulClient.return_from_game)
    def return_from_game(self, *args, **kwargs):
        pass

