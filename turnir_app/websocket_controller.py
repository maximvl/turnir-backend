import asyncio
import time
import logging

from turnir_app.websocket_client import start_websocket_client

logger = logging.getLogger()


class WSController:
    activate_event: asyncio.Event
    last_activation_at: int
    deactivation_time_seconds = 20

    def __init__(self):
        self.activate_event = asyncio.Event()
        self.last_activation_at = int(time.time())

    def start(self):
        self.activate_event.set()
        self.last_activation_at = int(time.time())

    async def wait_to_start(self):
        logger.info("Starting websocket controller")
        while True:
            if not self.activate_event.is_set():
                logger.info("Waiting for activation")
            await self.activate_event.wait()
            try:
                await start_websocket_client(self.should_deactivate)
            except Exception:
                pass
            if self.should_deactivate():
                logger.info("Deactivating websocket client")
                self.activate_event.clear()

    def should_deactivate(self):
        return int(time.time()) - self.last_activation_at > self.deactivation_time_seconds


controller = WSController()


def get_controller():
    return controller
