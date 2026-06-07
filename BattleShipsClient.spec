# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('audio', 'audio'), ('dołącz do pokoju.png', '.'), ('Gra Statki.png', '.'), ('graj.png', '.'), ('kontynuuj.png', '.'), ('logo.png', '.'), ('logo2.png', '.'), ('logowanie duże.png', '.'), ('losuj.png', '.'), ('opcje.png', '.'), ('plansza.png', '.'), ('plansza1os.png', '.'), ('plusk.png', '.'), ('plusk2.png', '.'), ('powrot do menu.png', '.'), ('powrót.png', '.'), ('RWEANŻ.png', '.'), ('S T A R T.png', '.'), ('ship_1.png', '.'), ('ship_2.png', '.'), ('ship_3.png', '.'), ('ship_4.png', '.'), ('smoke.png', '.'), ('stwórz pokój.png', '.'), ('szybka gra.png', '.'), ('top wyniki.png', '.'), ('tworcy.png', '.'), ('unnamed.png', '.'), ('wybuch.png', '.'), ('wyczyść.png', '.'), ('wyjście.png', '.'), ('zaloguj.png', '.'), ('zarejestruj.png', '.'), ('beachday.otf', '.'), ('beachday.ttf', '.'), ('.env', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BattleShipsClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
