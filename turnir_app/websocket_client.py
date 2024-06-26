import time
from typing import Optional
import websocket
import json
from dataclasses import dataclass

from turnir_app import settings
from turnir_app.types import ResetCommand, StopCommand, WorkerState


websocket_url = (
    "wss://pubsub.live.vkplay.ru/connection/websocket?cf_protocol_version=v2"
)


@dataclass
class VoteResponse:
    option_id: int
    voter_id: int


def start_websocket_client(state: WorkerState):
    def handle_message(ws, json_message):
        command = None
        try:
            command = state.control_queue.get_nowait()
        except Exception:
            pass
        match command:
            case StopCommand():
                print("Stopping...")
                ws.close()
                return
            case ResetCommand():
                print("Resetting", command)
                state.votes.clear()
                state.votes.update({option: 0 for option in command.options})
                state.voters.clear()
            case None:
                pass
            case _:
                print("Unsupported command", command)

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
    if str(response.option_id) not in state.votes:
        print("ignoring", response)
        return

    is_duplicate = response.voter_id in state.voters

    if is_duplicate and not settings.allow_duplicate_votes:
        print("already voted", response)
        return

    print("counting", response)
    state.votes[str(response.option_id)] += 1
    state.voters.add(response.voter_id)

    now = int(time.time())
    if (now - state.last_update_at) > settings.votes_update_interval_seconds:
        state.last_update_at = now
        state.votes_queue.put(state.votes.copy())


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
    # print("Message data")
    # print(message_data)
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


    print("Subscribing to", settings.vk_channel)

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
            "subscribe": {"channel": settings.vk_channel},
            "id": 2,
        }
    )
    ws.send(subscribe_message)
