import os

cookie_secret = os.getenv("COOKIE_SECRET", "SECRET")

control_queue_name = "control"
votes_queue_name = "votes"

rabbit_host = os.getenv("RABBIT_HOST", "localhost")
