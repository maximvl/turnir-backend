import os
import base64
from typing import Optional

from turnir_app import settings


class Poll:
    votes: dict[str, int]
    voters: set[int]
    channel: str
    last_access_at: int = 0

    def __init__(self, options: list[str], channel: str) -> None:
        self.voters = set()
        self.votes = {option: 0 for option in options}
        self.channel = channel

    def vote(self, voter: int, option: int):
        if str(option) not in self.votes:
            return

        is_duplicate = voter in self.voters
        if is_duplicate and not settings.allow_duplicate_votes:
            print("already voted", voter, option)
            return

        print("counting vote", voter, option)
        self.votes[str(option)] += 1
        self.voters.add(voter)


class PollsManager:
    polls: dict[str, Poll]

    def __init__(self):
        self.polls = {}

    def create(self, key: str, options: list[str]) -> Poll:
        channel = settings.vk_channel
        poll = Poll(options=options, channel=channel)
        self.polls[key] = poll
        return poll

    def get(self, key: str) -> Optional[Poll]:
        return self.polls.get(key)

    def get_random_id(self) -> str:
        return base64.urlsafe_b64encode(os.urandom(6)).decode()

    def get_all_for_channel(self, channel: str) -> list[Poll]:
        return [poll for poll in self.polls.values() if poll.channel == channel]


manager = PollsManager()


def get_manager():
    return manager
