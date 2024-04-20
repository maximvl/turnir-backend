from flask import Flask, session
from multiprocessing import Process, Queue
from queue import Empty
import os
import base64
import time

from turnir_app.worker_pool import WorkerPool

app = Flask(__name__)

app.secret_key = 'SECRET'

worker_pool = WorkerPool(workers_limit=30)

@app.route('/turnir-api/votes')
def get_votes():
    session_key = 'pid'
    worker_id = session.get(session_key) or worker_pool.get_random_id()
    session[session_key] = worker_id
    worker = worker_pool.get_or_create_worker(session[session_key])
    message = worker.get_last_message()
    return {"poll_votes": message}

@app.route('/turnir-api/reset')
def reset():
    workers = worker_pool.reset()
    return "ok"

@app.route('/turnir-api/status')
def status():
    return worker_pool.get_status()
