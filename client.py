import socket
import threading
import config
import sys
import json
import random
import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic

class Client(QtWidgets.QMainWindow):
    def __init__(self, ip, username, port=57801):
        super().__init__()
        uic.loadUi("ui/chatroom.ui", self)

        self._username = username
        self._users_connected = []
        self._username_check_done = False
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.connect((ip, port))

        self.send_button.clicked.connect(self.handle_input)

        self.set_username(username)

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
            data = self._server_socket.recv(1024).decode()
            print(data)
            if data:
                if data.startswith("USL"):
                    data = data[3:]
                    data = json.loads(data)

                    self._users_connected = data
                    if self._username_check_done is False:
                        self.check_username()
                        self._username_check_done = True

                    self.user_list.clear()
                    for username in data:
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
            username = " ".join(msg.split(" ")[1:]) # joins everything after the first space together
            self.set_username(username=username)
        else:
            msg = "MSG" + msg

        self._server_socket.send(msg.encode("utf-8"))

    def set_username(self, username=None):
        username = username.replace(':', '').lower()

        discrim = str(random.randint(1000,9999))
        self._username = username + "#" + discrim

        _set_username = "USN" + self._username
        self._server_socket.send(_set_username.encode("utf-8"))

    def check_username(self):
        while True:
            if self._users_connected.count(self._username) > 1:
                discrim = str(random.randint(1000,9999))
                self._username = self._username[:-4] + discrim
                self.set_username(username=self._username)
            else:
                return

    def closeEvent(self, event):
        os._exit()

class InputUsername(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/username.ui", self)
        self.ok_button.clicked.connect(self.save_username)
        self.show()

    def save_username(self):
        self.window = Client(config.cfg(), self.username_box.text())
        self.window.show()
        self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = InputUsername()
    app.exec_()
