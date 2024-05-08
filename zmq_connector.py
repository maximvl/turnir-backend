import zmq
import settings


class ZmqConnection:
    context: zmq.Context
    socket: zmq.Socket

    def __init__(self) -> None:
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.IPV6, 1)
        self.socket.connect(settings.zeromq_address)

    def close(self) -> None:
        self.socket.close()
        self.context.term()

    def get_messages(self, client_id: str, ts_from: int) -> list[dict]:
        self.socket.send_json({"command": "get_messages", "client_id": client_id, "ts_from": ts_from})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return received.get("messages") # pyright: ignore
        raise Exception(f"Error while getting messages: {received}")

    def reset_client(self, client_id: str) -> None:
        self.socket.send_json({"command": "reset_client", "client_id": client_id})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return
        raise Exception(f"Error while resetting client: {received}")

    def clear_storage(self) -> None:
        self.socket.send_json({"command": "clear_storage"})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return
        raise Exception(f"Error while clearing storage: {received}")

    def ping(self) -> None:
        self.socket.send_json({"command": "ping"})
        received = self.socket.recv_json()
        if isinstance(received, dict) and received.get("status") == "ok":
            return
        raise Exception(f"Error while pinging: {received}")
