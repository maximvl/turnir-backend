from flask import Flask, request, send_from_directory, session
import settings
import os
import base64
import zmq
from db_connector import Preset, db, init_db, save_preset, serialize_preset
from zmq_connector import ZmqConnection
import json
from datetime import datetime


app = Flask(__name__)
app.secret_key = settings.cookie_secret
init_db(app)


@app.route("/turnir")
def static_index():
    return send_from_directory("../turnir/build", "index.html")


@app.route("/turnir/static/<path:path>")
def static_js(path):
    return send_from_directory("../turnir/build/static/", path)


def get_random_id() -> str:
    return base64.urlsafe_b64encode(os.urandom(6)).decode()


def get_client_id() -> str:
    client_id_key = "client_id"
    if not client_id_key in session:
        client_id = get_random_id()
        session[client_id_key] = client_id
    else:
        client_id = session[client_id_key]
    return client_id


@app.route("/turnir-api/votes", methods=["GET"])
def get_votes():
    client_id = get_client_id()
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
    client_id = get_client_id()
    connection = ZmqConnection()
    connection.reset_client(client_id)
    connection.close()
    return {"status": "ok"}


@app.route("/turnir-api/presets/", methods=["POST"])
def create_preset():
    client_id = get_client_id()
    preset_id = get_random_id()

    data = request.json
    if not isinstance(data, dict):
        return {"error": "Data should be a json"}

    preset = Preset(
        id=preset_id,
        title=data.get("title", ""),
        owner_id=client_id,
        options=json.dumps(data["options"]),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ) # pyright: ignore
    save_preset(preset)
    return serialize_preset(preset)


@app.route("/turnir-api/presets/<id>", methods=["GET"])
def get_preset(id: str):
    preset = Preset.query.get_or_404(id)
    return serialize_preset(preset)


@app.route("/turnir-api/presets/<id>", methods=["POST"])
def update_preset(id: str):
    client_id = get_client_id()

    data = request.json
    if not isinstance(data, dict):
        return {"error": "Data should be a json"}

    preset = Preset.query.get_or_404(id)
    if preset.owner_id != client_id:
        return {"error": "You are not the owner of the preset"}

    if "title" in data:
        preset.title = data.get("title")
        preset.updated_at = datetime.utcnow()
    if "options" in data:
        preset.options = json.dumps(data.get("options"))
        preset.updated_at = datetime.utcnow()

    db.session.commit()
    return serialize_preset(preset)


@app.route("/turnir-api/ping", methods=["GET"])
def ping():
    connection = ZmqConnection()
    connection.ping()
    connection.close()
    return {"status": "ok"}
