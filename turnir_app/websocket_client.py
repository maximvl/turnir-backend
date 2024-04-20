import time
from typing import Optional
import websocket
import json
from dataclasses import dataclass

from turnir_app.types import WorkerState


websocket_url = (
    "wss://pubsub.live.vkplay.ru/connection/websocket?cf_protocol_version=v2"
)
update_interval_seconds = 3


@dataclass
class VoteResponse:
    option_id: int
    voter_id: int


def start_websocket_client(state: WorkerState):
    def handle_message(ws, json_message):
        if state.stop_flag.is_set():
            print("Stopping...")
            ws.close()
            return

        if state.reset_flag.is_set():
            print("Resetting...")
            state.votes.clear()
            state.voters.clear()
            state.reset_flag.clear()

        response = on_message(ws, json_message)
        if response:
            handle_vote_response(state, response)

    def on_open(ws):
        send_initial_messages(state, ws)

    print("Starting websocket client")
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=handle_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
        header={"Origin": "https://live.vkplay.ru"},
    )
    ws.run_forever(
        reconnect=5,
        skip_utf8_validation=True,
    )
    print("Websocket client stopped")


def handle_vote_response(state: WorkerState, response: VoteResponse) -> None:
    if response.voter_id in state.voters:
        return

    if response.option_id not in state.votes:
        state.votes[response.option_id] = 0
    state.votes[response.option_id] += 1
    state.voters.add(response.voter_id)

    now = int(time.time())
    if (now - state.last_update_at) > update_interval_seconds:
        state.last_update_at = now
        state.queue.put(state.votes.copy())


def on_message(ws, json_message) -> Optional[VoteResponse]:
    # print(f" -> {json_message}")
    if json_message == b"{}":
        ws.send("{}")
        return None

    message = json.loads(json_message)
    message_data = None
    author_id = None

    pub_data = message.get("push", {}).get("pub", {}).get("data", {})
    if pub_data.get("type") != "message":
        return None

    message_data = pub_data.get("data", {}).get("data", [])
    print("Message data")
    print(message_data)
    text_items = [
        d.get("content")
        for d in message_data
        if d.get("type") == "text" and d.get("content")
    ]

    if not text_items:
        return None

    item = json.loads(text_items[0])
    try:
        option_id = int(item[0])
    except Exception:
        return None

    author_id = pub_data.get("data", {}).get("author", {}).get("id")
    if not author_id:
        return None

    return VoteResponse(option_id, author_id)


def on_error(ws, error):
    print("*** WS Error ***")
    print(error)
    print("*** WS Error ***")


def on_close(ws, status_code, msg):
    print("*** WS Closed ***")
    print(status_code)
    print(msg)
    print("*** WS Closed ***")


def send_initial_messages(state, ws):
    initial_message = json.dumps(
        {
            "connect": {
                "token": state.websocket_token,
                "name": "js",
            },
            "id": 1,
        }
    )
    ws.send(initial_message)

    subscribe_message = json.dumps(
        {
            "subscribe": {"channel": "channel-chat:8845069"},
            "id": 2,
        }
    )
    ws.send(subscribe_message)
