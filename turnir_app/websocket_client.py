import asyncio
import signal
from typing import Optional
import requests
from bs4 import BeautifulSoup
import websockets
import json
from dataclasses import dataclass

from websockets import WebSocketClientProtocol, Data
from turnir_app import poll_manager, settings


websocket_url = (
    "wss://pubsub.live.vkplay.ru/connection/websocket?cf_protocol_version=v2"
)

manager = poll_manager.get_manager()


@dataclass
class VoteResponse:
    option_id: int
    voter_id: int
    channel: str


async def start_websocket_client():
    print("Starting websocket client")
    token = get_websocket_token()
    async with websockets.connect(
        websocket_url,
        extra_headers={"Origin": "https://live.vkplay.ru"},
    ) as websocket:
        # close websocket on SIGTERM
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, loop.create_task, websocket.close())

        await send_initial_messages(websocket, token=token)
        async for message in websocket:
            await handle_message(websocket, message)

    print("Websocket client stopped")


async def handle_message(ws: WebSocketClientProtocol, json_message: Data):
    response = await on_message(ws, json_message)
    if response:
        polls = manager.get_all_for_channel(response.channel)
        for poll in polls:
            poll.vote(response.voter_id, response.option_id)


async def on_message(
    ws: WebSocketClientProtocol, json_message: Data
) -> Optional[VoteResponse]:
    # print(f" <- {json_message}")
    if json_message == "{}":
        await ws.send("{}")
        return None

    message = json.loads(json_message)
    message_data = None
    author_id = None
    channel = None

    pub_data = message.get("push", {}).get("pub", {}).get("data", {})
    if pub_data.get("type") != "message":
        return None

    author_id = pub_data.get("data", {}).get("author", {}).get("id")
    if not author_id:
        return None

    channel = message.get("push", {}).get("channel")
    if not channel:
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

    return VoteResponse(option_id, author_id, channel)


async def send_initial_messages(ws: websockets.WebSocketClientProtocol, token: str):
    print("Subscribing to", settings.vk_channel)

    initial_message = json.dumps(
        {
            "connect": {
                "token": token,
                "name": "js",
            },
            "id": 1,
        }
    )
    await ws.send(initial_message)

    subscribe_message = json.dumps(
        {
            "subscribe": {"channel": settings.vk_channel},
            "id": 2,
        }
    )
    await ws.send(subscribe_message)


def get_websocket_token() -> str:
    response = requests.get("https://live.vkplay.ru")
    parsed = BeautifulSoup(response.text, "html.parser")
    parsed_config = json.loads(parsed.body.script.text)
    return parsed_config["websocket"]["token"]
