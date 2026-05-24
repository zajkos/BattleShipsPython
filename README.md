# BattleShips - Pełna Specyfikacja Techniczna i Architektoniczna (GDD & TDD)

## 1. High-Level Overview & System Identity

### 1.1 Metryczka Projektu
| Parametr | Specyfikacja Techniczna |
| :--- | :--- |
| **Tytuł Projektu** | BattleShips |
| **Gatunek** | Tactical Grid-Based Strategy |
| **Model Sieciowy** | Authoritative Client-Server with SSL/TLS |
| **System Operacyjny** | Windows (Windows Server / Windows 10+) |
| **Główny Stack** | Python 3.10+, Pygame 2.x, PostgreSQL 14+ |
| **Format Komunikacji** | Length-Prefixed JSON over Secure Sockets (SSL/TLS) |
| **Struktura Zadaniowa** | Jira (Epiki: Data Management, Audio & VFX, GUI & UX, Core Logic) |

### 1.2 Stack Technologiczny i Zależności
System opiera się na lekkim, wysokowydajnym stosie technologicznym, minimalizującym narzut systemowy (low-overhead).

*   **Język Programowania**: Python 3.10.12 (lub nowszy). Wykorzystanie typowania (Type Hinting) dla zwiększenia stabilności kodu.
*   **Silnik Renderujący**: `pygame` 2.5.0+. Wykorzystanie modułów: `display`, `draw`, `image`, `mixer`, `font`, `time`.
*   **Komunikacja Sieciowa**: Natywna biblioteka `socket` owinięta w moduł `ssl` (implementacja TLS 1.3). Wykorzystanie protokołu **Length-Prefixing** (4-bajtowy nagłówek binarny) dla stabilnej obsługi fragmentacji TCP.
*   **Zarządzanie Danymi**:
    *   `psycopg2.pool`: Implementacja Connection Pooling (`SimpleConnectionPool`) dla wysokiej wydajności przy wielu graczach.
    *   `python-dotenv`: Separacja wrażliwych danych konfiguracyjnych (poświadczenia DB).
*   **Kryptografia & Security**: `bcrypt` (adaptacyjny algorytm haszowania haseł z soleniem).
*   **Serializacja**: Biblioteka `json` (standard RFC 8259).

### 1.3 Wymagania Środowiskowe i Prerekwizyty
*   **Klient**:
    *   Procesor: 2-rdzeniowy (obsługa wątku renderowania i wątku sieciowego).
    *   Pamięć RAM: ~256MB (VRAM/RAM).
    *   Ekran: Natywna rozdzielczość 1920x1080 (FullHD) z wykorzystaniem `pygame.SCALED`. Implementacja wykorzystuje flagę `pygame.FULLSCREEN | pygame.SCALED`.
    *   Łącze: Stabilne połączenie TCP, latency < 250ms dla płynnego UI.
*   **Audio (Podsystem)**: Moduł `audio_manager.py` implementuje system **Randomized SFX Categories** (KAN-9). System losuje pliki (np. `hit1-8.mp3`), co zapobiega monotonii dźwiękowej.
*   **Serwer**:
    *   Środowisko: Windows (Windows Server / Windows 10+).
    *   Database: Dostęp do instancji PostgreSQL z możliwością zapisu logów meczowych.
    *   Przepustowość: Skalowalna liczba wątków (1 per client + turn timer thread).

### 1.4 Cele Wydajnościowe (KPI)
*   **Frame Consistency**: Dynamiczne FPS (zgodne z `options.current_fps`, domyślnie 360) dzięki technikom cache'owania `_grid_cache` oraz pre-renderowania arkuszy animacji (`load_spritesheet`). Jitter klatek nie może przekraczać 5%.
*   **Network Latency Compensation**: Klient musi pozostawać responsywny (asynchroniczny polling `net_buffer`) podczas oczekiwania na dane.
*   **DB Performance**: Zapytania rankingowe (Top 100) wykonywane w czasie < 50ms dzięki indeksowaniu `points DESC`.

### 1.5 Bezpieczeństwo i Integralność
*   **Trust Model**: Obecna wersja serwera stosuje model **Semi-Authoritative**. Serwer w pełni kontroluje i autoryzuje strzały (`shoot`) oraz punktację, zapobiegając nielegalnym strzałom w to samo miejsce lub poza turą.
*   **Placement Validation (Ograniczenie)**: Serwer przyjmuje gotowy układ floty od klienta (`player_ready`).
*   **Auth Validation (KAN-70)**: 
    *   Weryfikacja unikatowości nicku (KAN-73).
    *   Weryfikacja siły hasła (KAN-72): Minimum 8 znaków, co najmniej jedna mała litera, jedna duża litera, jedna cyfra oraz jeden znak specjalny.
    *   Pola tekstowe (`InputBox`) akceptują wyłącznie znaki alfanumeryczne (`isalnum()`) dla loginów.
