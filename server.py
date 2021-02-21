import socket
import threading
import json
import requests

class Server:
    def __init__(self, ip, port=57801, listeners=5):
        self._server_socket = socket.socket()
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # avoids annoying error on restarts
        self._server_socket.bind((ip, port))
        self._server_socket.listen(listeners)

        self._threads = {}      # stores the threads (Thread) & their keys ({sockname}_client_thread)
        self._connections = {}  # stores the connections ([conn, username]) & their keys (sockname)

        self.start()

    def start(self):
        try:
            self._threads["connection_handling_thread"] = threading.Thread(target=self.handle_connections)
            self._threads["connection_handling_thread"].start()
        except Exception as e:
            print(e)

    def handle_connections(self):
        conn, addr = self._server_socket.accept()
        self._connections[addr[1]] = [conn, None]

        # creates & starts thread for new connection
        self._threads[f"{addr[1]}_client_thread"] = threading.Thread(target=self.listen_to_connection, args=(conn, addr))
        self._threads[f"{addr[1]}_client_thread"].start()

        # print(list(self._threads.keys()))   # print current thread names

        self.handle_connections()

    def broadcast_user_list(self):
        try:
            data = "USL" + str(json.dumps(self.usernames))
            self.broadcast_message(data)
        except Exception as e:
            print(e)

    def listen_to_connection(self, conn, addr):
        while True:
            try:
                data = conn.recv(4096).decode()
                if data:
                    if data[:3] == "USN":   # username change
                        data = data[3:]
                        username = self.check_username(data)
                        self._connections[addr[1]][1] = username    # set username
                        self.send_data_to_client(conn, f"USN{username}")    # send validated username back to the client
                        self.broadcast_user_list()
                    elif data[:3] == "MSG": # message
                        data = data[3:]
                        self.broadcast_message(f"MSG{self._connections[addr[1]][1]}: {data}")    # sends data back to all clients

            except ConnectionResetError:
                username_cache = self._connections[addr[1]][1]
                del self._connections[addr[1]]                  # client has disconnected, we don't need to deal with them anymore;
                del self._threads[f"{addr[1]}_client_thread"]   # throw conn & thread out of dictionaries and break the loop so the
                self.broadcast_message(f"MSGServer: {username_cache} has disconnected.")             # server will stop processing it.
                self.broadcast_user_list()
                break

    def send_data_to_client(self, conn, data):
        conn.send(data.encode("utf-8"))

    def broadcast_message(self, data):
        data = data.encode("utf-8")
        print("broadcasting", data)
        for conn in self._connections.values():
            conn[0].send(data)

    def check_username(self, username):
        username = username.replace(':', '').lower()
        while True:
            if self.usernames.count(username) > 1:
                username = username[:-4] + str(random.randint(1000,9999))
            else:
                return username

    @property
    def usernames(self):
        usernames = []
        for user in self._connections.values():
            usernames.append(user[1])
        return usernames

if __name__ == "__main__":
    ip = requests.get('https://checkip.amazonaws.com').text.strip()
    server = Server(ip)
