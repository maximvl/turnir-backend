import asyncio
from quart import Quart, request, session, send_from_directory

from turnir_app import settings
from turnir_app.poll_manager import get_manager
from turnir_app.websocket_client import start_websocket_client


app = Quart(__name__)
app.secret_key = settings.cookie_secret
poll_manager = get_manager()


@app.route("/turnir")
async def static_index():
    return await send_from_directory("../turnir/build", "index.html")


@app.route("/turnir/static/<path:path>")
async def static_js(path):
    return await send_from_directory("../turnir/build/static/", path)


@app.route("/turnir-api/votes", methods=["GET"])
async def get_votes():
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
    body = await request.get_json()
    vote_options = body.get("vote_options")

    session_key = "pid"
    state_id = session.get(session_key)
    if not state_id:
        state_id = poll_manager.get_random_id()
        session[session_key] = state_id

    poll_manager.create(key=state_id, options=vote_options)
    return {"status": "ok"}


# @app.route("/turnir-api/reset")
# async def reset():
#     worker_pool.reset()
#     return "ok"


# @app.route("/turnir-api/status")
# async def status():
#     return worker_pool.get_status()


async def main():
    await asyncio.gather(start_websocket_client(), app.run_task(debug=True))


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(start_websocket_client())
