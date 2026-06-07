
import os
import glob
import PyInstaller.__main__

def build_client():
    added_files = [('audio', 'audio')]
    
    # Dodajemy wszystkie pliki PNG, OTF, TTF z głównego katalogu
    for ext in ['*.png', '*.otf', '*.ttf', '.env']:
        for f in glob.glob(ext):
            if os.path.isfile(f):
                added_files.append((f, '.'))

    # Konfiguracja argumentów dla PyInstallera
    args = [
        'main.py',
        '--onefile',
        '--noconsole',
        '--name=BattleShipsClient',
    ]

    for src, dest in added_files:
        args.append(f'--add-data={src};{dest}')

    print(f"Budowanie KLIENTA z argumentami: {args}")
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    build_client()
