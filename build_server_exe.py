
import os
import PyInstaller.__main__

def build_server():
    # Serwer potrzebuje głównie pliku .env, jeśli tam trzymasz poświadczenia bazy
    added_files = []
    if os.path.exists('.env'):
        added_files.append(('.env', '.'))

    # Konfiguracja argumentów dla PyInstallera
    args = [
        'server.py',
        '--onefile',
        # Serwer zazwyczaj chcemy widzieć w konsoli (logi)
        '--console',
        '--name=BattleShipsServer',
    ]

    for src, dest in added_files:
        args.append(f'--add-data={src};{dest}')

    print(f"Budowanie SERWERA z argumentami: {args}")
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    build_server()
