from dataclasses import dataclass, field
from multiprocessing import Queue, synchronize
from time import time


@dataclass
class WorkerState:
    queue: Queue
    websocket_token: str
    stop_flag: synchronize.Event
    reset_flag: synchronize.Event
    votes: dict[int, int] = field(default_factory=dict)
    voters: set[int] = field(default_factory=set)
    last_update_at: int = int(time())
