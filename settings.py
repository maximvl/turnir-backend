import os

cookie_secret = os.getenv("COOKIE_SECRET", "SECRET")

control_queue_name = "control"
votes_queue_name = "votes"

zeromq_address = os.getenv("ZMQ_ADDRESS", "tcp://127.0.0.1:4242")
