# network.py
import socket
import json

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"
        self.port = 5555
        self.addr = (self.server, self.port)
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            # Odbieramy pierwszą wiadomość powitalną od serwera
            print(self.client.recv(2048).decode())
        except socket.error as e:
            print(f"Błąd połączenia: {e}")

    def send(self, data):
        try:
            # Wysyłamy dane w formacie JSON
            self.client.send(str.encode(json.dumps(data)))
            # Czekamy na odpowiedź serwera
            response = self.client.recv(2048).decode()
            return json.loads(response)
        except socket.error as e:
            print(e)
            return None

    def send_no_wait(self, data):
        """Wysyła dane bez oczekiwania na odpowiedź (dla akcji asynchronicznych)."""
        try:
            self.client.sendall(str.encode(json.dumps(data)))
        except socket.error as e:
            print(f"Błąd wysyłania: {e}")