*   **Credential Protection**: Hasła są haszowane przed zapisem przy użyciu `bcrypt`. Pliki `.env` are wykluczone z repozytorium.
*   **Anti-Cheat**: Logika rozstrzygania trafień odbywa się wyłącznie w pamięci RAM serwera. Klient nie posiada informacji o pozycjach statków przeciwnika do momentu ich trafienia/zatopienia.

### 1.6 Maszyna Stanów Gry (Game State Machine)
Cykl życia sesji jest ściśle zdefiniowany, co pozwala na walidację pakietów JSON po stronie serwera.

| Stan | Opis | Dozwolone Akcje |
| :--- | :--- | :--- |
| **AUTH** | Ekran logowania/rejestracji. | `login`, `register` |
| **LOBBY** | Menu główne, przeglądanie rankingu. | `get_high_scores`, `random_match`, `create_room` |
| **MATCHMAKING** | Oczekiwanie na przeciwnika w pokoju. | `join_room`, `disconnect` |
| **PLACEMENT** | Rozstawianie własnej floty na planszy. | `player_ready` |
| **BATTLE** | Aktywna wymiana ognia, tury. | `shoot`, `chat_message`, `surrender` |
| **ENDGAME** | Ekran wyników, propozycja rewanżu. | `request_rematch`, `return_to_menu` |

---

## 2. Architektura Plików i Modułów (System Breakdown)

### 2.1 Klient (Frontend - Pygame Layer)

#### `main.py` - Orchestrator & Entry Point
*   **Inicjalizacja**: Uruchomienie `pygame.init()`, `init_audio()`, oraz ustawienie trybu wideo `FULLSCREEN | SCALED` przy bazowej rozdzielczości 1920x1080.
*   **Asset Preloading**: Wywołanie `preload_assets()` przed wejściem do pętli menu. Funkcja ta wymusza inicjalizację obiektów `Ship` (budowa cache obrazów) oraz wycina klatki animacji z arkuszy (spritesheets).
*   **Główna Pętla Menu**: Obsługuje nawigację między `show_auth_screen()`, `main_menu()`, oraz wywołania podmodułów `high_scores`, `options`, `credits`.
*   **Interakcja Sieciowa**: Tworzy globalną instancję `Network()`, która jest przekazywana do wszystkich ekranów wymagających komunikacji z serwerem.

#### `game.py` - Core Gameplay Controller
Jest to najbardziej rozbudowany moduł, zarządzający cyklem życia bitwy.
*   **Faza Matchmakingu (`matchmaking_menu`, `waiting_screen`)**:
    *   Ustawia socket in tryb `setblocking(False)` dla płynnego renderowania UI podczas oczekiwania.
    *   `waiting_screen` implementuje polling bufora sieciowego w każdej klatce.
*   **Faza Rozstawiania (`play_game`)**:
    *   Zarządza listą `placed_ships`.
    *   Implementuje logikę Drag & Drop oraz rotację (R / PPM).
    *   `is_valid_placement()`: Funkcja walidująca pozycję statku względem granic i sąsiedztwa innych jednostek.
*   **Faza Bitwy (`battle_phase`)**:
    *   **Zarządzanie Turą**: Lokalna zmienna `current_turn` synchronizowana komunikatami `shot_result` i `turn_timeout`.
    *   **System Animacji**: Zarządza listą `active_animations` (krótkotrwałe np. wybuchy) i `persistent_effects` (np. dym na uszkodzonych polach).
    *   **Input Handling**: Wykrywanie kliknięć na siatce przeciwnika i wysyłka `shoot(x, y)`.
*   **Ekran Zwycięstwa (KAN-46)**: Wyświetlanie wyników końcowych, nicków obu graczy oraz ich punktacji (KAN-48).
*   **Komunikacja Asynchroniczna**: System wykorzystuje protokół **Length-Prefixing** (4-bajtowy nagłówek binarny). Każdy pakiet jest odbierany w całości na podstawie zadeklarowanej długości, co eliminuje problemy z fragmentacją TCP i zapewnia pełną integralność obiektów JSON bez konieczności skanowania bufora tekstowego.
*   **Czat In-Game**: Obsługa bufora tekstowego `chat_input`, limitowanie długości wiadomości (30 znaków) i wyświetlanie logu `chat_log`.

