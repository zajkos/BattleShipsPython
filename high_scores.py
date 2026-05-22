# high_scores.py
import pygame
import sys
import json
from settings import *
from button import Button
import options

def show_high_scores(screen, clock, net, background=None):
    """Ekran wyświetlający listę najlepszych 100 wyników z serwerem i sortowaniem."""
    # Zmniejszone czcionki dla lepszej czytelności
    font_title = pygame.font.SysFont("arial", 70, bold=True)
    font_header = pygame.font.SysFont("arial", 28, bold=True)
    font_row = pygame.font.SysFont("arial", 24)
    font_small = pygame.font.SysFont("arial", 20)
    
    # Przycisk powrotu
    btn_back = Button(WIDTH // 2 - 150, HEIGHT - 80, 300, 60, "Wstecz", font_header)

    # Pobieranie danych z serwera
    loading_surf = font_header.render("Pobieranie wyników...", True, TEXT_COLOR)
    
    if background:
        screen.blit(background, (0, 0))
    else:
        screen.fill(BG_COLOR)
        
    screen.blit(loading_surf, loading_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    pygame.display.update()

    response = net.send({"action": "get_high_scores"})
    raw_data = []
    if response and response.get("status") == "success":
        raw_data = response.get("data", [])
    else:
        print("Błąd pobierania rankingu lub brak danych.")

    # Parametry listy
    row_height = 40
    list_y_start = 250
    list_height = HEIGHT - 380
    scroll_y = 0
    
    # Definicja kolumn - poszerzone szerokości dla bezpiecznych marginesów
    cols = [
        {"name": "Poz", "width": 110, "attr": "rank", "sort_key": None},
        {"name": "Gracz", "width": 320, "attr": "username", "sort_key": "username"},
        {"name": "Najlepszy Wynik", "width": 300, "attr": "best_score", "sort_key": "best_score"},
        {"name": "Wygrane", "width": 180, "attr": "wins", "sort_key": "wins"},
        {"name": "Przegrane", "width": 180, "attr": "losses", "sort_key": "losses"},
        {"name": "Średnia", "width": 180, "attr": "avg_points", "sort_key": "avg_points"}
    ]
    
    total_table_width = sum(c["width"] for c in cols)
    table_x = (WIDTH - total_table_width) // 2

    # Logika sortowania
    current_sort_col = "best_score"
    sort_reverse = True # True = malejąco, False = rosnąco
    
    def get_sorted_data():
        if current_sort_col == "rank":
            # Sortowanie po oryginalnej pozycji (z bazy przyszły posortowane po best_score)
            return sorted(raw_data, key=lambda x: raw_data.index(x), reverse=sort_reverse)
        
        # Znajdź klucz do sortowania
        key = current_sort_col
        return sorted(raw_data, key=lambda x: x.get(key, 0) if isinstance(x.get(key), (int, float)) else x.get(key, "").lower(), reverse=sort_reverse)

    scores_data = get_sorted_data()
    max_scroll = max(0, len(scores_data) * row_height - list_height)

    # Cache powierzchni tabeli
    def create_table_surface(data):
        surf = pygame.Surface((total_table_width, max(list_height, len(data) * row_height)), pygame.SRCALPHA)
        for i, row in enumerate(data):
            y = i * row_height
            
            # Kolorowanie
            rank_in_original = raw_data.index(row) + 1
            color = TEXT_COLOR
            bg_alpha = 20
            
            if rank_in_original <= 3:
                color = (255, 215, 0)
                bg_alpha = 60
            elif rank_in_original <= 10:
                color = (200, 200, 200)
                bg_alpha = 40
            
            if i % 2 == 0:
                pygame.draw.rect(surf, (255, 255, 255, bg_alpha), (0, y, total_table_width, row_height))

            curr_x = 0
            # Pozycja (oryginalna z bazy)
            table_surface.blit(font_row.render(str(rank_in_original), True, color), (curr_x + 10, y + 5))
            curr_x += cols[0]["width"]
            
            # Nick
            name_text = row["username"]
            if len(name_text) > 20: name_text = name_text[:17] + "..."
            table_surface.blit(font_row.render(name_text, True, color), (curr_x + 10, y + 5))
            curr_x += cols[1]["width"]

            # Wynik
            table_surface.blit(font_row.render(str(row["best_score"]), True, color), (curr_x + 10, y + 5))
            curr_x += cols[2]["width"]

            # Wygrane
            table_surface.blit(font_row.render(str(row["wins"]), True, (100, 255, 100)), (curr_x + 10, y + 5))
            curr_x += cols[3]["width"]

            # Przegrane
            table_surface.blit(font_row.render(str(row["losses"]), True, (255, 100, 100)), (curr_x + 10, y + 5))
            curr_x += cols[4]["width"]

            # Średnia
            table_surface.blit(font_row.render(f"{row['avg_points']:.2f}", True, (150, 200, 255)), (curr_x + 10, y + 5))
        return surf

    table_surface = pygame.Surface((total_table_width, max(list_height, len(scores_data) * row_height)), pygame.SRCALPHA)
    
    def update_table():
        nonlocal scores_data, table_surface
        scores_data = get_sorted_data()
        table_surface.fill((0, 0, 0, 0))
        curr_y = 0
        for i, row in enumerate(scores_data):
            y = i * row_height
            rank_in_original = raw_data.index(row) + 1
            color = TEXT_COLOR
            bg_alpha = 20
            if rank_in_original <= 3: color = (255, 215, 0); bg_alpha = 60
            elif rank_in_original <= 10: color = (200, 200, 200); bg_alpha = 40
            
            if i % 2 == 0:
                pygame.draw.rect(table_surface, (255, 255, 255, bg_alpha), (0, y, total_table_width, row_height))
            
            cx = 0
            table_surface.blit(font_row.render(str(rank_in_original), True, color), (cx + 10, y + 5))
            cx += cols[0]["width"]
            name_txt = row["username"]
            if len(name_txt) > 20: name_txt = name_txt[:17] + "..."
            table_surface.blit(font_row.render(name_txt, True, color), (cx + 10, y + 5))
            cx += cols[1]["width"]
            table_surface.blit(font_row.render(str(row["best_score"]), True, color), (cx + 10, y + 5))
            cx += cols[2]["width"]
            table_surface.blit(font_row.render(str(row["wins"]), True, (100, 255, 100)), (cx + 10, y + 5))
            cx += cols[3]["width"]
            table_surface.blit(font_row.render(str(row["losses"]), True, (255, 100, 100)), (cx + 10, y + 5))
            cx += cols[4]["width"]
            table_surface.blit(font_row.render(f"{row['avg_points']:.2f}", True, (150, 200, 255)), (cx + 10, y + 5))

    update_table()

    # Pasek przewijania (zmienne do obsługi przeciągania)
    dragging_scroll = False

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    
    # Optymalizacja: Pre-renderowanie stałych elementów
    title_surf = font_title.render("RANKING GRACZY", True, (255, 215, 0))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 80))
    
    hint_surf = font_small.render("Kliknij nagłówek, aby sortować | Kółko myszy / Strzałki / Przeciągnij pasek: Przewijanie", True, (150, 150, 150))
    hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 115))
    
    # Cache dla nazw kolumn (aktywne / nieaktywne)
    header_surfaces = {}
    for col in cols:
        header_surfaces[(col["name"], True)] = font_header.render(col["name"], True, (255, 215, 0))
        header_surfaces[(col["name"], False)] = font_header.render(col["name"], True, (180, 180, 180))
        
    ind_up = font_header.render("▲", True, (255, 215, 0))
    ind_down = font_header.render("▼", True, (255, 215, 0))

    while True:
        mouse_pos = pygame.mouse.get_pos()

        if background:
            screen.blit(background, (0, 0))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)
            
        screen.blit(title_surf, title_rect)

        # Nagłówki kolumn z detekcją kliknięcia
        curr_x = table_x
        header_rects = []
        for col in cols:
            rect = pygame.Rect(curr_x, list_y_start - 60, col["width"], 50)
            header_rects.append((rect, col))
            
            is_active = current_sort_col == (col["sort_key"] if col["sort_key"] else "rank")
            
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 255, 255, 30), rect, border_radius=5)

            # --- LOGIKA REZERWACJI MIEJSCA ---
            # Pobieramy zbuforowany obrazek nagłówka
            text_surf = header_surfaces[(col["name"], is_active)]
            
            # 2. Rezerwujemy stałe miejsce na strzałkę (np. 30px), aby tekst nie "skakał"
            arrow_reserved_space = 30
            total_content_width = text_surf.get_width() + arrow_reserved_space
            
            # 3. Wyliczamy punkt startowy tak, aby CAŁY BLOK (tekst + miejsce na strzałkę) był wycentrowany
            start_x = rect.left + (rect.width - total_content_width) // 2
            
            # 4. Rysujemy tekst (zawsze w tym samym miejscu względem start_x)
            text_rect = text_surf.get_rect(midleft=(start_x, rect.centery))
            screen.blit(text_surf, text_rect)

            # 5. Jeśli kolumna jest aktywna, rysujemy strzałkę w zarezerwowanym miejscu
            if is_active:
                ind_surf = ind_up if not sort_reverse else ind_down
                # Strzałka zawsze 5px za tekstem
                ind_rect = ind_surf.get_rect(midleft=(text_rect.right + 5, text_rect.centery))
                screen.blit(ind_surf, ind_rect)

            curr_x += col["width"]
        
        pygame.draw.line(screen, (100, 100, 100), (table_x, list_y_start - 10), (table_x + total_table_width, list_y_start - 10), 2)

        # Wyświetlanie tabeli
        view_rect = pygame.Rect(0, scroll_y, total_table_width, list_height)
        screen.blit(table_surface, (table_x, list_y_start), view_rect)

        # Scrollbar (po PRAWEJ stronie zgodnie z poprzednią wersją)
        sb_x = table_x + total_table_width + 15
        sb_rect = pygame.Rect(sb_x, list_y_start, 12, list_height)
        if max_scroll > 0:
            pygame.draw.rect(screen, (40, 40, 60), sb_rect, border_radius=6)
            bar_h = max(30, (list_height / (len(scores_data) * row_height)) * list_height)
            bar_y = (scroll_y / max_scroll) * (list_height - bar_h)
            bar_rect = pygame.Rect(sb_x, list_y_start + bar_y, 12, bar_h)
            
            bar_color = (130, 130, 230) if (max_scroll > 0 and bar_rect.collidepoint(mouse_pos)) or dragging_scroll else (100, 100, 200)
            pygame.draw.rect(screen, bar_color, bar_rect, border_radius=6)

        # Stopka z instrukcją - PRZESUNIĘTA W DÓŁ (HEIGHT - 115)
        screen.blit(hint_surf, hint_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Detekcja kliknięcia w pasek przewijania
                    if max_scroll > 0 and bar_rect.collidepoint(event.pos):
                        dragging_scroll = True
                    
                    # Kliknięcie w nagłówek
                    for rect, col in header_rects:
                        if rect.collidepoint(event.pos):
                            new_sort = col["sort_key"] if col["sort_key"] else "rank"
                            if current_sort_col == new_sort:
                                sort_reverse = not sort_reverse
                            else:
                                current_sort_col = new_sort
                                sort_reverse = True
                            update_table()
                            scroll_y = 0
                            break

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_scroll = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_scroll and max_scroll > 0:
                    # Relatywna pozycja myszy wewnątrz szyny scrollbara
                    rel_y = event.pos[1] - list_y_start
                    # Procentowe przesunięcie (z uwzględnieniem połowy wysokości suwaka dla centrowania pod myszką)
                    scroll_percent = (rel_y - bar_h / 2) / (list_height - bar_h)
                    scroll_y = max(0, min(max_scroll, scroll_percent * max_scroll))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return
                if event.key == pygame.K_UP: scroll_y = max(0, scroll_y - row_height * 2)
                if event.key == pygame.K_DOWN: scroll_y = min(max_scroll, scroll_y + row_height * 2)

            if event.type == pygame.MOUSEWHEEL:
                scroll_y = max(0, min(max_scroll, scroll_y - event.y * row_height * 3))

            if btn_back.handle_event(event): return

        btn_back.check_hover(mouse_pos)
        btn_back.draw(screen)
        pygame.display.update()
        clock.tick(options.current_fps)
