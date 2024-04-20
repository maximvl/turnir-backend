from dataclasses import dataclass
from multiprocessing import Process, Queue, Event
from queue import Empty
import time

from .websocket_client import start_websocket_client
from .types import WorkerState


class Worker:
    process: Process
    queue: Queue
    state: WorkerState
    id: str
    started_at: int

    def __init__(self, id: str, websocket_token: str) -> None:
        self.id = id
        self.started_at = int(time.time())
        self.queue = Queue()
        self.state = WorkerState(self.queue, stop_flag=Event(), websocket_token=websocket_token)
        self.process = Process(target=start_websocket_client, args=(self.state,))

    def start(self) -> None:
        self.process.start()

    def stop(self) -> None:
        self.state.stop_flag.set()

    def hard_stop(self) -> None:
        self.process.terminate()
        time.sleep(0.5)
        self.process.close()

    def get_last_message(self):
        last_message = None
        try:
            while True:
                last_message = self.queue.get_nowait()
        except Empty:
            pass
        return last_message