#### `ship.py` - Ship Entity & Rendering
*   **Klasa `Ship`**: Enkapsuluje stan fizyczny okrętu.
*   **Image Cache**: Statyczny słownik `_image_cache` przechowuje załadowane obrazy bazowe. Zapobiega wielokrotnemu odczytowi z dysku przy tworzeniu nowej floty.
*   **Skalowanie Dynamiczne**: Metody `update_to_grid_size` i `update_to_tray_size` wykonują `pygame.transform.scale()` tylko gdy aktualna skala nie odpowiada docelowej, co drastycznie redukuje zużycie CPU podczas rozstawiania.

#### `network.py` - Communication Bridge
*   **Klasa `Network`**: Wraper na natywne sockety TCP.
*   **Metoda `send(data)`**: Blokująca wysyłka JSON. Czeka na odpowiedź (używana głównie przy logowaniu i rankingach).
*   **Metoda `send_no_wait(data)`**: Asynchroniczna wysyłka `sendall()`, używana w krytycznych fazach bitwy, aby nie blokować renderowania klatek.

#### `high_scores.py` - Data Visualization (KAN-49)
*   **Pobieranie Danych**: Wysyła akcję `get_high_scores`, odbiera listę 100 rekordów (KAN-50).
*   **Tabela UI**: Implementuje autorski system renderowania tabelarycznego z obsługą ucinania długich nicków (`...`) (KAN-51).
*   **Sortowanie**: Funkcja `get_sorted_data()` wykorzystuje wbudowaną funkcję `sorted()` z kluczem dynamicznym (lambda), co zapewnia stabilne sortowanie (Timsort) po stronie klienta.

#### `credits.py` - Ekran Twórców
*   **Logika**: Pętla z przewijającym się tekstem (credits loop). Pre-renderowanie linii tekstu zapobiega dropom FPS.

#### `auth_screen.py` & `button.py`
*   **`auth_screen.py` (KAN-70)**: Zarządza ekranem logowania/rejestracji. Wykorzystuje `InputBox` do przechwytywania znaków Unicode. Implementuje walidację danych (KAN-71, 72, 73).
*   **`button.py`**:
    *   `Button`: Przycisk tekstowy. Tekst jest renderowany do Surface raz w `__init__` lub przy zmianie treści (Property Setter).
    *   `ImageButton`: Przycisk graficzny. Wczytuje PNG, usuwa przezroczyste marginesy (bounding rect) i generuje jaśniejszą wersję dla efektu `hover`.

### 2.2 Serwer (Backend - Authoritative Logic)

#### `server.py` - Master Server Controller
*   **Zarządzanie Połączeniami**: `socket.listen()` przyjmuje nowe połączenia, zabezpiecza je warstwą SSL i deleguje do wątków.
*   **Threaded Architecture**:
    *   **Wątek Klienta**: Obsługuje bezpieczną pętlę `recv()`.
    *   **Async Turn Watchdog**: Wątek Turn Timer monitoruje czas bez blokowania globalnego stanu, co zapobiega zatorom przy wielu graczach.
*   **Matchmaking & Rooms**:
    *   Pokoje wykorzystują **Match Epoch** do synchronizacji stanu.
*   **Persistence Layer**: 
    *   Wykorzystanie `SimpleConnectionPool` do zarządzania zasobami PostgreSQL.
    *   **Ranking Cache**: Top 100 wyników utrzymywane w RAM i odświeżane co 5 minut.
*   **Disconnects & Reconnects**: System implementuje 15-sekundowe okno na powrót gracza (Reconnect Window). W tym czasie stan gry jest wstrzymany.
*   **Security**: Weryfikacja haseł `bcrypt.checkpw()` odbywa się wyłącznie na serwerze. Klient nigdy nie otrzymuje haszy haseł.

### 2.3 Struktura Repozytorium (Repository Tree)
Fizyczny układ plików w projekcie:

