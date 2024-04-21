from flask import Flask, session
from turnir_app.worker_pool import WorkerPool

app = Flask(__name__)

app.secret_key = "SECRET"

worker_pool = WorkerPool(workers_limit=30)


@app.route("/turnir-api/votes")
def get_votes():
    session_key = "pid"
    worker_id = session.get(session_key)
    if not worker_id:
        worker_id = worker_pool.get_random_id()
        session[session_key] = worker_id
    worker = worker_pool.get_or_create_worker(worker_id)
    message = worker.get_last_message()
    return {"poll_votes": message}


@app.route("/turnir-api/votes/reset")
def votes_reset():
    session_key = "pid"
    worker_id = session.get(session_key)
    if not worker_id:
        worker_id = worker_pool.get_random_id()
        session[session_key] = worker_id
    worker = worker_pool.get_or_create_worker(worker_id)
    worker.reset_voting()
    return {"status": "ok"}


@app.route("/turnir-api/reset")
def reset():
    worker_pool.reset()
    return "ok"


@app.route("/turnir-api/status")
def status():
    return worker_pool.get_status()
