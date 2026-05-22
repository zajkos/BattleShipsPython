# Propozycje Nowych Funkcjonalności - BattleShipsPython

Ten dokument zawiera listę planowanych oraz potencjalnych ulepszeń dla gry Statki.

## 1. Rozgrywka i Mechanika (Gameplay)
*   [X] **"Trafiony - Zatopiony!" (Rozpoznawanie zniszczenia całego statku):**
    *   *Opis:* Serwer sprawdza, czy wszystkie segmenty danego statku zostały trafione. Jeśli tak, odtwarzany jest specjalny dźwięk, a wrak statku zostaje odkryty/obrysowany na planszy przeciwnika.
*   [X] **Limit czasu na turę (Timer):**
    *   *Opis:* Dodanie paska postępu lub odliczania (np. 30 sekund). Po upływie czasu tura automatycznie przechodzi na przeciwnika lub oddawany jest losowy strzał.
*   [X] **System Rewanżu (Rematch):**
    *   *Opis:* Po zakończeniu gry, na ekranie wynikowym dostępny jest przycisk "Rewanż". Jeśli obaj gracze go klikną, gra wraca do fazy rozstawiania bez wychodzenia do menu.

## 2. Interfejs Użytkownika i UX
*   [X] **Wbudowany Czat Tekstowy:**
    *   *Opis:* Okienko czatu podczas bitwy i oczekiwania, pozwalające na komunikację między graczami. (Klawisz 'T')
*   [X] **Menu Pauzy (In-Game Menu):**
    *   *Opis:* Overlay pod klawiszem ESC z opcjami: Kontynuuj, Opcje, Poddaj się.
*   [X] **Wizualny Celownik:**
    *   *Opis:* Animowany celownik zamiast prostej obwódki podczas wybierania pola do strzału.
*   [X] **Konfigurowalne Animacje:**
    *   *Opis:* Możliwość niezależnego włączenia/wyłączenia wybuchów, dymu oraz plusku w opcjach gry. (Domyślnie dym wyłączony).
*   [X] **Limit FPS:**
    *   *Opis:* Możliwość ustawienia limitu klatek na sekundę (30, 60, 120, 144, 240, 360) w menu opcji.
*   [X] **Rewanż po Poddaniu:**
    *   *Opis:* Naprawiono logikę poddawania się – gracz który się poddaje, nie jest już wyrzucany do menu, lecz trafia na ekran końca gry, gdzie może zaproponować rewanż.

## 3. Sieć i Serwer
*   [X] **Kary za ucieczkę:**
    *   *Opis:* Automatyczne przyznanie zwycięstwa graczowi, który pozostał w grze po rozłączeniu się przeciwnika. Zapis walkowera do bazy danych.
*   [X] **Separacja Matchmakingu:**
    *   *Opis:* Gwarancja, że gracze z "Szybkiej gry" nie trafią do prywatnych pokojów z kodem. (Wprowadzono flagę `is_private`).

## 4. Inne
*   [ ] **Tryb Singleplayer (AI):**
    *   *Opis:* Możliwość gry przeciwko komputerowi z algorytmem szukania i dobijania statków.
