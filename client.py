import socket
import threading
import config

class Client:
    def __init__(self, ip, port=57801):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.connect((ip, port))

        print(f"user id: {self._server_socket.getsockname()[1]}")
        self.set_username()
        print("--------------------------")
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
            msg = str(input())

            if msg.startswith("/username"):
                username = " ".join(msg.split(" ")[1:]) # joins everything after the first space together
                self.set_username(username=username)
                continue
            else:
                msg = "MSG" + msg

            self._server_socket.send(msg.encode("utf-8"))

    def handle_broadcasts(self):
        while True:
            data = self._server_socket.recv(1024).decode()
            if data:
                if data.startswith(f"{self._username}:") is False:
                    print(data)

    def set_username(self, username=None):
        if not username:
            username = str(input("pick a username: "))

        self._username = username.lower()
        _set_username = "USN" + self._username
        self._server_socket.send(_set_username.encode("utf-8"))

if __name__ == "__main__":
    ip = config.cfg()
    client = Client(ip)
