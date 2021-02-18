import socket
import threading
import config

class Client:
    def __init__(self, ip, port=57801):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.connect((ip, port))

        print(f"user id: {self._server_socket.getsockname()[1]}")

        self.start()

    def start(self):
        try:
            self._input_thread = threading.Thread(target=self.handle_inputs)
            self._broadcast_thread = threading.Thread(target=self.handle_broadcasts)
            self._input_thread.start()
            self._broadcast_thread.start()
        except Exception as e:
            print(e)

    def handle_inputs(self):
        while True:
            msg = input()
            self._server_socket.send(msg.encode("utf-8"))

    def handle_broadcasts(self):
        while True:
            data = self._server_socket.recv(1024).decode()
            if data:
                if data.startswith(str(self._server_socket.getsockname()[1])) is False:
                    print(data)


if __name__ == "__main__":
    ip = config.cfg()
    client = Client(ip)
