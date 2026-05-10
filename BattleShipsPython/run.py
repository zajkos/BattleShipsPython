import subprocess
import time
import sys

def run_game():
    print("[1/3] Uruchamianie serwera...")
    # Używamy sys.executable, aby użyć dokładnie tego samego Pythona, w którym odpalamy skrypt
    server_process = subprocess.Popen([sys.executable, "server.py"])

    print("[2/3] Oczekiwanie 3 sekundy na start serwera...")
    time.sleep(3)

    print("[3/3] Uruchamianie dwóch klientów...")
    client1_process = subprocess.Popen([sys.executable, "main.py"])
    client2_process = subprocess.Popen([sys.executable, "main.py"])

    print("\n--- WSZYSTKO URUCHOMIONE ---")
    print("Naciśnij Ctrl+C w tym oknie, aby zabić wszystkie procesy naraz.")

    try:
        # Skrypt będzie wisiał tutaj i czekał, aż wyłączysz serwer
        server_process.wait()
    except KeyboardInterrupt:
        print("\nZamykanie wszystkich procesów...")
        server_process.terminate()
        client1_process.terminate()
        client2_process.terminate()

if __name__ == "__main__":
    run_game()