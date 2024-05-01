from flask import Flask, request, send_from_directory, session
import settings
import os
import base64
import zmq


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


class ZmqConnection:
    context: zmq.Context
    socket: zmq.Socket

    def __init__(self) -> None:
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(settings.zeromq_address)

    def close(self) -> None:
        self.socket.close()
        self.context.term()

    def get_messages(self, client_id: str, ts_from: int) -> list[dict]:
        self.socket.send_json({"command": "get_messages", "client_id": client_id, "ts_from": ts_from})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return received.get("messages")
        raise Exception(f"Error while getting messages: {received}")

    def reset_client(self, client_id: str) -> None:
        self.socket.send_json({"command": "reset_reader", "client_id": client_id})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return
        raise Exception(f"Error while resetting client: {received}")

    def clear_storage(self) -> None:
        self.socket.send_json({"command": "clear_storage"})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return
        raise Exception(f"Error while clearing storage: {received}")

    def ping(self) -> None:
        self.socket.send_json({"command": "ping"})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return
        raise Exception(f"Error while pinging: {received}")


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

    connection = ZmqConnection()
    messages = connection.get_messages(client_id, ts_from)
    connection.close()
    return {"poll_votes": messages}


@app.route("/turnir-api/votes/reset", methods=["POST"])
def votes_reset():
    if not client_id_key in session:
        client_id = get_random_id()
        session[client_id_key] = client_id
    else:
        client_id = session[client_id_key]

    connection = ZmqConnection()
    connection.reset_client(client_id)
    connection.close()
    return {"status": "ok"}


@app.route("/turnir-api/ping", methods=["GET"])
def ping():
    connection = ZmqConnection()
    connection.ping()
    connection.close()
    return {"status": "ok"}
