import socket
import threading
import config
import time
import json

class Server:
    def __init__(self, ip, port=57801, listeners=5):
        self._server_socket = socket.socket()
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # avoids annoying error on restarts
        self._server_socket.bind((ip, port))
        self._server_socket.listen(listeners)

        self._threads = {}      # stores the threads (Thread) & their keys ({sockname}_client_thread)
        self._connections = {}  # stores the connections (conn) & their keys (sockname)
        self._usernames = {}    # stores the usernames & their keys (sockname)

        self.start()

    def start(self):
        try:
            self._threads["connection_handling_thread"] = threading.Thread(target=self.handle_connections)
            self._threads["user_list_thread"] = threading.Thread(target=self.broadcast_user_list)
            self._threads["connection_handling_thread"].start()
            self._threads["user_list_thread"].start()
        except Exception as e:
            print(e)

    def handle_connections(self):
        conn, addr = self._server_socket.accept()
        self._connections[addr[1]] = conn

        # creates & starts thread for new connection
        self._threads[f"{addr[1]}_client_thread"] = threading.Thread(target=self.listen_to_connection, args=(conn, addr))
        self._threads[f"{addr[1]}_client_thread"].start()

        print(list(self._threads.keys()))   # print current thread names

        self.handle_connections()

    def broadcast_user_list(self):
        while True:
            try:
                data = "USL" + str(json.dumps(list(self._usernames.values())))
                self.broadcast_message(data)
                time.sleep(0.25)
            except Exception as e:
                pass

    def listen_to_connection(self, conn, addr):
        while True:
            try:
                data = conn.recv(1024).decode()
                if data:
                    if data[:3] == "USN":   # username list
                        data = data[3:]
                        self._usernames[addr[1]] = data
                    elif data[:3] == "MSG": # message
                        data = data[3:]
                        self.broadcast_message(f"{self._usernames[addr[1]]}: {data}")    # sends data back to all clients

            except ConnectionResetError:                        # client has disconnected, we don't need to deal with them anymore;
                del self._connections[addr[1]]                  # throw conn & thread out of dictionaries and break the loop so the
                del self._threads[f"{addr[1]}_client_thread"]   # server will stop processing it.
                self.broadcast_message(f"Server: {self._usernames[addr[1]]} has disconnected.")
                del self._usernames[addr[1]]
                break

    def broadcast_message(self, data):
        data = data.encode("utf-8")
        print("broadcasting", data)
        for conn in self._connections.values():
            conn.send(data)

if __name__ == "__main__":
    ip = config.cfg()
    server = Server(ip)
