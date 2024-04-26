import asyncio
import signal
import logging
from quart import Quart, request, session, send_from_directory

from turnir_app import settings
from turnir_app.poll_manager import get_manager
from turnir_app.websocket_controller import get_controller


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


app = Quart(__name__)
app.secret_key = settings.cookie_secret
poll_manager = get_manager()
ws_controller = get_controller()


@app.route("/turnir")
async def static_index():
    return await send_from_directory("../turnir/build", "index.html")


@app.route("/turnir/static/<path:path>")
async def static_js(path):
    return await send_from_directory("../turnir/build/static/", path)


@app.route("/turnir-api/votes", methods=["GET"])
async def get_votes():
    ws_controller.start()
    session_key = "pid"
    state_id = session.get(session_key)
    if not state_id:
        state_id = poll_manager.get_random_id()
        session[session_key] = state_id

    poll = poll_manager.get(state_id)
    if not poll:
        return {"poll_votes": None}
    return {"poll_votes": poll.votes}


@app.route("/turnir-api/votes/reset", methods=["POST"])
async def votes_reset():
    ws_controller.start()
    body = await request.get_json()
    vote_options = body.get("vote_options")

    session_key = "pid"
    state_id = session.get(session_key)
    if not state_id:
        state_id = poll_manager.get_random_id()
        session[session_key] = state_id

    poll_manager.create(key=state_id, options=vote_options)
    return {"status": "ok"}


def shutdown(trigger: asyncio.Event):
    logger.info("Cancelling tasks")
    trigger.set()
    tasks = asyncio.all_tasks()
    [task.cancel() for task in tasks]
    logger.info("Shutdown")


async def main():
    trigger = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, shutdown, trigger)
    loop.add_signal_handler(signal.SIGINT, shutdown, trigger)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(app.run_task(shutdown_trigger=trigger.wait))
        tg.create_task(ws_controller.wait_to_start())


def start():
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    start()
