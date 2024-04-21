from dataclasses import dataclass, field
from multiprocessing import Queue, synchronize
from time import time


@dataclass
class WorkerState:
    votes_queue: Queue
    control_queue: Queue
    websocket_token: str
    stop_flag: synchronize.Event
    vote_options: list[str]
    votes: dict[int, int] = field(default_factory=dict)
    voters: set[int] = field(default_factory=set)
    last_update_at: int = int(time())


@dataclass
class ResetCommand:
    options: list[str]


class StopCommand:
    pass