```text
BattleShipsPython/
├── audio/               # Efekty dźwiękowe (.mp3, .wav)
├── .venv/               # Środowisko wirtualne Pythona
├── .env                 # Plik konfiguracyjny (DB credentials)
├── audio_manager.py     # Zarządzanie warstwą audio (mixer)
├── auth_screen.py       # Interfejs logowania/rejestracji
├── button.py            # Wspólne klasy przycisków
├── game.py              # Główna logika gry i bitwy
├── main.py              # Punkt wejścia (Menu Główne)
├── network.py           # Komunikacja sieciowa klienta
├── server.py            # Logika serwera i bazy danych
├── ship.py              # Klasa statku i renderowanie floty
├── high_scores.py       # Moduł rankingu Top 100
├── settings.py          # Stałe systemowe i konfiguracja kolorów
├── bazaSqlKomenda.txt   # Skrypt DDL dla PostgreSQL
├── Dokumentacja_GDD_TDD.md # Niniejsza dokumentacja
└── *.png                # Zasoby graficzne (statki, tła, UI)
```

---

## 3. Szczegółowe Mechaniki i Algorytmy

### 3.1 Algorytm Walidacji Rozstawiania (Collision & Boundary)
Algorytm gwarantuje integralność pola bitwy przed wysłaniem danych do serwera. Wykorzystuje on koncepcję **Sąsiedztwa Moore'a** o promieniu 1.

1.  **Grid Constraint**: Dla każdego segmentu statku $S_i = (x_i, y_i)$, musi zachodzić $0 \le x_i < 10 \land 0 \le y_i < 10$.
2.  **Overlap & Proximity Check**: System iteruje po każdej komórce nowego statku i sprawdza obszar wokół niej. Jeśli jakakolwiek komórka w tym obszarze należy do już postawionego statku, pozycja jest odrzucana. Gwarantuje to obowiązkowy 1-polowy odstęp między jednostkami.

### 3.2 Autorytatywna Logika Trafień (Hit/Sunk Logic)
Serwer przetwarza akcję `shoot(x, y)` w następujących krokach:
1.  **Turn Validation**: Sprawdzenie czy $Sender\_ID == Current\_Turn\_Player\_ID$.
2.  **Duplicate Shot Check**: Weryfikacja czy $(x, y) \notin Hits \cup Misses$ dla danej planszy.
3.  **Collision Resolution**:
    - Iteracja po obiektach statków przeciwnika.
    - Jeśli trafienie: Dodanie $(x, y)$ do zbioru trafień gracza.
    - **Sunk Detection**: Statek jest zatopiony, jeśli $|Ship_{cells} \cap Player_{hits}| = |Ship_{cells}|$.
4.  **Response Generation**: Rozesłanie `shot_result` do obu graczy. Payload zawiera flagi `hit`, `sunk` oraz listę `sunk_cells` (do wizualizacji wraku).

### 3.3 System Punktacji (Scoring Formula - KAN-20, 21)
Punkty są naliczane dynamicznie w celu promowania agresywnej i precyzyjnej gry.
*   **Podstawowe trafienie**: $+50$ pkt.
*   **Pudło (Penalty)**: $-10$ pkt.
*   **Premia za zatopienie ($P_{sunk}$)**: Zależna od klasy jednostki. Premia jest **całkowitą wartością punktową za dany strzał** (zastępuje standardowe 50 pkt):
    - 4-masztowiec: $500$ pkt.
    - 3-masztowiec: $400$ pkt.
    - 2-masztowiec: $200$ pkt.
    - 1-masztowiec: $100$ pkt.
*   **Kara za stratę ($P_{loss}$)**: Gdy gracz traci własny statek, odejmowane jest $50\%$ wartości premii za zatopienie danej klasy (np. $-250$ pkt za stratę 4-masztowca).

### 3.4 Zarządzanie Czasem (Turn Timer & Synchronization)
Zaimplementowany jako **Server-Side Watchdog Thread** z wizualizacją po stronie klienta.
*   **Server Watchdog**: Funkcja `turn_timer_thread()` w `server.py` iteruje co sekundę po wszystkich pokojach. Jeśli gracz nie wykona akcji w ciągu 35 sekund (`time.time() - last_action_time > 35`), serwer wysyła komunikat `turn_timeout`.
*   **Client Visualization (KAN-22)**: Klient oblicza `time_left` jako $max(0, 30 - (CurrentTime - TurnStartTime))$ na potrzeby renderowania paska postępu. Zmiana logiczna następuje po otrzymaniu pakietu `turn_timeout`.

