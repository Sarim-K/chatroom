import socket
import threading
import sys
import json
import random
import os
from resources import breeze_resources
from PyQt5 import QtCore, QtGui, QtWidgets, uic

class Chatroom(QtWidgets.QMainWindow):
    def __init__(self, ip, username, port=57801):
        super().__init__()
        uic.loadUi("ui/chatroom.ui", self)

        self._username = username
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.connect((ip, port))

        self.message_box.returnPressed.connect(self.handle_input)
        self.send_button.clicked.connect(self.handle_input)

        username_to_send = self.add_tags("USN", self._username)
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
                if data[:5] == "<USL>" and data[-6:] == "</USL>":  # username list
                    data = json.loads(data[5:-6]) #string to list
                    self.user_list.clear()
                    for username in data:
                        if username == self._username:
                            username += " (You)"
                        self.add_to_list(self.user_list, username)

                elif data[:5] == "<USN>" and data[-6:] == "</USN>":    # username change
                    self._username = data[5:-6]

                elif data[:5] == "<MSG>" and data[-6:] == "</MSG>":
                    data = data[5:-6]
                    if data.startswith(f"{self._username}:"):
                        data = data.replace(f"{self._username}:", "You:", 1)
                    self.add_to_list(self.message_list, data)

    def handle_input(self):
        msg = self.message_box.text()
        self.message_box.setText("")

        if msg.startswith("/username"):
            self._username = " ".join(msg.split(" ")[1:])   # joins everything after the first space together
            username_to_send = self.add_tags("USN", self._username)
            self._server_socket.send(username_to_send.encode("utf-8"))
        else:
            msg = self.add_tags("MSG", msg)
            self._server_socket.send(msg.encode("utf-8"))

    def add_to_list(self, list_object, data):
        list_item = QtWidgets.QListWidgetItem(data)
        list_object.addItem(list_item)

    def add_tags(self, tag, data):
        return f"<{tag}>{data}</{tag}>"

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
                    self.ip_box.setText(ip.strip())
                if username:
                    self.username_box.setText(username.strip())
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

    file = QtCore.QFile(":/dark.qss")
    file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
    stream = QtCore.QTextStream(file)
    app.setStyleSheet(stream.readAll())

    window = Home()
    app.exec_()
