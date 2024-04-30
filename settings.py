import os

cookie_secret = os.getenv("COOKIE_SECRET", "SECRET")

control_queue_name = "control"
votes_queue_name = "votes"

rpc_address = os.getenv("RPC_ADDRESS", "tcp://0.0.0.0:4242")