### 3.5 Efekty Wizualne i Screenshake (VFX Logic - KAN-9)
Efekty są projektowane tak, by nie blokować głównego wątku renderowania.
*   **Screenshake**: Przy trafieniu, zmienna `shake_amount` (np. 10px) ulega wygaszaniu liniowemu w pętli `while`. Przesunięcie realizowane jest poprzez modyfikację współrzędnych docelowych funkcji `screen.blit(display_surface, (offset_x, offset_y))`.
*   **Animation Normalization**: Klatki animacji są odtwarzane z prędkością skalowaną do FPS:
    $$V_{frame} = BaseSpeed \times \frac{60}{FPS}$$
    **Uwaga inżynierska**: W obecnej wersji występuje niespójność zasobów — `main.py` wykonuje preload pliku `plusk.png`, podczas gdy `game.py` w fazie bitwy wykorzystuje `plusk2.png`.
*   **Screenshake Intensity**: Przy trafieniu `shake_amount = 10` (trwa 15 klatek), przy pudle przeciwnika `shake_amount = 3` (trwa 8 klatek).

### 3.6 Logika Rewanżu (Rematch Handshake)
1.  Gracz A klika "Rewanż" $\rightarrow$ Serwer ustawia `rematch_votes[0] = true`.
2.  Serwer wysyła `rematch_requested` do Gracza B.
3.  Gracz B klika "Rewanż" $\rightarrow$ Serwer wykrywa `all(rematch_votes) == true`.
4.  Reset stanu pokoju (czyszczenie `hits`, `scores`, `boards`) i wysyłka `rematch_start`.
5.  Klienci wykonują powrót do fazy `PLACEMENT`.

---

## 4. Specyfikacja Komunikatów JSON (DTO)

Wszystkie komunikaty są przesyłane jako stringi UTF-8 zakończone niejawnie przez zamknięcie obiektu JSON. System obsługuje **asynchroniczne potokowanie**, co oznacza, że klient musi być gotowy na odebranie wielu obiektów w jednym odczycie bufora.

### 4.1 Autentykacja i Profil (Auth Phase)

**Klient $\rightarrow$ Serwer:**
| Action | Payload | Opis |
| :--- | :--- | :--- |
| `register` | `{"action": "register", "username": "...", "password": "..."}` | Rejestracja. Hasło musi spełniać wymogi KAN-72. |
| `login` | `{"action": "login", "username": "...", "password": "..."}` | Logowanie użytkownika. |
| `get_high_scores` | `{"action": "get_high_scores"}` | Żądanie listy Top 100 (KAN-50). |

**Serwer $\rightarrow$ Klient:**
- **Sukces Auth**: `{"status": "success", "message": "Zalogowano!", "user_id": 15}`
- **Błąd Auth**: `{"status": "error", "message": "Błędne hasło!"}`
- **Ranking**: `{"status": "success", "data": [{"username": "Slayer", "best_score": 5000, "wins": 10, ...}, ...]}`

### 4.2 Matchmaking i Zarządzanie Pokojem

**Klient $\rightarrow$ Serwer:**
- **Szybka gra**: `{"action": "random_match"}`
- **Stwórz prywatny**: `{"action": "create_room"}`
- **Dołącz**: `{"action": "join_room", "room_code": "XY789"}`

**Serwer $\rightarrow$ Klient:**
- **Pokój stworzony**: `{"status": "room_created", "room_code": "AB123"}`
- **Start sesji**: `{"status": "game_start", "opponent": "Nazwa_Wroga"}`

### 4.3 Faza Rozstawiania i Start Bitwy

**Klient $\rightarrow$ Serwer:**
- **Gotowość**: 
```json
{
  "action": "player_ready",
  "board": [
    {"cells": [[0,0], [0,1], [0,2], [0,3]]},
    {"cells": [[5,5], [6,5], [7,5]]},
    ...
  ]
}
```

**Serwer $\rightarrow$ Klient:**
- **Start Bitwy**: `{"status": "battle_start", "your_idx": 0, "starting_turn": 1}`

### 4.4 Mechanika Bitwy (Real-time Events)

**Klient $\rightarrow$ Serwer:**
- **Strzał**: `{"action": "shoot", "x": 5, "y": 2}`
- **Czat**: `{"action": "chat_message", "message": "Dobra gra!"}`

**Serwer $\rightarrow$ Klient:**
- **Rezultat Strzału**:
```json
{
  "status": "shot_result",
  "x": 5, "y": 2,
  "hit": true,
  "sunk": true,
  "sunk_cells": [[5,0], [5,1], [5,2]],
  "shooter": 0,
  "next_turn": 0,
  "scores": [150, 0]
}
```
- **Timeout**: `{"status": "turn_timeout", "next_turn": 1, "message": "Czas minął! Zmiana tury."}`

