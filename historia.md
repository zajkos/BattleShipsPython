# Historia Projektu - BattleShipsPython

## [2026-05-20] Inicjalizacja Nowego Etapu Prac
- **Ustalenie Zasad**: Wprowadzono plik `zasady.md` określający workflow (kopie zapasowe, komunikacja, logowanie zmian).
- **Analiza Projektu**: Przeprowadzono wstępny przegląd struktury plików (Pygame, PostgreSQL, architektura Klient-Serwer).
- **Rola**: Przyjęto rolę eksperta Python Game Dev do dalszego rozwoju gry multiplayer 2D.

## [2026-05-20] Implementacja KAN-49 - Ekran Top Wyników
- **Serwer (`server.py`)**:
    - Dodano obsługę akcji `get_high_scores` z agregacją SQL (Best Score, Wins, Losses, Avg Points).
    - Zaimplementowano logikę końca gry (18 trafień) oraz automatyczne zapisywanie wyników do tabel `matches` i `scores`.
    - Rozszerzono strukturę pokoju o `user_id` graczy dla potrzeb bazy danych.
- **Klient (`high_scores.py`)**:
    - Stworzono nowy moduł UI z listą Top 100.
    - Zaimplementowano scrollowanie (mysz/strzałki) oraz wizualne wyróżnienie Top 3, 10, 50, 100.
    - Dodano obsługę klawisza ESC i przycisku powrotu.
- **Komunikacja (`network.py`)**:
    - Zwiększono bufor odbioru danych do 16KB dla obsłużenia dużej listy wyników.
- **Gameplay (`game.py`)**:
    - Dodano obsługę statusu `game_over` oraz ekran końcowy z wynikiem i przyciskiem powrotu do menu.
- **Menu Główne (`main.py`)**:
    - Podpięto przycisk "Top Wyniki" pod nowy ekran rankingowy.

## [2026-05-20] Optymalizacja UI i Dodanie Sortowania (High Scores)
- **UI (`high_scores.py`)**:
    - Zmniejszono czcionki i zoptymalizowano odstępy między wierszami/kolumnami, aby zapobiec nachodzeniu tekstu.
    - Wprowadzono skracanie zbyt długich nicków (ellipsis).
    - Zaimplementowano dynamiczne sortowanie po wszystkich kolumnach (Pozycja, Gracz, Wynik, Wygrane, Przegrane, Średnia) po kliknięciu w nagłówek.
    - Dodano wizualne wskaźniki kierunku sortowania (strzałki ▲/▼) oraz podświetlanie aktywnej kolumny.
    - Poprawiono płynność przewijania (zwiększono krok scrollowania).
    - Dodano instrukcję obsługi w dolnej części ekranu.
- **Korekta Layoutu (`high_scores.py`)**:
    - Przesunięto kolumnę "Najlepszy Wynik" o 10px w lewo, aby ikony sortowania nie nachodziły na sąsiednie nagłówki.
    - Zmniejszono szerokość kolumny "Poz" i "Gracz" dla lepszego balansu tabeli.
    - Potwierdzono działanie mechanizmu ucinania nicków (`...`) dla zachowania integralności tabeli.

## [2026-05-21] Ekstremalna Optymalizacja Wydajności (FPS Drop Fix)
- **Problem**: Gra na słabszych sprzętach spadała poniżej 10 FPS, a na mocnych nie potrafiła utrzymać zablokowanych 60 klatek.
- **Diagnoza i Profilowanie**: Zidentyfikowano setki zbędnych operacji I/O, alokacji pamięci oraz renderowania wektorowego wykonywanych co klatkę (wewnątrz pętli `while True:`).
- **Zastosowane Rozwiązania**:
    - **Globalny Cache Klasy Button**: Zmodyfikowano plik `button.py` – tekst przycisków tekstowych jest teraz renderowany (`font.render()`) tylko raz podczas wywołania `__init__`, eliminując renderowanie go co klatkę wewnątrz metody `draw()`.
    - **Cache Siatki Gry**: W `game.py` wprowadzono technikę zapamiętywania tekstury siatki (`draw_grid()`). Tworzenie liter od A do J i liczb, a także rysowanie 22 linii, odbywa się tylko za pierwszym razem i jest zachowywane w globalnym buforze `_grid_cache`.
    - **Eksterminacja Alokacji Overlay'ów**: Z głównych pętli `game.py`, `high_scores.py` przeniesiono tworzenie wielkich powierzchni typu `pygame.Surface((1920, 1080))` powyżej pętli. Eliminacja "garbage creation" rzędu 500 MB/s.
    - **Pre-renderowanie Tekstu**: Całkowicie wyczyszczono z pętli zdarzeń wszystkie wywołania `.render()` w plikach: `auth_screen.py` (napis LOGOWANIE, Login, Hasło), `options.py` (nagłówki opcji), `credits.py` (wszystkie nazwiska), `high_scores.py` (nagłówki tabel i podpowiedzi), `game.py` (podpowiedzi, pytania o nick i kody pokoi).
