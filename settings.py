import os

cookie_secret = os.getenv("COOKIE_SECRET", "SECRET")

control_queue_name = "control"
votes_queue_name = "votes"

rabbit_host = os.getenv("RABBIT_HOST", "localhost")
rabbit_user = os.getenv("RABBIT_USER", "guest")
rabbit_pass = os.getenv("RABBIT_PASS", "guest")
rabbit_vhost = os.getenv("RABBIT_VHOST", "/")
