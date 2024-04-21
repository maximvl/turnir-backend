import os

lasqa_channel = "channel-chat:8845069"
roadhouse_channel = "channel-chat:6367818"

vk_channel = os.getenv("VK_CHANNEL", lasqa_channel)
allow_duplicate_votes = os.getenv("ALLOW_DUPLICATE_VOTES", "false") == "true"

votes_update_interval_seconds = int(os.getenv("VOTES_UPDATE_INTERVAL_SECONDS", "3"))
cookie_secret = os.getenv("COOKIE_SECRET", "SECRET")
