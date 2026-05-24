import socket
import json
import struct

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
            # Odbieramy powitanie przy użyciu nowego protokołu
            response = self.recv()
            if response:
                print(f"Serwer: {response.get('message')}")
            else:
                print("Błąd: Serwer nie wysłał powitania.")
        except Exception as e:
            print(f"Błąd połączenia: {e}")

    def send(self, data):
        """Wysyła dane z prefiksem długości i czeka na odpowiedź."""
        try:
            msg = json.dumps(data).encode('utf-8')
            header = struct.pack('>I', len(msg))
            self.client.sendall(header + msg)
            return self.recv()
        except Exception as e:
            print(f"Błąd send: {e}")
            return None

    def send_no_wait(self, data):
        """Wysyła dane bez blokowania na odpowiedź."""
        try:
            msg = json.dumps(data).encode('utf-8')
            header = struct.pack('>I', len(msg))
            self.client.sendall(header + msg)
        except Exception as e:
            print(f"Błąd send_no_wait: {e}")

    def recv(self):
        """Odbiera wiadomość zgodnie z protokołem Length-Prefixing."""
        try:
            header = self.client.recv(4)
            if not header: return None
            msg_len = struct.unpack('>I', header)[0]
            
            chunks = []
            bytes_recd = 0
            while bytes_recd < msg_len:
                chunk = self.client.recv(min(msg_len - bytes_recd, 4096))
                if not chunk: return None
                chunks.append(chunk)
                bytes_recd += len(chunk)
            
            return json.loads(b"".join(chunks).decode('utf-8'))
        except BlockingIOError:
            return None
        except Exception as e:
            print(f"Błąd recv: {e}")
            return None
