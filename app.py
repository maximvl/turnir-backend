from flask import Flask, send_from_directory
import settings
from turnir_app import rabbit

app = Flask(__name__)

app.secret_key = settings.cookie_secret


@app.route("/turnir")
def static_index():
    return send_from_directory("../turnir/build", "index.html")


@app.route("/turnir/static/<path:path>")
def static_js(path):
    return send_from_directory("../turnir/build/static/", path)


@app.route("/turnir-api/votes", methods=["GET"])
def get_votes():
    connection = rabbit.get_connection()
    rabbit.ping_chat_reader(connection)
    messages = list(rabbit.read_all_messages(connection))
    return {"poll_votes": messages}


@app.route("/turnir-api/votes/reset", methods=["POST"])
def votes_reset():
    connection = rabbit.get_connection()
    rabbit.clear_vote_messages(connection)
    return {"status": "ok"}
