from flask import Flask, send_from_directory, session, request
from turnir_app.worker import Worker
from turnir_app.worker_pool import WorkerPool

app = Flask(__name__)

app.secret_key = "SECRET"

worker_pool = WorkerPool(workers_limit=30)


@app.route("/turnir")
def static_index():
    return send_from_directory("../turnir/build", "index.html")


@app.route("/turnir/static/<path:path>")
def static_js(path):
    return send_from_directory("../turnir/build/static/", path)


def get_worker() -> Worker:
    session_key = "pid"
    worker_id = session.get(session_key)
    if not worker_id:
        worker_id = worker_pool.get_random_id()
        session[session_key] = worker_id
    return worker_pool.get_or_create_worker(worker_id)


@app.route("/turnir-api/votes", methods=["GET"])
def get_votes():
    worker = get_worker()
    message = worker.get_last_message()
    return {"poll_votes": message}


@app.route("/turnir-api/votes/reset", methods=["POST"])
def votes_reset():
    body = request.get_json()
    vote_options = body.get("vote_options")
    worker = get_worker()
    worker.reset_voting(vote_options)
    return {"status": "ok"}


@app.route("/turnir-api/reset")
def reset():
    worker_pool.reset()
    return "ok"


@app.route("/turnir-api/status")
def status():
    return worker_pool.get_status()
