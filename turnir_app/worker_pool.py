import time
from datetime import datetime
from typing import Optional
import os
import base64
from turnir_app.worker import Worker

class TooManyWorkersException(Exception):
    pass


class WorkerPool:
    workers_map: dict[str, Worker] = {}
    all_workers: list[Worker] = []
    workers_limit: int

    def __init__(self, workers_limit: int = 10):
        self.workers_limit = workers_limit

    def create_worker(self, worker_id: str) -> Worker:
        if len(self.workers_map) >= self.workers_limit:
            raise TooManyWorkersException("Workers limit exceeded")
        worker = Worker(id=worker_id)
        self.workers_map[worker_id] = worker
        self.all_workers.append(worker)
        worker.start()
        return worker

    def get_or_create_worker(self, worker_id: str) -> Worker:
        worker = self.workers_map.get(worker_id)
        if worker and worker.process.is_alive():
            return worker
        worker = self.create_worker(worker_id)
        return worker

    def get_random_id(self) -> str:
        return base64.urlsafe_b64encode(os.urandom(6)).decode()

    def reset(self) -> None:
        for worker in self.workers_map.values():
            worker.stop()
        self.workers_map = {}

    def get_status(self) -> list[dict]:
        return [
            {
                "alive": worker.process.is_alive(),
                "pid": worker.process.pid,
                "id": worker.id,
                "started_at": datetime.fromtimestamp(worker.started_at).isoformat(),
            }
            for worker in self.all_workers
        ]