### 4.5 Koniec Gry i Rewanż

**Serwer $\rightarrow$ Klient:**
- **Game Over**: `{"status": "game_over", "winner": "Nick", "final_scores": [1500, 400], "message": "Przeciwnik poddał się"}`
- **Rozłączenie**: `{"status": "opponent_disconnected"}`

**Handshake Rewanżu:**
1. Klient $\rightarrow$ Serwer: `{"action": "request_rematch"}`
2. Serwer $\rightarrow$ Klient (do drugiego): `{"status": "rematch_requested"}`
3. Serwer $\rightarrow$ Klient (do obu): `{"status": "rematch_start"}`

### 4.6 Obsługa Błędów i Wyjątków (Error Codes)
W przypadku wystąpienia błędu, serwer przesyła komunikat o statusie `error`.

| Komunikat (Message) | Kod Kontekstowy | Przyczyna |
| :--- | :--- | :--- |
| `Błędny login lub hasło.` | `AUTH_FAILED` | Nieprawidłowe poświadczenia podczas logowania. |
| `Użytkownik już istnieje.` | `USER_EXISTS` | Próba rejestracji zajętego nicku. |
| `Użytkownik jest już zalogowany!` | `ALREADY_LOGGED` | Wykryto aktywną sesję dla tego konta. |
| `Pokój nie istnieje lub jest pełny.` | `ROOM_ERROR` | Błędny kod pokoju lub próba dołączenia jako 3. gracz. |
| `Błąd bazy danych.` | `DB_ERROR` | Problem z połączeniem lub zapisem w PostgreSQL. |
| `Niepoprawne dane.` | `VALIDATION_ERROR` | Hasło nie spełnia wymogów KAN-72 lub nick zawiera znaki specjalne. |

---

## 5. Baza Danych - Struktura Szczegółowa (KAN-10)

System wykorzystuje relacyjną bazę danych PostgreSQL 14+.

### 5.1 Definicje Tabel (DDL - Zgodne z bazaSqlKomenda.txt)

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,
    player1_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    player2_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    winner_id INT REFERENCES users(user_id) ON DELETE SET NULL,
    played_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scores (
    score_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    match_id INT NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    points INT NOT NULL,
    is_winner BOOLEAN NOT NULL
);
```

### 5.3 Kluczowe Zapytania Logiki Biznesowej
Zapytanie rankingowe (Top 100) wykorzystuje agregację w celu wyliczenia statystyk meczowych:
```sql
SELECT 
    u.username, 
    MAX(s.points) as best_score, 
    SUM(CASE WHEN s.is_winner = TRUE THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN s.is_winner = FALSE THEN 1 ELSE 0 END) as losses,
    ROUND(AVG(s.points), 2) as avg_points
FROM users u
JOIN scores s ON u.user_id = s.user_id
GROUP BY u.user_id, u.username
ORDER BY best_score DESC
LIMIT 100;
```

### 5.4 Zarządzanie Połączeniami (Connection Management)
*   **Model Połączeń**: Serwer wykorzystuje **Connection Pooling** (`psycopg2.pool.SimpleConnectionPool`). Zapobiega to nadmiernemu zużyciu zasobów PostgreSQL przez eliminację modelu "jeden proces na gracza". Połączenia są pobierane i zwracane do puli w cyklu transakcyjnym.

---

## 6. Local Setup & Deployment

Instrukcja szybkiego uruchomienia środowiska deweloperskiego.

### 6.1 Konfiguracja Środowiska (Python)
1.  **Wirtualne środowisko**:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    ```
2.  **Instalacja zależności**:
    ```bash
    pip install pygame psycopg2-binary python-dotenv bcrypt
    ```
3.  **Plik .env**: Stwórz plik `.env` w katalogu głównym na podstawie wzoru:
    ```text
    DB_HOST=localhost
    DB_NAME=battleships_db
    DB_USER=postgres
    DB_PASS=twoje_haslo
    ```

### 6.2 Inicjalizacja Bazy Danych
System wymaga PostgreSQL 14+. 
1. Utwórz bazę danych o nazwie zgodnej z `.env`.
2. Uruchom zapytania SQL zawarte w pliku `bazaSqlKomenda.txt` w celu utworzenia struktury tabel.

### 6.3 Uruchomienie
1. **Serwer**: `python server.py` (musi działać w tle, aby klienci mogli się łączyć).
2. **Klient**: `python main.py`

