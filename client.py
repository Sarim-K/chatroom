import socket
import threading
import sys
import json
import random
import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic

class Chatroom(QtWidgets.QMainWindow):
    def __init__(self, ip, username, port=57801):
        super().__init__()
        uic.loadUi("ui/chatroom.ui", self)

        self._username = username + "#" + str(random.randint(1000,9999))
        self._users_connected = []
        self._username_check_count = 0
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.connect((ip, port))

        self.message_box.returnPressed.connect(self.handle_input)
        self.send_button.clicked.connect(self.handle_input)
        self.check_and_send_username()

        self.show()
        self.start()

    def start(self):
        try:
            self._broadcast_thread = threading.Thread(target=self.handle_broadcasts)
            self._broadcast_thread.start()
        except Exception as e:
            print(e)

    def handle_broadcasts(self):
        while True:
            data = self._server_socket.recv(4096).decode()
            if data:
                if data.startswith("USL"):
                    data = data[3:]
                    data = json.loads(data)

                    self._users_connected = data    # used to see if username is valid in self.check_and_send_username()
                    if self._username_check_count != 2:     # 2 bc on the 1st run the username list is not in memory yet, so the check [1/5]
                        self.check_and_send_username()      # only works after 1st run. we only want it to run once (not for every new user) [2/5]
                                                            # otherwise both conflicting users will have their names changed, not just the new user [3/5]
                    self.user_list.clear()                  # as the new user will be running it on its second run whereas the already existing user [4/5]
                    for username in data:                   # would be on their 3rd (or more) run of the method [5/5]
                        list_item = QtWidgets.QListWidgetItem(username)
                        self.user_list.addItem(list_item)
                else:
                    if data.startswith(f"{self._username}:"):
                        data = data.replace(f"{self._username}:", "You:", 1)
                    list_item = QtWidgets.QListWidgetItem(data)
                    self.message_list.addItem(list_item)

    def handle_input(self):
        msg = self.message_box.text()
        self.message_box.setText("")

        if msg.startswith("/username"):
            self._username = " ".join(msg.split(" ")[1:])   # joins everything after the first space together
            self.check_and_send_username()
        else:
            msg = "MSG" + msg
            self._server_socket.send(msg.encode("utf-8"))

    # method loops until username is valid then increments flag & sends username to server
    def check_and_send_username(self):
        self._username = self._username.replace(':', '').lower()
        while True:
            if self._users_connected.count(self._username) > 1:
                discrim = str(random.randint(1000,9999))
                self._username = self._username[:-4] + discrim
            else:
                _send_username = "USN" + self._username
                self._server_socket.send(_send_username.encode("utf-8"))
                self._username_check_count += 1
                return

    def closeEvent(self, event):
        os._exit(1)

class Home(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/username.ui", self)
        self.ok_button.clicked.connect(self.open_room)

        try:
            with open("resources/cache.txt", "r") as f:
                ip, username = f.readline(), f.readline()
                if ip:
                    self.ip_box.setText(ip)
                if username:
                    self.username_box.setText(username)
        except FileNotFoundError:
            if not os.path.exists("resources"):    # creates directory
                os.makedirs("resources")
            open("resources/cache.txt", "w+").close()    # creates file

        self.show()

    def open_room(self):
        ip, username = self.ip_box.text(), self.username_box.text()
        with open("resources/cache.txt", "w") as f:
            f.write(ip + "\n")
            f.write(username)

        self.window = Chatroom(self.ip_box.text(), self.username_box.text())
        self.window.show()
        self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Home()
    app.exec_()
