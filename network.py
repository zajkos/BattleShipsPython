import socket
import json
import struct
import os
import ssl
from dotenv import load_dotenv

# Wczytujemy zmienne z pliku .env, jeśli on istnieje
load_dotenv()

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = os.getenv("SERVER_HOST", "127.0.0.1")
        self.port = int(os.getenv("SERVER_PORT", 5555))
        self.addr = (self.server, self.port)
        self._buffer = bytearray()
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            # Odbieramy powitanie przy użyciu nowego protokołu
            response = self.recv(blocking=True)
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
            return self.recv(blocking=True)
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

    def flush(self):
        """Czyści bufor i ignoruje zaległe pakiety ('duchy') ze starej gry z gniazda TCP."""
        self._buffer.clear()
        self.client.setblocking(False)
        try:
            while True:
                data = self.client.recv(4096)
                if not data:
                    break
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Błąd podczas opróżniania gniazda: {e}")

    def recv(self, blocking=False):
        """Odbiera wiadomość z użyciem bufora."""
        try:
            if blocking:
                self.client.settimeout(5.0) # Zabezpieczenie przed nieskończonym zamrożeniem gry
                self.client.setblocking(True)
            
            while True:
                # Sprawdzenie czy w buforze jest już cała wiadomość
                if len(self._buffer) >= 4:
                    msg_len = struct.unpack('>I', self._buffer[:4])[0]
                    if len(self._buffer) >= 4 + msg_len:
                        break  # Mamy pełną wiadomość, przerywamy wczytywanie

                try:
                    chunk = self.client.recv(4096)
                    if not chunk: 
                        break
                    self._buffer.extend(chunk)
                except BlockingIOError:
                    break # W trybie nieblokującym przerywamy czytanie, gdy nie ma danych
                except socket.timeout:
                    break # Przerwanie po 5 sekundach oczekiwania
                    
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Błąd recv: {e}")
            return None
        finally:
            if blocking:
                self.client.settimeout(None) # Przywrócenie domyślnego stanu

        if len(self._buffer) >= 4:
            msg_len = struct.unpack('>I', self._buffer[:4])[0]
            if len(self._buffer) >= 4 + msg_len:
                msg_data = self._buffer[4:4+msg_len]
                self._buffer = self._buffer[4+msg_len:]
                try:
                    return json.loads(msg_data.decode('utf-8'))
                except json.JSONDecodeError:
                    return None
        return None
