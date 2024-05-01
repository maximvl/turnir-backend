from flask import Flask, request, send_from_directory, session
import zerorpc
import settings
import os
import base64

app = Flask(__name__)

app.secret_key = settings.cookie_secret


@app.route("/turnir")
def static_index():
    return send_from_directory("../turnir/build", "index.html")


@app.route("/turnir/static/<path:path>")
def static_js(path):
    return send_from_directory("../turnir/build/static/", path)


def get_random_id() -> str:
    return base64.urlsafe_b64encode(os.urandom(6)).decode()

def get_rpc_connection():
    client = zerorpc.Client()
    client.connect(settings.rpc_address)
    return client


client_id_key = "client_id"


@app.route("/turnir-api/votes", methods=["GET"])
def get_votes():
    if not client_id_key in session:
        client_id = get_random_id()
        session[client_id_key] = client_id
    else:
        client_id = session[client_id_key]

    ts_from = request.args.get("ts")
    if not ts_from:
        return {"error": "ts is required"}

    try:
        ts_from = int(ts_from)
    except Exception:
        return {"error": "ts should be a number"}

    rpc = get_rpc_connection()
    messages = rpc.get_messages(client_id, ts_from)
    rpc.close()
    return {"poll_votes": messages}


@app.route("/turnir-api/votes/reset", methods=["POST"])
def votes_reset():
    if not client_id_key in session:
        client_id = get_random_id()
        session[client_id_key] = client_id
    else:
        client_id = session[client_id_key]

    rpc = get_rpc_connection()
    rpc.reset_reader(client_id)
    rpc.close()
    return {"status": "ok"}


@app.route("/turnir-api/ping", methods=["GET"])
def ping():
    rpc = get_rpc_connection()
    rpc.ping()
    rpc.close()
    return {"status": "ok"}
