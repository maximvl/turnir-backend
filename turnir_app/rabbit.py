from typing import Generator
import pika
import settings
import json


def get_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=settings.control_queue_name)
    channel.queue_declare(queue=settings.votes_queue_name)
    return channel


def read_all_messages(connection) -> Generator[bytes, None, None]:
    while True:
        method_frame, header_frame, body = connection.basic_get(queue=settings.votes_queue_name, auto_ack=True)
        print("method_frame", method_frame)
        print("header_frame", header_frame)
        print("body", body)
        if method_frame and isinstance(body, bytes):
            yield json.loads(body)
        else:
            break

def ping_chat_reader(connection):
    connection.basic_publish(
        exchange="",
        routing_key=settings.control_queue_name,
        body=b"ping",
    )


def clear_vote_messages(connection):
    connection.purge_queue(queue=settings.votes_queue_name)
