import pygame
import random
import json
import os
from config import *
from entities.gem import Gem
from ui.shop import Shop
from ui.main_menu import MainMenu

class Game:
    def __init__(self):
        try:
            print("Инициализация Pygame...")
            pygame.init()
            print("Создание окна...")
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("Match-3 RPG")
            print("Окно создано успешно")
            
            self.clock = pygame.time.Clock()
            self.running = True
            self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
            self.selected_gem = None
            self.enemy_health = ENEMY_MAX_HEALTH
            print(f"Здоровье врага инициализировано: {self.enemy_health}")
            self.coins = 0
            self.moves_left = 50
            print(f"Количество ходов: {self.moves_left}")
            self.shop = Shop(self)
            self.main_menu = MainMenu()  # Создаем главное меню
            self.game_started = False    # Флаг для отслеживания состояния игры
            self.damage_popup = None
            self.damage_popup_time = 0
            self.damage_popup_value = 0
            self.npc_hit_time = None  # Для анимации получения урона
            self.last_swap_target = None  # <-- координата последнего хода
            
            # Загружаем фоновое изображение всего окна
            bg_path = os.path.join("images", "bg1-1.jpg")
            if not os.path.exists(bg_path):
                raise FileNotFoundError(f"Фоновое изображение не найдено: {bg_path}")
            self.background = pygame.image.load(bg_path).convert()
            self.background = pygame.transform.smoothscale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
            
            # Загружаем фон поля
            self.field_bg = pygame.image.load(os.path.join("images", "backgraund.png")).convert_alpha()
            
            # Загружаем спрайт персонажа
            npc_sprite_path = os.path.join("images", "npc_g", "NPC-1-1.png")
            if not os.path.exists(npc_sprite_path):
                raise FileNotFoundError(f"Спрайт персонажа не найден: {npc_sprite_path}")
            self.npc_image = pygame.image.load(npc_sprite_path).convert_alpha()
            # Масштабируем спрайт под высоту игрового поля
            npc_height = GRID_SIZE * CELL_SIZE
            scale_factor = npc_height / self.npc_image.get_height()
            npc_width = int(self.npc_image.get_width() * scale_factor)
            self.npc_image = pygame.transform.smoothscale(self.npc_image, (npc_width, npc_height))
            
            print("Проверка директории с изображениями...")
            if not os.path.exists(IMAGE_DIR):
                raise FileNotFoundError(f"Директория с изображениями не найдена: {IMAGE_DIR}")
            print(f"Директория с изображениями найдена: {IMAGE_DIR}")
            
            print("Проверка файлов изображений...")
            for gem_type, image_path in GEM_IMAGES.items():
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Изображение не найдено: {image_path}")
                print(f"Изображение найдено: {image_path}")
            
            print("Инициализация игрового поля...")
            self.initialize_grid()
            print("Загрузка сохранения...")
            self.load_save()
            print(f"Здоровье врага после загрузки: {self.enemy_health}")
            print("Игра успешно инициализирована")
        except Exception as e:
            print(f"Ошибка при инициализации игры: {e}")
            self.running = False
            pygame.quit()
            raise

    def initialize_grid(self):
        # Создаем пустое поле
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Заполняем поле гемами, избегая комбинаций
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Список доступных типов гемов
                available_types = GEM_TYPES.copy()
                
                # Проверяем два предыдущих гема по горизонтали
                if x >= 2:
                    if (self.grid[y][x-1] and self.grid[y][x-2] and 
                        self.grid[y][x-1].type == self.grid[y][x-2].type):
                        # Удаляем тип, который создаст комбинацию
                        if self.grid[y][x-1].type in available_types:
                            available_types.remove(self.grid[y][x-1].type)
                
                # Проверяем два предыдущих гема по вертикали
                if y >= 2:
                    if (self.grid[y-1][x] and self.grid[y-2][x] and 
                        self.grid[y-1][x].type == self.grid[y-2][x].type):
                        # Удаляем тип, который создаст комбинацию
                        if self.grid[y-1][x].type in available_types:
                            available_types.remove(self.grid[y-1][x].type)
                
                # Если нет доступных типов, используем случайный
                if not available_types:
                    available_types = GEM_TYPES.copy()
                
                # Создаем новый гем
                self.grid[y][x] = Gem(x, y, random.choice(available_types))

    def draw(self):
        # Отображаем фоновое изображение
        self.screen.blit(self.background, (0, 0))
        
        # Если игра не начата, показываем только меню
        if not self.game_started:
            self.main_menu.draw(self.screen)
            pygame.display.flip()
            return
        
        # --- Верхняя панель с монетами и ходами ---
        top_panel_h = 60
        top_panel_margin = 30  # увеличенный отступ сверху
        top_panel_rect = pygame.Rect(GRID_OFFSET_X - 15, top_panel_margin, GRID_SIZE * CELL_SIZE + 30, top_panel_h)
        total_top_offset = top_panel_margin + top_panel_h + 10  # 10px дополнительный отступ

        # Смещаем игровое поле и все элементы вниз
        field_rect = pygame.Rect(
            GRID_OFFSET_X - 15,
            total_top_offset + GRID_OFFSET_Y - 15,
            GRID_SIZE * CELL_SIZE + 30,
            GRID_SIZE * CELL_SIZE + 30
        )
        # Тень от поля
        shadow_rect = field_rect.move(8, 8)
        pygame.draw.rect(self.screen, COLORS['SHADOW'], shadow_rect, border_radius=18)
        # Фон поля — изображение
        bg_img = pygame.transform.smoothscale(self.field_bg, (field_rect.width, field_rect.height))
        self.screen.blit(bg_img, field_rect.topleft)
        # Рамка
        pygame.draw.rect(self.screen, COLORS['WHITE'], field_rect, 4, border_radius=18)
        
        # --- HUD панель справа ---
        hud_width = 220
        hud_height = GRID_SIZE * CELL_SIZE + 30
        hud_x = field_rect.right + 20
        hud_y = field_rect.top
        hud_rect = pygame.Rect(hud_x, hud_y, hud_width, hud_height)
        # Тень HUD
        hud_shadow = hud_rect.move(6, 6)
        pygame.draw.rect(self.screen, (0,0,0,80), hud_shadow, border_radius=22)
        # Полупрозрачная панель
        hud_surface = pygame.Surface((hud_width, hud_height), pygame.SRCALPHA)
        pygame.draw.rect(hud_surface, (40, 40, 60, 210), hud_surface.get_rect(), border_radius=22)
        # Декоративный градиент сверху
        grad = pygame.Surface((hud_width, 60), pygame.SRCALPHA)
        for i in range(60):
            alpha = max(0, 120 - i*2)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,hud_width,1))
        hud_surface.blit(grad, (0,0))
        self.screen.blit(hud_surface, (hud_x, hud_y))
        # Светящиеся углы
        glow = pygame.Surface((40,40), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (120,200,255,60), (0,0,40,40))
        self.screen.blit(glow, (hud_x-10, hud_y-10))
        self.screen.blit(glow, (hud_x+hud_width-30, hud_y-10))
        self.screen.blit(glow, (hud_x-10, hud_y+hud_height-30))
        self.screen.blit(glow, (hud_x+hud_width-30, hud_y+hud_height-30))
        # --- Верхняя панель с монетами и ходами ---
        top_panel_h = 60
        top_panel_margin = 30  # увеличенный отступ сверху
        top_panel_rect = pygame.Rect(field_rect.left, top_panel_margin, field_rect.width, top_panel_h)
        # Тень
        top_panel_shadow = top_panel_rect.move(0, 6)
        border_radius_top = 18
        pygame.draw.rect(self.screen, (0,0,0,80), top_panel_shadow, border_radius=border_radius_top)
        # Полупрозрачная панель
        top_panel_surface = pygame.Surface((top_panel_rect.width, top_panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(top_panel_surface, (40, 40, 60, 210), top_panel_surface.get_rect(), border_radius=border_radius_top)
        grad = pygame.Surface((top_panel_rect.width, 30), pygame.SRCALPHA)
        for i in range(30):
            alpha = max(0, 100 - i*3)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,top_panel_rect.width,1))
        # Маска для скругления градиента
        grad_mask = pygame.Surface((top_panel_rect.width, 30), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=border_radius_top)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        top_panel_surface.blit(grad, (0,0))
        self.screen.blit(top_panel_surface, top_panel_rect.topleft)
        # Монеты
        font = pygame.font.Font(None, 38)
        coin_icon = pygame.Surface((32,32), pygame.SRCALPHA)
        pygame.draw.circle(coin_icon, COLORS['GOLD'], (16,16), 16)
        pygame.draw.circle(coin_icon, (255,255,255,80), (16,16), 16, 3)
        self.screen.blit(coin_icon, (top_panel_rect.left+30, top_panel_rect.top+14))
        coins_text = font.render(f"{self.coins}", True, COLORS['GOLD'])
        self.screen.blit(coins_text, (top_panel_rect.left+74, top_panel_rect.top+18))
        # Ходы
        moves_text = font.render(f"Ходы: {self.moves_left}", True, COLORS['WHITE'])
        self.screen.blit(moves_text, (top_panel_rect.left+180, top_panel_rect.top+18))
        # --- Кнопка магазина справа от поля ---
        shop_btn_w, shop_btn_h = 160, 48
        shop_btn_x = hud_x + (hud_width - shop_btn_w)//2
        shop_btn_y = hud_y + hud_height + 24
        shop_button = pygame.Rect(shop_btn_x, shop_btn_y, shop_btn_w, shop_btn_h)
        # Тень
        shop_shadow = shop_button.move(0, 6)
        border_radius_shop = 16
        pygame.draw.rect(self.screen, (0,0,0,80), shop_shadow, border_radius=border_radius_shop)
        # Красивая кнопка
        shop_surface = pygame.Surface((shop_btn_w, shop_btn_h), pygame.SRCALPHA)
        pygame.draw.rect(shop_surface, (60, 60, 90, 220), shop_surface.get_rect(), border_radius=border_radius_shop)
        grad = pygame.Surface((shop_btn_w, shop_btn_h//2), pygame.SRCALPHA)
        for i in range(shop_btn_h//2):
            alpha = max(0, 80 - i*3)
            pygame.draw.rect(grad, (255,255,255,alpha), (0,i,shop_btn_w,1))
        # Маска для скругления градиента
        grad_mask = pygame.Surface((shop_btn_w, shop_btn_h//2), pygame.SRCALPHA)
        pygame.draw.rect(grad_mask, (255,255,255,255), grad_mask.get_rect(), border_radius=border_radius_shop)
        grad.blit(grad_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        shop_surface.blit(grad, (0,0))
        self.screen.blit(shop_surface, (shop_btn_x, shop_btn_y))
        # Текст
        shop_font = pygame.font.Font(None, 36)
        shop_text = shop_font.render("Магазин", True, COLORS['WHITE'])
        self.screen.blit(shop_text, (shop_btn_x + shop_btn_w//2 - shop_text.get_width()//2, shop_btn_y + shop_btn_h//2 - shop_text.get_height()//2))
        # Обновляю координаты кнопки магазина для handle_click
        self._shop_button_rect = shop_button
        # --- Остальной игровой процесс ---
        # --- Гемы с тенью ---
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x]:
                    # Тень под гемом
                    shadow = pygame.Surface((CELL_SIZE-4, CELL_SIZE-4), pygame.SRCALPHA)
                    shadow.fill((0,0,0,80))
                    sx = FIELD_DRAW_OFFSET_X + FIELD_INNER_PADDING + x * CELL_SIZE + 2
                    sy = FIELD_DRAW_OFFSET_Y + FIELD_INNER_PADDING + y * CELL_SIZE + 8  # тень чуть ниже
                    self.screen.blit(shadow, (sx, sy))
                    # Сам гем
                    self.grid[y][x].draw(self.screen)
        
        # Рисуем спрайт персонажа справа от игрового поля
        npc_x = FIELD_DRAW_OFFSET_X + GRID_SIZE * CELL_SIZE + 50
        npc_y = FIELD_DRAW_OFFSET_Y
        # --- Эффект урона: только встряска ---
        shake = 0
        
        if self.npc_hit_time:
            current_time = pygame.time.get_ticks()
            hit_duration = 200  # Длительность эффекта в мс
            elapsed = current_time - self.npc_hit_time
            
            if elapsed < hit_duration:
                # Встряска с затуханием
                intensity = 1 - (elapsed / hit_duration)
                shake = int(8 * intensity) * random.choice([-1, 1])
            else:
                self.npc_hit_time = None
        
        # Отрисовка персонажа только со встряской
        self.screen.blit(self.npc_image, (npc_x + shake, npc_y))
        
        # --- Рисуем popup урона ---
        if self.damage_popup:
            elapsed = pygame.time.get_ticks() - self.damage_popup
            if elapsed < self.damage_popup_time:
                font = pygame.font.Font(None, 48)
                dmg_text = font.render(f"-{self.damage_popup_value}", True, COLORS['RED'])
                text_x = npc_x + self.npc_image.get_width() // 2 - dmg_text.get_width() // 2
                text_y = npc_y - 40 - int(40 * (elapsed / self.damage_popup_time))
                self.screen.blit(dmg_text, (text_x, text_y))
            else:
                self.damage_popup = None
        
        # В конце проверяем, нужно ли отобразить меню поверх игры
        if self.main_menu.visible:
            self.main_menu.draw(self.screen)
        
        # --- Сетка внутри поля ---
        grid_left = FIELD_DRAW_OFFSET_X + FIELD_INNER_PADDING
        grid_top = FIELD_DRAW_OFFSET_Y + FIELD_INNER_PADDING
        grid_size_px = GRID_SIZE * CELL_SIZE
        grid_color = (255,255,255,30)  # светлая полупрозрачная
        grid_surface = pygame.Surface((grid_size_px, grid_size_px), pygame.SRCALPHA)
        for i in range(GRID_SIZE+1):
            # Вертикальные линии
            pygame.draw.line(grid_surface, grid_color, (i*CELL_SIZE, 0), (i*CELL_SIZE, grid_size_px), 1)
            # Горизонтальные линии
            pygame.draw.line(grid_surface, grid_color, (0, i*CELL_SIZE), (grid_size_px, i*CELL_SIZE), 1)
        self.screen.blit(grid_surface, (grid_left, grid_top))
        
        pygame.display.flip()

    def handle_click(self, pos):
        # Если открыто главное меню, обрабатываем его события
        if self.main_menu.visible:
            action = self.main_menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos}))
            if action:
                self.handle_menu_action(action)
            return
        
        # Проверяем, есть ли гемы в процессе анимации
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] and (self.grid[y][x].is_moving or self.grid[y][x].is_returning):
                    return
        
        # Проверяем клик по кнопке магазина
        if self._shop_button_rect.collidepoint(pos):
            self.shop.toggle_visibility()
            return
        
        # Если магазин открыт, обрабатываем клики в нем
        if self.shop.visible:
            self.shop.handle_click(pos)
            return
        
        # Обрабатываем клики по игровому полю
        # Учитываем смещение поля вниз
        total_top_offset = 30 + 60 + 10  # top_panel_margin + top_panel_h + 10
        x = (pos[0] - GRID_OFFSET_X) // CELL_SIZE
        y = (pos[1] - (GRID_OFFSET_Y + total_top_offset)) // CELL_SIZE
        
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            if self.selected_gem is None:
                self.selected_gem = (x, y)
                self.grid[y][x].is_selected = True
            else:
                if self.is_adjacent(self.selected_gem, (x, y)):
                    # Меняем гемы местами
                    self.swap_gems(self.selected_gem, (x, y))
                    
                    # Проверяем совпадения
                    matches = self.check_matches()
                    if matches:
                        self.process_matches(matches)
                        self.moves_left -= 1
                        # Сбросить выделение у всех гемов
                        for row in self.grid:
                            for gem in row:
                                if gem:
                                    gem.is_selected = False
                        self.selected_gem = None
                    else:
                        # Если совпадений нет, возвращаем гемы в исходные позиции
                        self.swap_gems(self.selected_gem, (x, y))
                        self.grid[y][x].return_to_original()
                        self.grid[self.selected_gem[1]][self.selected_gem[0]].return_to_original()
                        # Анимация дрожания для обоих гемов
                        if self.grid[y][x]:
                            self.grid[y][x].start_shake()
                        if self.grid[self.selected_gem[1]][self.selected_gem[0]]:
                            self.grid[self.selected_gem[1]][self.selected_gem[0]].start_shake()
                        # Снимаем выделение
                        self.grid[self.selected_gem[1]][self.selected_gem[0]].is_selected = False
                        self.selected_gem = None
                else:
                    # Если не соседний — выделяем новый гем
                    self.grid[self.selected_gem[1]][self.selected_gem[0]].is_selected = False
                    self.selected_gem = (x, y)
                    self.grid[y][x].is_selected = True

    def is_adjacent(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

    def swap_gems(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        
        # Временно сохраняем гемы
        gem1 = self.grid[y1][x1]
        gem2 = self.grid[y2][x2]
        
        # Обновляем позиции гемов в сетке
        self.grid[y1][x1] = gem2
        self.grid[y2][x2] = gem1
        
        # Обновляем координаты гемов
        if gem1:
            gem1.x, gem1.y = x2, y2
            gem1.move_to(x2, y2)
        if gem2:
            gem2.x, gem2.y = x1, y1
            gem2.move_to(x1, y1)
        
        # Сохраняем координату, куда был совершен ход
        self.last_swap_target = (x2, y2)

    def check_matches(self):
        matches = []
        # Проверяем горизонтальные совпадения
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE - 2):
                if (self.grid[y][x] is not None and 
                    self.grid[y][x+1] is not None and 
                    self.grid[y][x+2] is not None and
                    self.grid[y][x].type == self.grid[y][x+1].type == self.grid[y][x+2].type):
                    matches.append([(x, y), (x+1, y), (x+2, y)])

        # Проверяем вертикальные совпадения
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE - 2):
                if (self.grid[y][x] is not None and 
                    self.grid[y+1][x] is not None and 
                    self.grid[y+2][x] is not None and
                    self.grid[y][x].type == self.grid[y+1][x].type == self.grid[y+2][x].type):
                    matches.append([(x, y), (x, y+1), (x, y+2)])

        return matches

    def process_matches(self, matches, is_player_move=True):
        if not matches:  # Защита от пустого списка
            return
            
        # --- Анимация сложения ---
        if is_player_move and self.last_swap_target:
            # Анимация к целевому гемy хода
            target_x, target_y = self.last_swap_target
        else:
            # Анимация к центру комбинации
            target_x = sum([x for x, y in matches[0]]) / len(matches[0])
            target_y = sum([y for x, y in matches[0]]) / len(matches[0])
        for match in matches:
            for x, y in match:
                gem = self.grid[y][x]
                if gem:
                    gem.move_to_position(target_x, target_y)
        # Ждем завершения анимации
        animation_running = True
        while animation_running:
            animation_running = False
            for match in matches:
                for x, y in match:
                    gem = self.grid[y][x]
                    if gem and gem.is_moving:
                        animation_running = True
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x]:
                        self.grid[y][x].update(1/60)
            self.draw()
            self.clock.tick(60)
        # --- Конец анимации сложения ---
            
        total_damage = 0
        critical_hits = 0
        
        # Обрабатываем каждое совпадение
        for match in matches:
            for x, y in match:
                gem = self.grid[y][x]
                if gem:
                    # Получаем базовый урон и шанс крита
                    base_damage, crit_chance = gem.calculate_damage()
                    
                    # Учитываем бонусы из магазина
                    if self.shop.damage_bonus:
                        base_damage *= 1.5  # Увеличение урона на 50%
                        
                    if self.shop.crit_bonus:
                        crit_chance += 0.2  # Увеличение шанса крита на 20%
                        
                    # Проверяем крит
                    if random.random() < crit_chance:
                        damage = base_damage * gem.crit_multiplier
                        critical_hits += 1
                    else:
                        damage = base_damage
                        
                    total_damage += damage
                    gem.add_experience()
                    
                    # Удаляем гем
                    self.grid[y][x] = None
        
        # Наносим урон врагу
        self.enemy_health = max(0, self.enemy_health - total_damage)
        self.coins += critical_hits * 10
        
        # Заполняем пустые ячейки
        self.fill_empty_cells()
        
        # Обновляем таймеры бонусов
        self.shop.update()
        
        # Проверяем новые комбинации после заполнения/841
        new_matches = self.check_matches()
        if new_matches:
            print("Найдены новые комбинации после заполнения!")
            self.process_matches(new_matches, is_player_move=False)
        
        # --- Показываем popup урона ---
        if total_damage > 0:
            self.damage_popup = pygame.time.get_ticks()
            self.damage_popup_time = 1000  # мс
            self.damage_popup_value = int(total_damage)
            self.npc_hit_time = pygame.time.get_ticks()  # <-- для анимации урона

    def fill_empty_cells(self):
        for x in range(GRID_SIZE):
            empty_cells = 0
            for y in range(GRID_SIZE - 1, -1, -1):
                if self.grid[y][x] is None:
                    empty_cells += 1
                elif empty_cells > 0:
                    # Перемещаем гем вниз
                    self.grid[y + empty_cells][x] = self.grid[y][x]
                    self.grid[y][x] = None
                    self.grid[y + empty_cells][x].move_to(x, y + empty_cells)

            # Создаем новые гемы в пустых ячейках
            for y in range(empty_cells):
                new_gem = Gem(x, y)
                self.grid[y][x] = new_gem
                # Устанавливаем начальную позицию выше игрового поля
                new_gem.rect.y = GRID_OFFSET_Y - CELL_SIZE
                new_gem.move_to(x, y)

    def save_game(self):
        save_data = {
            'enemy_health': self.enemy_health,
            'coins': self.coins,
            'moves_left': self.moves_left,
            'grid': [[{'type': gem.type, 'level': gem.level} if gem else None 
                     for gem in row] for row in self.grid]
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f)

    def load_save(self):
        try:
            with open(SAVE_FILE, 'r') as f:
                save_data = json.load(f)
                # Загружаем здоровье врага только если оно больше 0
                if save_data['enemy_health'] > 0:
                    self.enemy_health = save_data['enemy_health']
                self.coins = save_data['coins']
                self.moves_left = save_data['moves_left']
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if save_data['grid'][y][x]:
                            gem_data = save_data['grid'][y][x]
                            self.grid[y][x] = Gem(x, y, gem_data['type'])
                            self.grid[y][x].level = gem_data['level']
        except FileNotFoundError:
            print("Сохранение не найдено, начинаем новую игру")
        except Exception as e:
            print(f"Ошибка при загрузке сохранения: {e}")
            print("Начинаем новую игру")

    def handle_menu_action(self, action):
        if action == 'new_game':
            self.start_new_game()
        elif action == 'continue':
            self.load_save()
            self.main_menu.visible = False
            self.game_started = True
        elif action == 'exit':
            self.running = False

    def start_new_game(self):
        self.enemy_health = ENEMY_MAX_HEALTH
        self.coins = 0
        self.moves_left = 50
        self.initialize_grid()
        self.main_menu.visible = False
        self.game_started = True

    def run(self):
        print("Запуск игрового цикла...")
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Получен сигнал выхода")
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.MOUSEMOTION and self.main_menu.visible:
                    self.main_menu.handle_event(event)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_started and not self.main_menu.visible:
                            self.save_game()  # Сохраняем игру перед открытием меню
                            self.main_menu.visible = True
                        elif self.game_started and self.main_menu.visible:
                            self.main_menu.visible = False

            # Обновляем состояние гемов только если игра начата
            if self.game_started:
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if self.grid[y][x]:
                            self.grid[y][x].update(dt)

            self.draw()

            # Проверяем условие окончания игры только если игра начата
            if self.game_started:
                if self.moves_left <= 0:
                    print("Закончились ходы")
                    self.save_game()
                    self.game_started = False
                    self.main_menu.visible = True
                elif self.enemy_health <= 0:
                    print("Враг побежден")
                    self.save_game()
                    self.game_started = False
                    self.main_menu.visible = True

        print("Завершение работы...")
        pygame.quit()

    def bounce(self, t):
        # Функция эффекта отскока
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - 2 * (1 - t) * (1 - t)

if __name__ == "__main__":
    print("Запуск игры...")
    game = Game()
    game.run()
    print("Игра завершена") 