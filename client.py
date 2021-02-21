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
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.connect((ip, port))

        self.message_box.returnPressed.connect(self.handle_input)
        self.send_button.clicked.connect(self.handle_input)

        username_to_send = "USN" + self._username
        self._server_socket.send(username_to_send.encode("utf-8"))

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
                print("data in:", data)
                if data.startswith("USL"):  # username list
                    data = data[3:]
                    data = json.loads(data)

                    self.user_list.clear()
                    for username in data:
                        list_item = QtWidgets.QListWidgetItem(username)
                        self.user_list.addItem(list_item)
                elif data.startswith("USN"):    # username change
                    self._username = data[3:]
                elif data.startswith("MSG"):
                    data = data[3:]
                    if data.startswith(f"{self._username}:"):
                        data = data.replace(f"{self._username}:", "You:", 1)
                    list_item = QtWidgets.QListWidgetItem(data)
                    self.message_list.addItem(list_item)

    def handle_input(self):
        msg = self.message_box.text()
        self.message_box.setText("")

        if msg.startswith("/username"):
            self._username = " ".join(msg.split(" ")[1:])   # joins everything after the first space together
            self._server_socket.send(self._username.encode("utf-8"))
        else:
            msg = "MSG" + msg
            self._server_socket.send(msg.encode("utf-8"))

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
